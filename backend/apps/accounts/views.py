from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from .models import CustomUser, AuditLog
from .serializers import CustomUserSerializer, AuditLogSerializer

User = get_user_model()


def record_audit(user, action, module, description, record_id=None, request=None):
    """Helper to record audit trail entries across any module"""
    ip = None
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

    user_name = "System"
    actual_user = None
    if user and user.is_authenticated:
        actual_user = user
        user_name = user.get_full_name() or user.username

    AuditLog.objects.create(
        user=actual_user,
        user_name=user_name,
        action=action,
        module=module,
        record_id=str(record_id) if record_id else '',
        description=description,
        ip_address=ip
    )


class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        user = serializer.save()
        record_audit(
            self.request.user,
            'CREATE',
            'USERS',
            f"Created user account '{user.username}' with role '{user.get_role_display()}'",
            record_id=user.id,
            request=self.request
        )

    def perform_update(self, serializer):
        user = serializer.save()
        record_audit(
            self.request.user,
            'UPDATE',
            'USERS',
            f"Updated user account '{user.username}'",
            record_id=user.id,
            request=self.request
        )


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [AllowAny]


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')
        remember_me = bool(request.data.get('remember_me', False))

        if not username or not password:
            return Response({'error': 'Please provide both username/email and password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Allow logging in with either username or email address
        if '@' in username:
            matched = CustomUser.objects.filter(email__iexact=username).first()
            if matched:
                username = matched.username

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if not remember_me:
                request.session.set_expiry(0)
            record_audit(
                user,
                'LOGIN',
                'USERS',
                f"User '{user.username}' logged into OrderCraft ERP",
                record_id=user.id,
                request=request
            )
            serializer = CustomUserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': serializer.data
            })
        return Response({'error': 'Invalid username/email or password.'}, status=status.HTTP_401_UNAUTHORIZED)


class RegisterView(APIView):
    """Create a regular OrderCraft account without exposing the user model."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not email or not password or not confirm_password:
            return Response(
                {'error': 'Email, password, and password confirmation are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Enter a valid email address.'}, status=status.HTTP_400_BAD_REQUEST)

        if password != confirm_password:
            return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email__iexact=email).exists():
            return Response({'error': 'An account with this email already exists. Please sign in.'}, status=status.HTTP_409_CONFLICT)

        # The configured Django password validators enforce the project policy.
        try:
            validate_password(password)
        except ValidationError as exc:
            return Response({'error': ' '.join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    role='ADMIN',
                    department='Manufacturing Operations',
                    designation='New Account',
                )
        except IntegrityError:
            # Covers a concurrent registration that wins the unique-email race.
            return Response({'error': 'An account with this email already exists. Please sign in.'}, status=status.HTTP_409_CONFLICT)

        record_audit(
            user,
            'CREATE',
            'USERS',
            f"Registered new OrderCraft account '{user.email}'",
            record_id=user.id,
            request=request,
        )
        return Response({'message': 'Account created successfully. Please sign in.'}, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.user.is_authenticated:
            record_audit(
                request.user,
                'LOGIN',
                'USERS',
                f"User '{request.user.username}' logged out",
                record_id=request.user.id,
                request=request
            )
            logout(request)
        return Response({'message': 'Logged out successfully'})


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            serializer = CustomUserSerializer(request.user)
            return Response(serializer.data)
        return Response({'error': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)
