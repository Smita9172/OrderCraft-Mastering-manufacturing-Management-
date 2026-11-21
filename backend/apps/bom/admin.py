from django.contrib import admin
from .models import RawMaterial, Product, BillOfMaterial, BOMItem


class BOMItemInline(admin.TabularInline):
    model = BOMItem
    extra = 1
    fields = ('raw_material', 'quantity_required', 'wastage_percentage', 'notes')


@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'unit_of_measure', 'standard_cost', 'current_stock', 'reorder_level', 'stock_status')
    list_filter = ('category', 'unit_of_measure')
    search_fields = ('code', 'name', 'warehouse_location')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'name', 'category', 'selling_price', 'total_bom_cost', 'profit_margin', 'lead_time_days', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('product_code', 'name')


@admin.register(BillOfMaterial)
class BillOfMaterialAdmin(admin.ModelAdmin):
    list_display = ('bom_number', 'product', 'version', 'is_approved', 'calculated_total_cost', 'updated_at')
    inlines = [BOMItemInline]
    search_fields = ('bom_number', 'product__name')


@admin.register(BOMItem)
class BOMItemAdmin(admin.ModelAdmin):
    list_display = ('bom', 'raw_material', 'quantity_required', 'wastage_percentage', 'line_cost')
