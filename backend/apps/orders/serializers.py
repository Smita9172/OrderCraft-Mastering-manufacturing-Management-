from rest_framework import serializers
from .models import Customer, SalesOrder, SalesOrderItem
from apps.bom.models import Product
from decimal import Decimal


class CustomerSerializer(serializers.ModelSerializer):
    orders_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = '__all__'

    def get_orders_count(self, obj):
        return obj.sales_orders.count()

    def get_total_spent(self, obj):
        total = sum(order.grand_total for order in obj.sales_orders.filter(status__in=['DELIVERED', 'DISPATCHED', 'CONFIRMED', 'IN_PRODUCTION']))
        return round(float(total), 2)


class SalesOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    unit_of_measure = serializers.CharField(source='product.unit_of_measure', read_only=True)

    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'order', 'product', 'product_name', 'product_code',
            'unit_of_measure', 'quantity', 'unit_price', 'discount_percentage',
            'line_total', 'specifications'
        ]
        extra_kwargs = {'order': {'required': False}}


class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.company_name', read_only=True)
    customer_code = serializers.CharField(source='customer.code', read_only=True)
    customer_city = serializers.CharField(source='customer.city', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items = SalesOrderItemSerializer(many=True, required=False)
    has_invoice = serializers.SerializerMethodField()
    invoice_id = serializers.SerializerMethodField()

    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'customer_code', 'customer_city',
            'order_date', 'delivery_due_date', 'priority', 'priority_display',
            'status', 'status_display', 'subtotal', 'tax_rate', 'tax_amount',
            'discount_amount', 'grand_total', 'payment_terms', 'special_instructions',
            'has_invoice', 'invoice_id', 'items', 'created_at', 'updated_at'
        ]

    def get_has_invoice(self, obj):
        return obj.invoices.exists()

    def get_invoice_id(self, obj):
        inv = obj.invoices.first()
        return inv.id if inv else None

    def create(self, validated_data):
        items_data = self.context.get('request').data.get('items', []) if self.context.get('request') else []
        order = SalesOrder.objects.create(**validated_data)
        
        for item_data in items_data:
            product_id = item_data.get('product')
            quantity = int(item_data.get('quantity', 1))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            discount_pct = Decimal(str(item_data.get('discount_percentage', 0)))
            specs = item_data.get('specifications', '')

            if not unit_price and product_id:
                product = Product.objects.get(id=product_id)
                unit_price = product.selling_price

            SalesOrderItem.objects.create(
                order=order,
                product_id=product_id,
                quantity=quantity,
                unit_price=unit_price,
                discount_percentage=discount_pct,
                specifications=specs
            )
            
        order.recalculate_totals()
        return order
