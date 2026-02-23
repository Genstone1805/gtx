from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Level2Credentials, Level3Credentials, EmailVerificationCode, PasswordResetCode, BankAccountDetails


class CustomUserAdmin(UserAdmin):
    model = UserProfile
    list_display = ('email', 'full_name', 'is_verified', 'is_staff', 'is_active', 'level', 'status')
    list_filter = ('is_verified', 'is_staff', 'is_active', 'level', 'status')
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'bank_details', 'dp', 'has_pin', 'transaction_pin')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Account Status', {'fields': ('level', 'status', 'disabled')}),
        ('Balances', {'fields': ('pending_balance', 'withdrawable_balance', 'transaction_limit')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'is_staff', 'is_active', 'is_verified'),
        }),
    )

    readonly_fields = ('created_at', 'last_login', 'pending_balance', 'withdrawable_balance')


@admin.register(UserProfile)
class CustomUserAdminRegistered(CustomUserAdmin):
    pass


@admin.register(Level2Credentials)
class Level2CredentialsAdmin(admin.ModelAdmin):
    list_display = ['id', 'nin', 'status', 'approved', 'get_user_email', 'created_at']
    list_filter = ['status', 'approved', 'created_at']
    search_fields = ['nin', 'user__email']
    readonly_fields = ['nin', 'nin_image', 'status', 'approved', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def get_user_email(self, obj):
        from account.models import UserProfile
        user = UserProfile.objects.filter(level2_credentials=obj).first()
        return user.email if user else '-'
    get_user_email.short_description = 'User Email'


@admin.register(Level3Credentials)
class Level3CredentialsAdmin(admin.ModelAdmin):
    list_display = ['id', 'house_address_1', 'city', 'state', 'status', 'approved', 'get_user_email', 'created_at']
    list_filter = ['status', 'approved', 'created_at']
    search_fields = ['city', 'state', 'user__email']
    readonly_fields = [
        'house_address_1', 'house_address_2', 'nearest_bus_stop',
        'city', 'state', 'country', 'proof_of_address_image',
        'face_verification_image', 'status', 'approved', 'created_at'
    ]
    ordering = ['-created_at']
    list_per_page = 50

    def get_user_email(self, obj):
        from account.models import UserProfile
        user = UserProfile.objects.filter(level3_credentials=obj).first()
        return user.email if user else '-'
    get_user_email.short_description = 'User Email'


@admin.register(EmailVerificationCode)
class EmailVerificationCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'code', 'created_at', 'is_expired']
    list_filter = ['created_at']
    search_fields = ['user__email', 'code']
    readonly_fields = ['user', 'code', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'code', 'created_at', 'is_expired']
    list_filter = ['created_at']
    search_fields = ['user__email', 'code']
    readonly_fields = ['user', 'code', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'


@admin.register(BankAccountDetails)
class BankAccountDetailsAdmin(admin.ModelAdmin):
    list_display = ['id', 'bank_name', 'account_number', 'account_name', 'created_at']
    search_fields = ['bank_name', 'account_number', 'account_name']
    ordering = ['-created_at']
