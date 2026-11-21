from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from decimal import Decimal
from django.db.models import Sum

from .models import Payment
from .serializers import PaymentSerializer
from apps.invoices.models import Invoice
from apps.procurement.models import PurchaseOrder
from apps.accounts.views import record_audit


class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all().order_by('-payment_date', '-created_at')
    serializer_class = PaymentSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        if not serializer.validated_data.get('payment_number'):
            count = Payment.objects.count() + 1
            serializer.validated_data['payment_number'] = f"PAY-2026-{count:04d}"
        payment = serializer.save(recorded_by=self.request.user if self.request.user.is_authenticated else None)
        record_audit(
            self.request.user,
            'CREATE',
            'PAYMENTS',
            f"Recorded {payment.get_payment_type_display()} {payment.payment_number} of ₹{payment.amount} via {payment.get_payment_method_display()}",
            record_id=payment.id,
            request=self.request
        )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        inflow = Payment.objects.filter(
            payment_type='CUSTOMER_RECEIPT', status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        outflow = Payment.objects.filter(
            payment_type='VENDOR_PAYMENT', status='COMPLETED'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        receivables = Invoice.objects.filter(
            status__in=['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']
        ).aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

        payables = PurchaseOrder.objects.filter(
            status__in=['ISSUED', 'CONFIRMED', 'PARTIALLY_RECEIVED', 'COMPLETED']
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00') - outflow

        return Response({
            'total_inflow': float(inflow),
            'total_outflow': float(outflow),
            'net_cashflow': float(inflow - outflow),
            'accounts_receivable': float(receivables),
            'accounts_payable': float(max(Decimal('0.00'), payables))
        })
