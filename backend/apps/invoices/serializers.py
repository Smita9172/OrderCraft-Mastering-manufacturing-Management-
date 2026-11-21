from rest_framework import serializers
from .models import Invoice, InvoiceItem
from decimal import Decimal


class InvoiceItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)

    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'invoice', 'product', 'product_name', 'description',
            'hsn_sac_code', 'quantity', 'unit_price', 'tax_rate', 'line_total'
        ]
        extra_kwargs = {'invoice': {'required': False}}


class InvoiceSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    customer_phone = serializers.CharField(source='customer.phone', read_only=True)
    customer_gst = serializers.CharField(source='customer.gst_number', read_only=True)
    customer_address = serializers.CharField(source='customer.billing_address', read_only=True)
    sales_order_number = serializers.CharField(source='sales_order.order_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = InvoiceItemSerializer(many=True, required=False)
    payments_count = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'sales_order', 'sales_order_number',
            'customer', 'customer_name', 'customer_email', 'customer_phone',
            'customer_gst', 'customer_address',
            'invoice_date', 'due_date', 'payment_terms', 'status', 'status_display',
            'subtotal', 'cgst_rate', 'cgst_amount', 'sgst_rate', 'sgst_amount',
            'igst_rate', 'igst_amount', 'discount_amount', 'grand_total',
            'amount_paid', 'amount_due', 'bank_details', 'notes',
            'payments_count', 'items', 'created_at', 'updated_at'
        ]

    def get_payments_count(self, obj):
        return obj.payments.count()

    def create(self, validated_data):
        items_data = self.context.get('request').data.get('items', []) if self.context.get('request') else []
        invoice = Invoice.objects.create(**validated_data)

        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                product_id=item_data.get('product'),
                description=item_data.get('description', 'Manufacturing Component'),
                hsn_sac_code=item_data.get('hsn_sac_code', '8501'),
                quantity=int(item_data.get('quantity', 1)),
                unit_price=Decimal(str(item_data.get('unit_price', 0))),
                tax_rate=Decimal(str(item_data.get('tax_rate', 18))),
                line_total=Decimal(str(item_data.get('line_total', 0)))
            )

        invoice.recalculate_totals()
        return invoice
