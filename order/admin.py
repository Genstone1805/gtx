from django.contrib import admin
from .models import GiftCardOrder


@admin.register(GiftCardOrder)
class GiftCardOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'card', 'type', 'amount', 'status', 'created_at']
    list_filter = ['status', 'type', 'created_at']
    search_fields = ['user__email', 'user__full_name', 'card__name']
    readonly_fields = ['user', 'type', 'card', 'image', 'e_code_pin', 'amount', 'status', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'card', 'type', 'amount', 'status')
        }),
        ('Order Details', {
            'fields': ('image', 'e_code_pin')
        }),
    )
