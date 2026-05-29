from django.contrib import admin
from .models import Notification, NotificationEvent, PushNotificationToken

admin.site.register(Notification)
admin.site.register(NotificationEvent)
admin.site.register(PushNotificationToken)
