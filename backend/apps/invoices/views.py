from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
import datetime

from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer, InvoiceItemSerializer
from apps.accounts.views import record_audit


class InvoiceViewSet(viewsets.ModelViewSet):
    queryset = Invoice.objects.all().order_by('-invoice_date', '-created_at')
    serializer_class = InvoiceSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        if not serializer.validated_data.get('invoice_number'):
            count = Invoice.objects.count() + 1
            serializer.validated_data['invoice_number'] = f"INV-2026-{count:04d}"
        invoice = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'INVOICES',
            f"Issued tax invoice {invoice.invoice_number} to {invoice.customer.company_name} (₹{invoice.grand_total})",
            record_id=invoice.id,
            request=self.request
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        inv = self.get_object()
        new_status = request.data.get('status')
        valid = [c[0] for c in Invoice.STATUS_CHOICES]
        if new_status not in valid:
            return Response({'error': f"Invalid status: {new_status}"}, status=status.HTTP_400_BAD_REQUEST)

        inv.status = new_status
        inv.save(update_fields=['status'])

        record_audit(
            request.user,
            'STATUS_CHANGE',
            'INVOICES',
            f"Updated invoice {inv.invoice_number} status to {new_status}",
            record_id=inv.id,
            request=request
        )
        return Response({'message': f"Invoice status changed to {new_status}", 'status': inv.status})

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """
        Record a payment receipt directly against an invoice
        """
        from apps.payments.models import Payment
        inv = self.get_object()
        amount = Decimal(str(request.data.get('amount', inv.amount_due)))
        method = request.data.get('payment_method', 'BANK_TRANSFER')
        ref = request.data.get('reference_number', '')
        pay_date = request.data.get('payment_date', str(datetime.date.today()))
        notes = request.data.get('notes', f"Settlement for {inv.invoice_number}")

        if amount <= 0:
            return Response({'error': 'Amount must be greater than zero'}, status=status.HTTP_400_BAD_REQUEST)

        pay_count = Payment.objects.count() + 1
        payment = Payment.objects.create(
            payment_number=f"PAY-2026-{pay_count:04d}",
            payment_type='CUSTOMER_RECEIPT',
            invoice=inv,
            customer=inv.customer,
            amount=amount,
            payment_date=pay_date,
            payment_method=method,
            reference_number=ref,
            status='COMPLETED',
            notes=notes,
            recorded_by=request.user if request.user.is_authenticated else None
        )

        record_audit(
            request.user,
            'CREATE',
            'PAYMENTS',
            f"Recorded payment receipt {payment.payment_number} of ₹{amount} for invoice {inv.invoice_number} via {method}",
            record_id=payment.id,
            request=request
        )

        inv.refresh_from_db()

        return Response({
            'message': f"Payment recorded successfully! Invoice status: {inv.status}",
            'payment_number': payment.payment_number,
            'invoice_status': inv.status,
            'amount_paid': float(inv.amount_paid),
            'amount_due': float(inv.amount_due)
        })
