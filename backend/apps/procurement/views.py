from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
import datetime

from .models import Vendor, PurchaseOrder, PurchaseOrderItem, GoodsReceiptNote, VendorCommunication
from .serializers import (
    VendorSerializer, PurchaseOrderSerializer, PurchaseOrderItemSerializer,
    GoodsReceiptNoteSerializer, VendorCommunicationSerializer
)
from apps.accounts.views import record_audit


class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all().order_by('company_name')
    serializer_class = VendorSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        vendor = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'PROCUREMENT',
            f"Onboarded new vendor '{vendor.company_name}' ({vendor.code})",
            record_id=vendor.id,
            request=self.request
        )


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    queryset = PurchaseOrder.objects.all().order_by('-created_at')
    serializer_class = PurchaseOrderSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        if not serializer.validated_data.get('po_number'):
            count = PurchaseOrder.objects.count() + 1
            serializer.validated_data['po_number'] = f"PO-2026-{count:04d}"
        po = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'PROCUREMENT',
            f"Created purchase order {po.po_number} for vendor {po.vendor.company_name} (₹{po.total_amount})",
            record_id=po.id,
            request=self.request
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        po = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in PurchaseOrder.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'error': f"Invalid status: {new_status}"}, status=status.HTTP_400_BAD_REQUEST)

        po.status = new_status
        po.save(update_fields=['status'])

        record_audit(
            request.user,
            'STATUS_CHANGE',
            'PROCUREMENT',
            f"Purchase order {po.po_number} status changed to {new_status}",
            record_id=po.id,
            request=request
        )
        return Response({'message': f"PO status updated to {new_status}", 'status': po.status})

    @action(detail=True, methods=['post'])
    def receive_goods(self, request, pk=None):
        """
        Goods Receipt Note (GRN) workflow:
        Increments RawMaterial stock and updates PO lines
        """
        po = self.get_object()
        received_items = request.data.get('items', [])
        challan_no = request.data.get('challan_number', 'CH-REC')
        remarks = request.data.get('remarks', 'Goods received in warehouse')

        grn_count = GoodsReceiptNote.objects.count() + 1
        grn = GoodsReceiptNote.objects.create(
            grn_number=f"GRN-2026-{grn_count:04d}",
            purchase_order=po,
            receipt_date=datetime.date.today(),
            challan_number=challan_no,
            remarks=remarks,
            received_by=request.user if request.user.is_authenticated else None
        )

        all_completed = True
        for item_data in received_items:
            po_item_id = item_data.get('item_id')
            qty_received = Decimal(str(item_data.get('quantity_received', 0)))

            if qty_received > 0:
                po_item = PurchaseOrderItem.objects.get(id=po_item_id, purchase_order=po)
                po_item.quantity_received += qty_received
                po_item.save()

                # Increment raw material stock
                raw_mat = po_item.raw_material
                raw_mat.current_stock += qty_received
                raw_mat.save()

                record_audit(
                    request.user,
                    'RECEIVE_GOODS',
                    'PROCUREMENT',
                    f"Received {qty_received} {raw_mat.unit_of_measure} of {raw_mat.name} against PO {po.po_number}. New stock: {raw_mat.current_stock}",
                    record_id=raw_mat.id,
                    request=request
                )

        # Check if all items are fully received
        for itm in po.items.all():
            if itm.quantity_received < itm.quantity_ordered:
                all_completed = False
                break

        if all_completed:
            po.status = 'COMPLETED'
        else:
            po.status = 'PARTIALLY_RECEIVED'
        po.save(update_fields=['status'])

        return Response({
            'message': f"Goods received under GRN {grn.grn_number}",
            'grn_number': grn.grn_number,
            'po_status': po.status
        })


class GoodsReceiptNoteViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GoodsReceiptNote.objects.all().order_by('-created_at')
    serializer_class = GoodsReceiptNoteSerializer
    permission_classes = [AllowAny]


class VendorCommunicationViewSet(viewsets.ModelViewSet):
    queryset = VendorCommunication.objects.all().order_by('-date_logged')
    serializer_class = VendorCommunicationSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        comm = serializer.save(logged_by=self.request.user if self.request.user.is_authenticated else None)
        record_audit(
            self.request.user,
            'CREATE',
            'PROCUREMENT',
            f"Logged {comm.get_channel_display()} with {comm.vendor.company_name}: {comm.subject}",
            record_id=comm.id,
            request=self.request
        )
