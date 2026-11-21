from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.orders.models import SalesOrder, Customer
from apps.bom.models import Product


class Invoice(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft Invoice'),
        ('ISSUED', 'Issued / Sent to Customer'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Fully Paid'),
        ('OVERDUE', 'Payment Overdue'),
        ('CANCELLED', 'Cancelled'),
    ]

    invoice_number = models.CharField(max_length=50, unique=True, help_text="e.g. INV-2026-001")
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Originating Sales Order"
    )
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    invoice_date = models.DateField()
    due_date = models.DateField()
    payment_terms = models.CharField(max_length=100, default='Net 30 Days')
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='DRAFT')

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    cgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    cgst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    sgst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    sgst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    igst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    igst_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    amount_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    amount_due = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    bank_details = models.TextField(
        default="Bank: State Bank of India\nA/C Name: Apex Precision Engineering Pvt Ltd\nA/C No: 398201948201\nIFSC: SBIN0004521\nBranch: Andheri East Industrial Estate, Mumbai"
    )
    notes = models.TextField(blank=True, null=True, default="Thank you for your business. Please quote invoice number on bank transfer payments.")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-invoice_date', '-created_at']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.company_name} (₹{self.grand_total})"

    def recalculate_totals(self):
        sub = sum(item.line_total for item in self.items.all())
        self.subtotal = round(Decimal(str(sub)), 2)
        discount = Decimal(str(self.discount_amount or 0))
        taxable = max(Decimal('0.00'), self.subtotal - discount)
        
        cgst_r = Decimal(str(self.cgst_rate or 0))
        sgst_r = Decimal(str(self.sgst_rate or 0))
        igst_r = Decimal(str(self.igst_rate or 0))

        self.cgst_amount = round(taxable * (cgst_r / Decimal('100')), 2)
        self.sgst_amount = round(taxable * (sgst_r / Decimal('100')), 2)
        self.igst_amount = round(taxable * (igst_r / Decimal('100')), 2)
        
        total_tax = self.cgst_amount + self.sgst_amount + self.igst_amount
        self.grand_total = round(taxable + total_tax, 2)
        paid = Decimal(str(self.amount_paid or 0))
        self.amount_due = max(Decimal('0.00'), self.grand_total - paid)
        
        if paid >= self.grand_total and self.grand_total > 0:
            self.status = 'PAID'
        elif paid > 0:
            self.status = 'PARTIALLY_PAID'
            
        self.save()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.CharField(max_length=255)
    hsn_sac_code = models.CharField(max_length=20, default='8501', help_text="Harmonized System of Nomenclature code")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.line_total = round(Decimal(self.quantity) * self.unit_price, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description} x {self.quantity} ({self.invoice.invoice_number})"
