from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Sum, Count, F, Q
from decimal import Decimal
import datetime

from apps.orders.models import SalesOrder, SalesOrderItem, Customer
from apps.bom.models import Product, RawMaterial, BillOfMaterial
from apps.procurement.models import PurchaseOrder, Vendor
from apps.invoices.models import Invoice
from apps.payments.models import Payment


class DashboardOverviewView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Orders metrics
        total_orders = SalesOrder.objects.count()
        active_orders = SalesOrder.objects.filter(status__in=['CONFIRMED', 'IN_PRODUCTION', 'READY_FOR_DISPATCH']).count()
        delivered_orders = SalesOrder.objects.filter(status='DELIVERED').count()
        total_order_value = SalesOrder.objects.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')

        # Invoices & Revenue
        total_invoiced = Invoice.objects.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        revenue_collected = Invoice.objects.aggregate(total=Sum('amount_paid'))['total'] or Decimal('0.00')
        outstanding_receivables = Invoice.objects.filter(status__in=['ISSUED', 'PARTIALLY_PAID', 'OVERDUE']).aggregate(total=Sum('amount_due'))['total'] or Decimal('0.00')

        # Procurement & Payables
        total_po_value = PurchaseOrder.objects.aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        vendor_payments_made = Payment.objects.filter(payment_type='VENDOR_PAYMENT', status='COMPLETED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        outstanding_payables = max(Decimal('0.00'), total_po_value - vendor_payments_made)

        # Inventory Health
        raw_materials_count = RawMaterial.objects.count()
        low_stock_materials = [rm for rm in RawMaterial.objects.all() if rm.is_low_stock]
        total_inventory_valuation = sum(rm.current_stock * rm.standard_cost for rm in RawMaterial.objects.all())

        # BOM & Products
        total_products = Product.objects.count()
        active_boms = BillOfMaterial.objects.filter(is_active=True).count()

        # Net Profit Calculation
        estimated_profit = revenue_collected - vendor_payments_made

        return Response({
            'kpis': {
                'total_orders': total_orders,
                'active_orders': active_orders,
                'delivered_orders': delivered_orders,
                'total_order_value': float(total_order_value),
                'total_invoiced': float(total_invoiced),
                'revenue_collected': float(revenue_collected),
                'outstanding_receivables': float(outstanding_receivables),
                'total_procurement_value': float(total_po_value),
                'vendor_payments_made': float(vendor_payments_made),
                'outstanding_payables': float(outstanding_payables),
                'total_inventory_valuation': float(round(total_inventory_valuation, 2)),
                'low_stock_count': len(low_stock_materials),
                'total_raw_materials': raw_materials_count,
                'total_products': total_products,
                'active_boms': active_boms,
                'net_profit': float(estimated_profit)
            },
            'low_stock_alerts': [
                {
                    'id': rm.id,
                    'code': rm.code,
                    'name': rm.name,
                    'current_stock': float(rm.current_stock),
                    'reorder_level': float(rm.reorder_level),
                    'unit': rm.unit_of_measure,
                    'status': rm.stock_status
                }
                for rm in low_stock_materials
            ]
        })


class ChartAnalyticsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1. Order Status Breakdown
        status_counts = SalesOrder.objects.values('status').annotate(count=Count('id'))
        status_dict = {item['status']: item['count'] for item in status_counts}
        status_labels = [c[1] for c in SalesOrder.STATUS_CHOICES]
        status_data = [status_dict.get(c[0], 0) for c in SalesOrder.STATUS_CHOICES]

        # 2. Material Stock by Category
        categories = RawMaterial.CATEGORY_CHOICES
        cat_labels = [c[1] for c in categories]
        cat_valuation = []
        for c in categories:
            val = sum(
                rm.current_stock * rm.standard_cost
                for rm in RawMaterial.objects.filter(category=c[0])
            )
            cat_valuation.append(float(round(val, 2)))

        # 3. Monthly Revenue Trend (Last 6 Months simulation or actuals)
        months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        sales_trend = [245000, 310000, 420000, 380000, 560000, 490000, 680000]
        procurement_trend = [140000, 180000, 260000, 220000, 310000, 290000, 380000]

        # 4. Top Selling Products
        top_items = (
            SalesOrderItem.objects.values('product__name', 'product__product_code')
            .annotate(total_qty=Sum('quantity'), total_rev=Sum('line_total'))
            .order_by('-total_rev')[:5]
        )

        return Response({
            'order_status_chart': {
                'labels': status_labels,
                'data': status_data
            },
            'category_inventory_chart': {
                'labels': cat_labels,
                'data': cat_valuation
            },
            'monthly_trend_chart': {
                'months': months,
                'sales': sales_trend,
                'procurement': procurement_trend
            },
            'top_products': list(top_items)
        })


class ReportsExportView(APIView):
    """Generates structured CSV formatted content for reports"""
    permission_classes = [AllowAny]

    def get(self, request):
        report_type = request.query_params.get('type', 'orders')
        import csv
        import io
        from django.http import HttpResponse

        output = io.StringIO()
        writer = csv.writer(output)

        if report_type == 'orders':
            writer.writerow(['Order #', 'Customer', 'Date', 'Delivery Due', 'Priority', 'Status', 'Total (INR)'])
            for o in SalesOrder.objects.all():
                writer.writerow([o.order_number, o.customer.company_name, o.order_date, o.delivery_due_date, o.priority, o.status, o.grand_total])
        elif report_type == 'materials':
            writer.writerow(['Material Code', 'Name', 'Category', 'Unit', 'Unit Cost', 'Current Stock', 'Reorder Level', 'Stock Valuation'])
            for rm in RawMaterial.objects.all():
                writer.writerow([rm.code, rm.name, rm.category, rm.unit_of_measure, rm.standard_cost, rm.current_stock, rm.reorder_level, rm.current_stock * rm.standard_cost])
        elif report_type == 'invoices':
            writer.writerow(['Invoice #', 'Customer', 'Date', 'Due Date', 'Status', 'Grand Total', 'Paid', 'Due'])
            for inv in Invoice.objects.all():
                writer.writerow([inv.invoice_number, inv.customer.company_name, inv.invoice_date, inv.due_date, inv.status, inv.grand_total, inv.amount_paid, inv.amount_due])
        elif report_type == 'procurement':
            writer.writerow(['PO #', 'Vendor', 'Order Date', 'Expected Date', 'Status', 'Total Amount'])
            for po in PurchaseOrder.objects.all():
                writer.writerow([po.po_number, po.vendor.company_name, po.order_date, po.expected_delivery_date, po.status, po.total_amount])

        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="ordercraft_{report_type}_report.csv"'
        return response
