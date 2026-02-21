from django.contrib import admin
from .models import Withdrawal, WithdrawalAuditLog


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'amount', 'status',
        'processed_by', 'processed_at', 'created_at'
    ]
    list_filter = ['status', 'created_at', 'processed_at']
    search_fields = ['user__email', 'user__full_name', 'transaction_reference']
    readonly_fields = [
        'user', 'amount',
        'bank_name', 'account_name', 'account_number',
        'status', 'processed_by', 'processed_at', 'rejection_reason',
        'admin_notes', 'transaction_reference', 'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Withdrawal Information', {
            'fields': ('user', 'amount', 'status')
        }),
        ('Bank Account Details', {
            'fields': ('bank_name', 'account_name', 'account_number')
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
