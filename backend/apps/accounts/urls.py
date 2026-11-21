from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomUserViewSet, AuditLogViewSet, LoginView, LogoutView, CurrentUserView, RegisterView

router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'audit-logs', AuditLogViewSet, basename='auditlog')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='api-login'),
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/me/', CurrentUserView.as_view(), name='api-current-user'),
    path('', include(router.urls)),
]
