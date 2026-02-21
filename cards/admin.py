from django.contrib import admin
from .models import GiftCardNames, GiftCardStore


@admin.register(GiftCardStore)
class GiftCardStoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'category', 'get_cards_count', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name']
    ordering = ['-created_at']
    list_per_page = 50

    def get_cards_count(self, obj):
        return obj.giftcardnames_set.count()
    get_cards_count.short_description = 'Cards Count'


@admin.register(GiftCardNames)
class GiftCardNamesAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'store', 'type', 'rate', 'created_at']
    list_filter = ['type', 'store', 'created_at']
    search_fields = ['name', 'store__name']
    ordering = ['-created_at']
    list_per_page = 50

    fieldsets = (
        ('Card Information', {
            'fields': ('name', 'store', 'type', 'rate')
        }),
    )
