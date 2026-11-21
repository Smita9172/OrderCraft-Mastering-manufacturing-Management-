from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from decimal import Decimal
from .models import RawMaterial, Product, BillOfMaterial, BOMItem
from .serializers import RawMaterialSerializer, ProductSerializer, BillOfMaterialSerializer, BOMItemSerializer
from apps.accounts.views import record_audit


class RawMaterialViewSet(viewsets.ModelViewSet):
    queryset = RawMaterial.objects.all().order_by('code')
    serializer_class = RawMaterialSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        item = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'BOM',
            f"Added raw material '{item.name}' ({item.code}) with initial stock {item.current_stock} {item.unit_of_measure}",
            record_id=item.id,
            request=self.request
        )

    def perform_update(self, serializer):
        item = serializer.save()
        record_audit(
            self.request.user,
            'UPDATE',
            'BOM',
            f"Updated raw material '{item.name}' ({item.code}), stock: {item.current_stock}",
            record_id=item.id,
            request=self.request
        )

    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        material = self.get_object()
        qty = Decimal(str(request.data.get('quantity', 0)))
        reason = request.data.get('reason', 'Manual Inventory Adjustment')
        
        material.current_stock += qty
        material.save()

        record_audit(
            request.user,
            'UPDATE',
            'BOM',
            f"Stock adjusted for {material.code} by {qty} ({reason}). New stock: {material.current_stock}",
            record_id=material.id,
            request=request
        )
        return Response({
            'message': 'Stock updated successfully',
            'current_stock': float(material.current_stock),
            'stock_status': material.stock_status
        })


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().order_by('product_code')
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        prod = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'BOM',
            f"Created finished product '{prod.name}' ({prod.product_code})",
            record_id=prod.id,
            request=self.request
        )


class BillOfMaterialViewSet(viewsets.ModelViewSet):
    queryset = BillOfMaterial.objects.all().order_by('-created_at')
    serializer_class = BillOfMaterialSerializer
    permission_classes = [AllowAny]

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        bom = self.get_object()
        raw_material_id = request.data.get('raw_material_id')
        qty = Decimal(str(request.data.get('quantity_required', 1)))
        wastage = Decimal(str(request.data.get('wastage_percentage', 0)))
        notes = request.data.get('notes', '')

        material = RawMaterial.objects.get(id=raw_material_id)
        item, created = BOMItem.objects.update_or_create(
            bom=bom,
            raw_material=material,
            defaults={
                'quantity_required': qty,
                'wastage_percentage': wastage,
                'notes': notes
            }
        )
        return Response(BOMItemSerializer(item).data)


class BOMItemViewSet(viewsets.ModelViewSet):
    queryset = BOMItem.objects.all()
    serializer_class = BOMItemSerializer
    permission_classes = [AllowAny]


class BOMExplosionView(APIView):
    """
    Module 2 Core Feature:
    Simulates BOM material breakdown for a product batch or sales order.
    Checks stock levels and flags shortages for purchase requisition.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        product_id = request.data.get('product_id')
        order_quantity = Decimal(str(request.data.get('quantity', 1)))

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        if not hasattr(product, 'bom'):
            return Response({'error': f'No Bill of Materials configured for {product.name}'}, status=status.HTTP_400_BAD_REQUEST)

        bom = product.bom
        items_analysis = []
        total_estimated_material_cost = Decimal('0.00')
        has_shortage = False

        for item in bom.items.all().select_related('raw_material'):
            rm = item.raw_material
            required_qty = round(item.gross_quantity_required * order_quantity, 3)
            avail_stock = rm.current_stock
            shortage = max(Decimal('0.00'), required_qty - avail_stock)
            is_item_shortage = shortage > Decimal('0.00')
            if is_item_shortage:
                has_shortage = True

            line_cost = round(required_qty * rm.standard_cost, 2)
            total_estimated_material_cost += line_cost

            items_analysis.append({
                'material_id': rm.id,
                'material_code': rm.code,
                'material_name': rm.name,
                'unit': rm.unit_of_measure,
                'unit_cost': float(rm.standard_cost),
                'qty_per_unit': float(item.quantity_required),
                'wastage_pct': float(item.wastage_percentage),
                'total_required': float(required_qty),
                'current_stock': float(avail_stock),
                'shortage_quantity': float(shortage),
                'is_shortage': is_item_shortage,
                'total_cost': float(line_cost)
            })

        record_audit(
            request.user,
            'EXPLODE_BOM',
            'BOM',
            f"Ran BOM explosion for {order_quantity} units of {product.name}. Shortage detected: {has_shortage}",
            record_id=bom.id,
            request=request
        )

        return Response({
            'product_name': product.name,
            'product_code': product.product_code,
            'order_quantity': float(order_quantity),
            'bom_number': bom.bom_number,
            'version': bom.version,
            'has_shortage': has_shortage,
            'total_material_cost': float(round(total_estimated_material_cost, 2)),
            'unit_material_cost': float(round(total_estimated_material_cost / order_quantity, 2)),
            'items': items_analysis
        })
