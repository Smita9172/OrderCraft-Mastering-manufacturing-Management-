from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RawMaterialViewSet, ProductViewSet, BillOfMaterialViewSet, BOMItemViewSet, BOMExplosionView

router = DefaultRouter()
router.register(r'raw-materials', RawMaterialViewSet, basename='rawmaterial')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'boms', BillOfMaterialViewSet, basename='bom')
router.register(r'bom-items', BOMItemViewSet, basename='bomitem')

urlpatterns = [
    path('explode/', BOMExplosionView.as_view(), name='bom-explode'),
    path('', include(router.urls)),
]
