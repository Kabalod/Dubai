from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from .models import User, Payment, PaymentEventAudit, OTPCode, UserReportHistory

User = get_user_model()


# Пользовательский UserAdmin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User Admin with additional fields."""

    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('subscription_type', 'subscription_expires')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'first_name', 'last_name')}),
    )


# OTP коды
@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    """Admin for OTP codes."""

    list_display = ('email', 'code', 'is_used', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('email', 'code')
    readonly_fields = ('created_at', 'updated_at')

    # Не позволяем редактировать коды
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Платежи
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin for payments."""

    list_display = ('id', 'user', 'stripe_charge_id', 'amount', 'currency', 'status', 'created_at')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('user__email', 'user__username', 'stripe_charge_id')
    readonly_fields = ('created_at', 'updated_at', 'stripe_charge_id')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'amount', 'currency', 'status')
        }),
        ('Stripe Integration', {
            'fields': ('stripe_charge_id', 'description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Stripe Webhook Events
@admin.register(PaymentEventAudit)
class PaymentEventAuditAdmin(admin.ModelAdmin):
    """Admin for Stripe webhook events."""

    list_display = ('id', 'provider', 'event_type', 'event_id', 'status', 'created_at')
    list_filter = ('provider', 'event_type', 'status', 'created_at')
    search_fields = ('event_id', 'event_type')
    readonly_fields = ('created_at', 'updated_at', 'payload')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Event Info', {
            'fields': ('provider', 'event_type', 'event_id', 'status')
        }),
        ('Related Data', {
            'fields': ('related_payment', 'payload'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# История отчетов
@admin.register(UserReportHistory)
class UserReportHistoryAdmin(admin.ModelAdmin):
    """Admin for user report history."""

    list_display = ('id', 'user', 'report_type', 'generated_at', 'file_path')
    list_filter = ('report_type', 'generated_at')
    search_fields = ('user__email', 'user__username', 'report_type')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'generated_at'

    fieldsets = (
        ('Report Info', {
            'fields': ('user', 'report_type', 'parameters')
        }),
        ('File Info', {
            'fields': ('file_path', 'generated_at'),
            'classes': ('collapse',)
        }),
    )
