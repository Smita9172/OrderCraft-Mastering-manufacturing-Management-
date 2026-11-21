"""
URL configuration for OrderCraft: Mastering Manufacturing Management ERP.
College Major Project.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    # Django Admin Portal
    path('admin/', admin.site.urls),

    # 7 Core Manufacturing REST API Modules
    path('api/accounts/', include('apps.accounts.urls')),        # Module 7: User Management & RBAC
    path('api/orders/', include('apps.orders.urls')),            # Module 1: Order Booking & Customers
    path('api/bom/', include('apps.bom.urls')),                  # Module 2: Bill of Material & Products
    path('api/procurement/', include('apps.procurement.urls')),  # Module 3: Purchase Orders & Vendors
    path('api/invoices/', include('apps.invoices.urls')),        # Module 4: Invoice Generation & Tax
    path('api/payments/', include('apps.payments.urls')),        # Module 5: Payments & Reconciliation
    path('api/analytics/', include('apps.analytics.urls')),      # Module 6: Reports & Analytics

    # Core Pages
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', ensure_csrf_cookie(TemplateView.as_view(template_name='login.html')), name='login'),
    path('register/', ensure_csrf_cookie(TemplateView.as_view(template_name='register.html')), name='register'),
    path('app/', login_required(TemplateView.as_view(template_name='app.html')), name='app-dashboard'),
    path('dashboard/', login_required(TemplateView.as_view(template_name='app.html')), name='dashboard-alt'),
]

# Static files handling for frontend CSS/JS/Assets
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.FRONTEND_DIR)
    urlpatterns += [
        re_path(r'^(?P<path>.*)$', serve, {'document_root': settings.FRONTEND_DIR}),
    ]
