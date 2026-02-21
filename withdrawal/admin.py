from django.contrib import admin
from .models import Withdrawal, WithdrawalAuditLog


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'amount', 'payment_method', 'status',
        'processed_by', 'processed_at', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'created_at', 'processed_at']
    search_fields = ['user__email', 'user__full_name', 'transaction_reference']
    readonly_fields = [
        'user', 'amount', 'payment_method',
        'bank_name', 'account_name', 'account_number',
        'mobile_money_number', 'mobile_money_provider',
        'crypto_address', 'crypto_network',
        'status', 'processed_by', 'processed_at', 'rejection_reason',
        'admin_notes', 'transaction_reference', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Withdrawal Information', {
            'fields': ('user', 'amount', 'payment_method', 'status')
        }),
        ('Bank Transfer Details', {
            'fields': ('bank_name', 'account_name', 'account_number'),
            'classes': ('collapse',)
        }),
        ('Mobile Money Details', {
            'fields': ('mobile_money_number', 'mobile_money_provider'),
            'classes': ('collapse',)
        }),
        ('Crypto Details', {
            'fields': ('crypto_address', 'crypto_network'),
            'classes': ('collapse',)
        }),
        ('Processing Information', {
            'fields': ('processed_by', 'processed_at', 'rejection_reason', 'admin_notes', 'transaction_reference')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WithdrawalAuditLog)
class WithdrawalAuditLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'withdrawal', 'action', 'performed_by', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['withdrawal__id', 'performed_by__email']
    readonly_fields = ['withdrawal', 'action', 'performed_by', 'details', 
                       'previous_status', 'new_status', 'created_at']
    ordering = ['-created_at']
    list_per_page = 100
