from django.contrib import admin
from .models import Notification, NotificationEvent


admin.site.register(Notification)
admin.site.register(NotificationEvent)
