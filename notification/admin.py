from django.contrib import admin
from .models import Notification, NotificationEvent


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'title', 'priority', 'is_read', 'created_at']
    list_filter = ['notification_type', 'priority', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['user', 'notification_type', 'title', 'message', 'priority', 
                       'object_id', 'content_type', 'created_at', 'read_at']
    ordering = ['-created_at']
    list_per_page = 50


@admin.register(NotificationEvent)
class NotificationEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'event_type', 'channel', 'status', 'created_at', 'sent_at']
    list_filter = ['event_type', 'channel', 'status', 'created_at']
    search_fields = ['user__email', 'title', 'message', 'error_message']
    readonly_fields = ['user', 'event_type', 'title', 'message', 'channel', 
                       'status', 'error_message', 'created_at', 'sent_at', 'metadata']
    ordering = ['-created_at']
    list_per_page = 50
