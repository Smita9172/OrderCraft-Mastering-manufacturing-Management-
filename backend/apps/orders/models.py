from django.db import models
from django.conf import settings
from decimal import Decimal
from apps.bom.models import Product


class Customer(models.Model):
    code = models.CharField(max_length=50, unique=True, help_text="e.g. CUST-2026-001")
    company_name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    gst_number = models.CharField(max_length=25, blank=True, null=True, help_text="GST / Tax Identification Number")
    billing_address = models.TextField()
    shipping_address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, default='Mumbai')
    state = models.CharField(max_length=100, default='Maharashtra')
    pincode = models.CharField(max_length=10, default='400001')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['company_name']

    def __str__(self):
        return f"{self.code} - {self.company_name} ({self.contact_person})"


class SalesOrder(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent / Critical'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft Order'),
        ('CONFIRMED', 'Confirmed'),
        ('IN_PRODUCTION', 'In Production'),
        ('READY_FOR_DISPATCH', 'Ready for Dispatch'),
        ('DISPATCHED', 'Dispatched'),
        ('DELIVERED', 'Delivered'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=50, unique=True, help_text="e.g. SO-2026-001")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField()
    delivery_due_date = models.DateField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='DRAFT')
    
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00, help_text="GST Percentage")
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    
    payment_terms = models.CharField(max_length=100, default='Net 30 Days')
    special_instructions = models.TextField(blank=True, null=True, help_text="Customer specific manufacturing specs / notes")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.order_number} - {self.customer.company_name} (₹{self.grand_total})"

    def recalculate_totals(self):
        sub = sum(item.line_total for item in self.items.all())
        self.subtotal = round(Decimal(str(sub)), 2)
        discount = Decimal(str(self.discount_amount or 0))
        taxable = max(Decimal('0.00'), self.subtotal - discount)
        tax_rate = Decimal(str(self.tax_rate or 18))
        self.tax_amount = round(taxable * (tax_rate / Decimal('100')), 2)
        self.grand_total = round(taxable + self.tax_amount, 2)
        self.save(update_fields=['subtotal', 'tax_amount', 'grand_total'])


class SalesOrderItem(models.Model):
    order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    line_total = models.DecimalField(max_digits=14, decimal_places=2, default=0.00)
    specifications = models.TextField(blank=True, null=True, help_text="Custom specs like coating, IP rating, voltage tolerance")

    def save(self, *args, **kwargs):
        gross = Decimal(self.quantity) * self.unit_price
        discount = gross * (self.discount_percentage / Decimal('100'))
        self.line_total = round(gross - discount, 2)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity} for {self.order.order_number}"
