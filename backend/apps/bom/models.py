from django.db import models
from django.conf import settings
from decimal import Decimal


class RawMaterial(models.Model):
    CATEGORY_CHOICES = [
        ('METALS', 'Raw Metals & Alloys'),
        ('ELECTRICAL', 'Electrical & Winding'),
        ('FASTENERS', 'Fasteners & Hardware'),
        ('POLYMERS', 'Polymers & Seals'),
        ('CHEMICALS', 'Chemicals, Oils & Paints'),
        ('PACKAGING', 'Packaging & Crating'),
    ]

    UNIT_CHOICES = [
        ('KG', 'Kilograms (kg)'),
        ('MTR', 'Meters (m)'),
        ('PCS', 'Pieces (pcs)'),
        ('LTR', 'Liters (L)'),
        ('SQM', 'Square Meters (sqm)'),
        ('SET', 'Sets (set)'),
    ]

    code = models.CharField(max_length=50, unique=True, help_text="Unique material code e.g. RM-STL-001")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='METALS')
    unit_of_measure = models.CharField(max_length=10, choices=UNIT_CHOICES, default='KG')
    standard_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Cost per unit in INR")
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=50.00, help_text="Minimum threshold trigger for PO")
    safety_stock = models.DecimalField(max_digits=12, decimal_places=2, default=20.00)
    warehouse_location = models.CharField(max_length=100, default='Warehouse Rack A-01')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.name} ({self.current_stock} {self.unit_of_measure})"

    @property
    def is_low_stock(self):
        return self.current_stock <= self.reorder_level

    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'OUT_OF_STOCK'
        elif self.current_stock <= self.reorder_level:
            return 'LOW_STOCK'
        return 'OPTIMAL'


class Product(models.Model):
    product_code = models.CharField(max_length=50, unique=True, help_text="Finished Good Code e.g. FG-MTR-001")
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Industrial Motors & Pumps')
    description = models.TextField(blank=True, null=True)
    unit_of_measure = models.CharField(max_length=10, default='PCS')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    lead_time_days = models.PositiveIntegerField(default=5, help_text="Manufacturing lead time in business days")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['product_code']

    def __str__(self):
        return f"{self.product_code} - {self.name} (₹{self.selling_price})"

    @property
    def total_bom_cost(self):
        if hasattr(self, 'bom'):
            return self.bom.calculated_total_cost
        return Decimal('0.00')

    @property
    def profit_margin(self):
        cost = self.total_bom_cost
        if self.selling_price > 0:
            margin = ((self.selling_price - cost) / self.selling_price) * 100
            return round(margin, 2)
        return 0.00


class BillOfMaterial(models.Model):
    bom_number = models.CharField(max_length=50, unique=True, help_text="e.g. BOM-2026-001")
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='bom')
    version = models.CharField(max_length=20, default='v1.0')
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bom_number} - BOM for {self.product.name} ({self.version})"

    @property
    def calculated_total_cost(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.line_cost
        return round(total, 2)


class BOMItem(models.Model):
    bom = models.ForeignKey(BillOfMaterial, on_delete=models.CASCADE, related_name='items')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, related_name='bom_usages')
    quantity_required = models.DecimalField(max_digits=10, decimal_places=3, help_text="Required quantity per finished good")
    wastage_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=2.00, help_text="Scrap / wastage allowance %")
    notes = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('bom', 'raw_material')

    def __str__(self):
        return f"{self.raw_material.name} x {self.quantity_required} {self.raw_material.unit_of_measure} for {self.bom.product.product_code}"

    @property
    def gross_quantity_required(self):
        factor = Decimal('1') + (self.wastage_percentage / Decimal('100'))
        return round(self.quantity_required * factor, 3)

    @property
    def line_cost(self):
        return round(self.gross_quantity_required * self.raw_material.standard_cost, 2)
