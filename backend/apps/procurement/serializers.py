from rest_framework import serializers
from .models import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, VendorCommunication
from apps.bom.models import RawMaterial
from decimal import Decimal


class VendorSerializer(serializers.ModelSerializer):
    po_count = serializers.SerializerMethodField()
    total_purchased = serializers.SerializerMethodField()

    class Meta:
        model = Vendor
        fields = '__all__'

    def get_po_count(self, obj):
        return obj.purchase_orders.count()

    def get_total_purchased(self, obj):
        total = sum(po.total_amount for po in obj.purchase_orders.all())
        return round(float(total), 2)


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    material_code = serializers.CharField(source='raw_material.code', read_only=True)
    material_name = serializers.CharField(source='raw_material.name', read_only=True)
    unit_of_measure = serializers.CharField(source='raw_material.unit_of_measure', read_only=True)
    remaining_quantity = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'purchase_order', 'raw_material', 'material_code', 'material_name',
            'unit_of_measure', 'quantity_ordered', 'quantity_received',
            'remaining_quantity', 'unit_price', 'tax_rate', 'line_total'
        ]
        extra_kwargs = {'purchase_order': {'required': False}}


class GoodsReceiptNoteSerializer(serializers.ModelSerializer):
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    vendor_name = serializers.CharField(source='purchase_order.vendor.company_name', read_only=True)
    received_by_name = serializers.CharField(source='received_by.username', read_only=True)

    class Meta:
        model = GoodsReceiptNote
        fields = '__all__'


class VendorCommunicationSerializer(serializers.ModelSerializer):
    channel_display = serializers.CharField(source='get_channel_display', read_only=True)
    logged_by_name = serializers.CharField(source='logged_by.username', read_only=True)

    class Meta:
        model = VendorCommunication
        fields = '__all__'


class PurchaseOrderSerializer(serializers.ModelSerializer):
    vendor_name = serializers.CharField(source='vendor.company_name', read_only=True)
    vendor_code = serializers.CharField(source='vendor.code', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    linked_order_number = serializers.CharField(source='linked_sales_order.order_number', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, required=False)
    receipts = GoodsReceiptNoteSerializer(many=True, read_only=True, source='grn_records')

    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'po_number', 'vendor', 'vendor_name', 'vendor_code',
            'linked_sales_order', 'linked_order_number',
            'order_date', 'expected_delivery_date', 'status', 'status_display',
            'subtotal', 'tax_amount', 'total_amount', 'terms_and_conditions',
            'notes', 'items', 'receipts', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        items_data = self.context.get('request').data.get('items', []) if self.context.get('request') else []
        po = PurchaseOrder.objects.create(**validated_data)

        for item_data in items_data:
            material_id = item_data.get('raw_material')
            qty = Decimal(str(item_data.get('quantity_ordered', 1)))
            unit_price = Decimal(str(item_data.get('unit_price', 0)))
            tax_rate = Decimal(str(item_data.get('tax_rate', 18)))

            if not unit_price and material_id:
                rm = RawMaterial.objects.get(id=material_id)
                unit_price = rm.standard_cost

            PurchaseOrderItem.objects.create(
                purchase_order=po,
                raw_material_id=material_id,
                quantity_ordered=qty,
                quantity_received=Decimal('0.00'),
                unit_price=unit_price,
                tax_rate=tax_rate
            )

        po.recalculate_totals()
        return po
