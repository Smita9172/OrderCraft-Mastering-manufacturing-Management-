from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_number', 'payment_type', 'amount', 'payment_date', 'payment_method', 'reference_number', 'status', 'is_reconciled')
    list_filter = ('payment_type', 'payment_method', 'status', 'payment_date')
    search_fields = ('payment_number', 'reference_number', 'customer__company_name', 'vendor__company_name')
