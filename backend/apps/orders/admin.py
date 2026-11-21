from django.contrib import admin
from .models import Customer, SalesOrder, SalesOrderItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'discount_percentage', 'line_total', 'specifications')
    readonly_fields = ('line_total',)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('code', 'company_name', 'contact_person', 'email', 'phone', 'city', 'is_active')
    search_fields = ('code', 'company_name', 'contact_person', 'email')
    list_filter = ('is_active', 'state')


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'order_date', 'delivery_due_date', 'priority', 'status', 'grand_total')
    list_filter = ('status', 'priority', 'order_date')
    search_fields = ('order_number', 'customer__company_name')
    inlines = [SalesOrderItemInline]
