from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.bom.models import RawMaterial
from apps.orders.models import SalesOrder


class Vendor(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="e.g. VND-2026-001")
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=25, blank=True, null=True)
    address = models.TextField()
    city = models.CharField(max_length=100, default='Pune')
    state = models.CharField(max_length=100, default='Maharashtra')
    pincode = models.CharField(max_length=10, default='411001')
    payment_terms = models.CharField(max_length=100, default='Net 30 Days')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return f"{self.code} - {self.company_name} ({self.contact_person})"


class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft PO'),
        ('ISSUED', 'Issued to Vendor'),
        ('ACKNOWLEDGED', 'Acknowledged by Vendor'),
        ('PARTIALLY_RECEIVED', 'Partially Received'),
        ('COMPLETED', 'Completed / Received'),
        ('CANCELLED', 'Cancelled'),
    ]

    po_number = models.CharField(max_length=50, unique=True, help_text="e.g. PO-2026-001")
    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name='purchase_orders')
    linked_sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Optional link if PO was raised due to Sales Order material shortage"
    )
    order_date = models.DateField()
    expected_delivery_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    
    terms_and_conditions = models.TextField(blank=True, null=True, default="Standard delivery terms: Inspection on arrival. Payment within agreed terms upon QC clearance.")
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.po_number} - {self.vendor.company_name} (₹{self.total_amount})"

    def recalculate_totals(self):
        sub = sum(item.line_total for item in self.items.all())
        tax = sum(item.tax_line_amount for item in self.items.all())
        self.subtotal = round(Decimal(str(sub)), 2)
        self.tax_amount = round(Decimal(str(tax)), 2)
        self.total_amount = round(self.subtotal + self.tax_amount, 2)
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount'])


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.PROTECT, related_name='po_lines')
    quantity_ordered = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)

    @property
    def tax_line_amount(self):
        return round(self.line_total * (self.tax_rate / Decimal('100')), 2)

    @property
    def remaining_quantity(self):
        return max(Decimal('0.00'), self.quantity_ordered - self.quantity_received)

    def save(self, *args, **kwargs):
        self.line_total = round(self.quantity_ordered * self.unit_price, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.raw_material.name} x {self.quantity_ordered} {self.raw_material.unit_of_measure} ({self.purchase_order.po_number})"


class GoodsReceiptNote(models.Model):
    grn_number = models.CharField(max_length=50, unique=True, help_text="e.g. GRN-2026-001")
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='grn_records')
    receipt_date = models.DateField()
    challan_number = models.CharField(max_length=100, blank=True, null=True, help_text="Vendor delivery challan/invoice ref")
    remarks = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-receipt_date', '-created_at']

    def __str__(self):
        return f"{self.grn_number} for PO {self.purchase_order.po_number}"


class VendorCommunication(models.Model):
    CHANNEL_CHOICES = [
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Call'),
        ('WHATSAPP', 'WhatsApp / SMS'),
        ('MEETING', 'In-Person / Video Conference'),
    ]

    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='communications')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True, related_name='communications')
    channel = models.CharField(max_length=20, choices=CHANNEL_CHOICES, default='EMAIL')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    date_logged = models.DateTimeField(auto_now_add=True)
    logged_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-date_logged']

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.vendor.company_name}: {self.subject}"
