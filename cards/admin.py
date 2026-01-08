from django.contrib import admin
from .models import GiftCardNames, GiftCardStore

admin.site.register(GiftCardStore)
admin.site.register(GiftCardNames)

# Register your models here.
