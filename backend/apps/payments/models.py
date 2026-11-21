from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.invoices.models import Invoice
from apps.procurement.models import PurchaseOrder, Vendor
from apps.orders.models import Customer


class Payment(models.Model):
    TYPE_CHOICES = [
        ('CUSTOMER_RECEIPT', 'Customer Receipt (Inflow)'),
        ('VENDOR_PAYMENT', 'Vendor Payment (Outflow)'),
    ]

    METHOD_CHOICES = [
        ('BANK_TRANSFER', 'Bank Transfer (NEFT / RTGS / IMPS)'),
        ('UPI', 'UPI Payment'),
        ('CHEQUE', 'Cheque'),
        ('CREDIT_CARD', 'Corporate Credit Card'),
        ('CASH', 'Cash'),
        ('DEMAND_DRAFT', 'Demand Draft'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending Clearance'),
        ('COMPLETED', 'Completed / Verified'),
        ('FAILED', 'Failed / Bounced'),
        ('CANCELLED', 'Cancelled'),
    ]

    payment_number = models.CharField(max_length=50, unique=True, help_text="e.g. PAY-2026-001")
    payment_type = models.CharField(max_length=25, choices=TYPE_CHOICES, default='CUSTOMER_RECEIPT')
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="Associated customer invoice (for customer receipts)"
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        help_text="Associated vendor PO (for vendor payments)"
    )
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=25, choices=METHOD_CHOICES, default='BANK_TRANSFER')
    reference_number = models.CharField(max_length=100, blank=True, null=True, help_text="UTR / Cheque / Transaction Ref Number")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='COMPLETED')
    is_reconciled = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-payment_date', '-created_at']

    def __str__(self):
        party = self.customer.company_name if self.customer else (self.vendor.company_name if self.vendor else 'General')
        return f"{self.payment_number} - {self.get_payment_type_display()}: ₹{self.amount} ({party})"

    def save(self, *args, **kwargs):
        # Auto associate customer / vendor from invoice / PO if missing
        if self.invoice and not self.customer:
            self.customer = self.invoice.customer
        if self.purchase_order and not self.vendor:
            self.vendor = self.purchase_order.vendor

        super().save(*args, **kwargs)

        # Trigger auto-reconciliation on Invoice
        if self.invoice and self.status == 'COMPLETED':
            total_paid = sum(
                p.amount for p in self.invoice.payments.filter(status='COMPLETED')
            )
            self.invoice.amount_paid = round(Decimal(total_paid), 2)
            self.invoice.amount_due = max(Decimal('0.00'), self.invoice.grand_total - self.invoice.amount_paid)
            if self.invoice.amount_paid >= self.invoice.grand_total and self.invoice.grand_total > 0:
                self.invoice.status = 'PAID'
            elif self.invoice.amount_paid > 0:
                self.invoice.status = 'PARTIALLY_PAID'
            self.invoice.save(update_fields=['amount_paid', 'amount_due', 'status'])
