from rest_framework import serializers
from .models import RawMaterial, Product, BillOfMaterial, BOMItem
from decimal import Decimal


class RawMaterialSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    unit_display = serializers.CharField(source='get_unit_of_measure_display', read_only=True)
    stock_status = serializers.CharField(read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_valuation = serializers.SerializerMethodField()

    class Meta:
        model = RawMaterial
        fields = '__all__'

    def get_stock_valuation(self, obj):
        return round(float(obj.current_stock * obj.standard_cost), 2)


class BOMItemSerializer(serializers.ModelSerializer):
    raw_material_code = serializers.CharField(source='raw_material.code', read_only=True)
    raw_material_name = serializers.CharField(source='raw_material.name', read_only=True)
    raw_material_unit = serializers.CharField(source='raw_material.unit_of_measure', read_only=True)
    standard_cost = serializers.DecimalField(source='raw_material.standard_cost', max_digits=12, decimal_places=2, read_only=True)
    gross_quantity_required = serializers.DecimalField(max_digits=10, decimal_places=3, read_only=True)
    line_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = BOMItem
        fields = [
            'id', 'bom', 'raw_material', 'raw_material_code', 'raw_material_name',
            'raw_material_unit', 'standard_cost', 'quantity_required',
            'wastage_percentage', 'gross_quantity_required', 'line_cost', 'notes'
        ]
        extra_kwargs = {'bom': {'required': False}}


class BillOfMaterialSerializer(serializers.ModelSerializer):
    items = BOMItemSerializer(many=True, read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_code = serializers.CharField(source='product.product_code', read_only=True)
    total_cost = serializers.DecimalField(source='calculated_total_cost', max_digits=12, decimal_places=2, read_only=True)
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = BillOfMaterial
        fields = [
            'id', 'bom_number', 'product', 'product_name', 'product_code',
            'version', 'is_active', 'is_approved', 'notes',
            'total_cost', 'items_count', 'items', 'created_at', 'updated_at'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class ProductSerializer(serializers.ModelSerializer):
    bom_details = serializers.SerializerMethodField()
    total_bom_cost = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    profit_margin = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'product_code', 'name', 'category', 'description',
            'unit_of_measure', 'selling_price', 'lead_time_days',
            'is_active', 'total_bom_cost', 'profit_margin', 'bom_details',
            'created_at', 'updated_at'
        ]

    def get_bom_details(self, obj):
        if hasattr(obj, 'bom'):
            return {
                'id': obj.bom.id,
                'bom_number': obj.bom.bom_number,
                'version': obj.bom.version,
                'items_count': obj.bom.items.count(),
                'total_cost': float(obj.bom.calculated_total_cost)
            }
        return None
