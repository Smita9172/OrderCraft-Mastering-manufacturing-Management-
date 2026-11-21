from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
import datetime

from .models import Customer, SalesOrder, SalesOrderItem
from .serializers import CustomerSerializer, SalesOrderSerializer, SalesOrderItemSerializer
from apps.accounts.views import record_audit


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('company_name')
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        customer = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'ORDERS',
            f"Created customer '{customer.company_name}' ({customer.code})",
            record_id=customer.id,
            request=self.request
        )


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all().order_by('-created_at')
    serializer_class = SalesOrderSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        # Auto generate order number if not supplied
        if not serializer.validated_data.get('order_number'):
            count = SalesOrder.objects.count() + 1
            serializer.validated_data['order_number'] = f"SO-2026-{count:04d}"
        order = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'ORDERS',
            f"Booked new sales order {order.order_number} for {order.customer.company_name} (₹{order.grand_total})",
            record_id=order.id,
            request=self.request
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        valid_statuses = [choice[0] for choice in SalesOrder.STATUS_CHOICES]
        
        if new_status not in valid_statuses:
            return Response({'error': f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}, status=status.HTTP_400_BAD_REQUEST)

        old_status = order.status
        order.status = new_status
        order.save(update_fields=['status'])

        record_audit(
            request.user,
            'STATUS_CHANGE',
            'ORDERS',
            f"Changed order {order.order_number} status from {old_status} to {new_status}",
            record_id=order.id,
            request=request
        )

        return Response({
            'message': f"Order status updated to {new_status}",
            'status': order.status,
            'status_display': order.get_status_display()
        })

    @action(detail=True, methods=['get'])
    def check_materials(self, request, pk=None):
        """
        Check raw material availability for all line items in this order
        """
        order = self.get_object()
        materials_needed = {}

        for item in order.items.all():
            product = item.product
            if hasattr(product, 'bom'):
                for bom_item in product.bom.items.all():
                    rm = bom_item.raw_material
                    req_qty = bom_item.gross_quantity_required * Decimal(item.quantity)
                    
                    if rm.id not in materials_needed:
                        materials_needed[rm.id] = {
                            'material_id': rm.id,
                            'code': rm.code,
                            'name': rm.name,
                            'unit': rm.unit_of_measure,
                            'current_stock': float(rm.current_stock),
                            'total_required': Decimal('0.00'),
                            'standard_cost': float(rm.standard_cost)
                        }
                    materials_needed[rm.id]['total_required'] += req_qty

        result = []
        overall_shortage = False
        for m in materials_needed.values():
            req = round(m['total_required'], 2)
            stock = Decimal(str(m['current_stock']))
            shortage = max(Decimal('0.00'), req - stock)
            is_short = shortage > Decimal('0.00')
            if is_short:
                overall_shortage = True
            result.append({
                'material_id': m['material_id'],
                'code': m['code'],
                'name': m['name'],
                'unit': m['unit'],
                'unit_cost': m['standard_cost'],
                'current_stock': float(stock),
                'total_required': float(req),
                'shortage_quantity': float(shortage),
                'is_shortage': is_short
            })

        return Response({
            'order_number': order.order_number,
            'customer': order.customer.company_name,
            'overall_shortage': overall_shortage,
            'materials': result
        })

    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """
        1-Click convert sales order to invoice
        """
        from apps.invoices.models import Invoice, InvoiceItem
        order = self.get_object()

        if order.invoices.exists():
            inv = order.invoices.first()
            return Response({
                'message': 'Invoice already exists for this order',
                'invoice_id': inv.id,
                'invoice_number': inv.invoice_number
            })

        count = Invoice.objects.count() + 1
        inv_number = f"INV-2026-{count:04d}"
        today = datetime.date.today()
        due_date = today + datetime.timedelta(days=30)

        invoice = Invoice.objects.create(
            invoice_number=inv_number,
            sales_order=order,
            customer=order.customer,
            invoice_date=today,
            due_date=due_date,
            payment_terms=order.payment_terms,
            status='ISSUED',
            subtotal=order.subtotal,
            cgst_rate=Decimal('9.00'),
            sgst_rate=Decimal('9.00'),
            igst_rate=Decimal('0.00'),
            discount_amount=order.discount_amount,
            grand_total=order.grand_total,
            amount_due=order.grand_total,
            amount_paid=Decimal('0.00'),
            created_by=request.user if request.user.is_authenticated else None
        )

        for item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=item.product,
                description=f"{item.product.name} (Ref: {order.order_number})",
                hsn_sac_code='8501',
                quantity=item.quantity,
                unit_price=item.unit_price,
                tax_rate=Decimal('18.00'),
                line_total=item.line_total
            )

        invoice.recalculate_totals()

        record_audit(
            request.user,
            'CREATE',
            'INVOICES',
            f"Generated invoice {invoice.invoice_number} from sales order {order.order_number} for ₹{invoice.grand_total}",
            record_id=invoice.id,
            request=request
        )

        return Response({
            'message': f"Invoice {invoice.invoice_number} created successfully!",
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number
        })
