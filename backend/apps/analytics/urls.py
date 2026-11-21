from django.urls import path
from .views import DashboardOverviewView, ChartAnalyticsView, ReportsExportView

urlpatterns = [
    path('dashboard/', DashboardOverviewView.as_view(), name='analytics-dashboard'),
    path('charts/', ChartAnalyticsView.as_view(), name='analytics-charts'),
    path('export/', ReportsExportView.as_view(), name='analytics-export'),
]
