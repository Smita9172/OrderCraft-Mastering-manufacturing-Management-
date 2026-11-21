from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    payment_type_display = serializers.CharField(source='get_payment_type_display', read_only=True)
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    party_name = serializers.SerializerMethodField()
    document_ref = serializers.SerializerMethodField()

    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'payment_type', 'payment_type_display',
            'invoice', 'purchase_order', 'customer', 'vendor',
            'party_name', 'document_ref', 'amount', 'payment_date',
            'payment_method', 'payment_method_display', 'reference_number',
            'status', 'status_display', 'is_reconciled', 'notes',
            'created_at', 'updated_at'
        ]

    def get_party_name(self, obj):
        if obj.customer:
            return obj.customer.company_name
        if obj.vendor:
            return obj.vendor.company_name
        return "N/A"

    def get_document_ref(self, obj):
        if obj.invoice:
            return f"Invoice {obj.invoice.invoice_number}"
        if obj.purchase_order:
            return f"PO {obj.purchase_order.po_number}"
        return "-"
