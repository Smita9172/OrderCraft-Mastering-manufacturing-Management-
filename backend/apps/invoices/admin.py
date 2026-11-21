from django.contrib import admin
from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    fields = ('product', 'description', 'hsn_sac_code', 'quantity', 'unit_price', 'tax_rate', 'line_total')
    readonly_fields = ('line_total',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'sales_order', 'invoice_date', 'due_date', 'status', 'grand_total', 'amount_paid', 'amount_due')
    list_filter = ('status', 'invoice_date', 'payment_terms')
    search_fields = ('invoice_number', 'customer__company_name', 'sales_order__order_number')
    inlines = [InvoiceItemInline]
