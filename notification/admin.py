from django.contrib import admin
from .models import Notification, NotificationEvent, PushNotificationSubscriber

admin.site.register(Notification)
admin.site.register(NotificationEvent)
admin.site.register(PushNotificationSubscriber)
