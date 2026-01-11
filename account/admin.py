from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile


class CustomUserAdmin(UserAdmin):
    model = UserProfile
    list_display = ('email', 'full_name', 'is_verified', 'is_staff', 'is_active')
    list_filter = ('is_verified', 'is_staff', 'is_active', 'level', 'status')
    search_fields = ('email', 'full_name')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'phone_number', 'dp')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        ('Account Status', {'fields': ('level', 'status', 'disabled')}),
        ('Important dates', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'full_name', 'is_staff', 'is_active', 'is_verified'),
        }),
    )

    readonly_fields = ('created_at', 'last_login')


admin.site.register(UserProfile, CustomUserAdmin)
