from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VendorViewSet, PurchaseOrderViewSet, GoodsReceiptNoteViewSet, VendorCommunicationViewSet

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchaseorder')
router.register(r'grns', GoodsReceiptNoteViewSet, basename='grn')
router.register(r'communications', VendorCommunicationViewSet, basename='vendorcommunication')

urlpatterns = [
    path('', include(router.urls)),
]
