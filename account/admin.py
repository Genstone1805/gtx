from django.contrib import admin
from .models import (
    UserProfile,
    Level2Credentials,
    Level3Credentials,
    EmailVerificationCode,
    PasswordResetCode,
    BankAccountDetails,
    ReferralCommission,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'full_name', 'level', 'is_verified', 'phone_number',
        'referral_code', 'referred_by', 'referral_count', 'withdrawable_balance',
        'created_at',
    )
    search_fields = ('email', 'full_name', 'referral_code', 'referred_by__email')
    list_filter = ('level', 'is_verified', 'status', 'created_at')
    readonly_fields = ('referral_code', 'referral_count', 'created_at', 'last_login')

    def referral_count(self, obj):
        return obj.referrals.count()


@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'referrer', 'referred_user', 'qualifying_transaction',
        'amount', 'percentage', 'status', 'paid_at', 'created_at',
    )
    search_fields = ('referrer__email', 'referred_user__email')
    list_filter = ('status', 'created_at', 'paid_at')
    readonly_fields = ('created_at',)


admin.site.register(Level2Credentials)
admin.site.register(Level3Credentials)
admin.site.register(EmailVerificationCode)
admin.site.register(PasswordResetCode)
admin.site.register(BankAccountDetails)
