from django.contrib import admin
from withdrawal.services import WithdrawalLimitService
from .models import Withdrawal, WithdrawalAuditLog, WithdrawalLimitUsage


@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'amount', 'status', 'verification_level',
        'created_at', 'processed_at',
    )
    search_fields = ('user__email', 'transaction_reference', 'account_number')
    list_filter = ('status', 'created_at', 'processed_at')

    def verification_level(self, obj):
        level = WithdrawalLimitService.get_user_level(obj.user)
        return f"Level {level}" if level else "Unverified"


admin.site.register(WithdrawalAuditLog)


@admin.register(WithdrawalLimitUsage)
class WithdrawalLimitUsageAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'verification_level', 'total_amount', 'total_count', 'updated_at')
    search_fields = ('user__email',)
    list_filter = ('date',)

    def verification_level(self, obj):
        level = WithdrawalLimitService.get_user_level(obj.user)
        return f"Level {level}" if level else "Unverified"
