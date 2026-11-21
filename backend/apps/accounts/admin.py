from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'department', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_active', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Manufacturing Role & Info', {'fields': ('role', 'phone', 'department', 'designation')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Manufacturing Role & Info', {'fields': ('role', 'phone', 'department', 'designation')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user_name', 'action', 'module', 'record_id', 'description')
    list_filter = ('action', 'module', 'timestamp')
    search_fields = ('description', 'user_name', 'record_id')
    readonly_fields = [f.name for f in AuditLog._meta.fields]
