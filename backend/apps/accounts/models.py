from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    # Email is the public identifier used by registration and login.
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('ADMIN', 'Plant Administrator / Management'),
        ('SALES', 'Sales & Order Booking Officer'),
        ('PRODUCTION', 'Production & BOM Manager'),
        ('PROCUREMENT', 'Procurement & Purchase Officer'),
        ('FINANCE', 'Finance & Billing Specialist'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='ADMIN',
        help_text="Role determining access level within OrderCraft ERP"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    department = models.CharField(max_length=100, default='Manufacturing Operations')
    designation = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        full_name = self.get_full_name()
        display = full_name if full_name else self.username
        return f"{display} ({self.get_role_display()})"

    @property
    def is_admin_role(self):
        return self.role == 'ADMIN' or self.is_superuser


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Created'),
        ('UPDATE', 'Updated'),
        ('DELETE', 'Deleted'),
        ('STATUS_CHANGE', 'Status Changed'),
        ('LOGIN', 'User Logged In'),
        ('EXPLODE_BOM', 'BOM Explosion Run'),
        ('RECEIVE_GOODS', 'Goods Received'),
        ('RECONCILE', 'Payment Reconciled'),
    ]

    MODULE_CHOICES = [
        ('ORDERS', 'Order Booking'),
        ('BOM', 'Bill of Materials'),
        ('PROCUREMENT', 'Procurement & PO'),
        ('INVOICES', 'Invoice Generation'),
        ('PAYMENTS', 'Payment & Receipts'),
        ('ANALYTICS', 'Analytics & Reports'),
        ('USERS', 'User Management'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_name = models.CharField(max_length=150, blank=True, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    module = models.CharField(max_length=20, choices=MODULE_CHOICES)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M')}] {self.user_name or 'System'} - {self.action} on {self.module}: {self.description[:50]}"
