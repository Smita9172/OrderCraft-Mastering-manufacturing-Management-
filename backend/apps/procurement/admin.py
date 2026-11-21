from django.contrib import admin
from .models import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, VendorCommunication


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('raw_material', 'quantity_ordered', 'quantity_received', 'unit_price', 'tax_rate', 'line_total')
    readonly_fields = ('line_total',)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('code', 'company_name', 'contact_person', 'email', 'phone', 'city', 'rating', 'is_active')
    search_fields = ('code', 'company_name', 'contact_person')
    list_filter = ('is_active', 'rating')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'vendor', 'order_date', 'expected_delivery_date', 'status', 'total_amount')
    list_filter = ('status', 'order_date')
    search_fields = ('po_number', 'vendor__company_name')
    inlines = [PurchaseOrderItemInline]


@admin.register(GoodsReceiptNote)
class GoodsReceiptNoteAdmin(admin.ModelAdmin):
    list_display = ('grn_number', 'purchase_order', 'receipt_date', 'challan_number', 'received_by')
    search_fields = ('grn_number', 'purchase_order__po_number', 'challan_number')


@admin.register(VendorCommunication)
class VendorCommunicationAdmin(admin.ModelAdmin):
    list_display = ('vendor', 'channel', 'subject', 'date_logged', 'logged_by')
    list_filter = ('channel', 'date_logged')
    search_fields = ('subject', 'message', 'vendor__company_name')
