from django.urls import path
from .views import (
    NotificationListView,
    NotificationDetailView,
    NotificationMarkAsReadView,
    NotificationMarkAllAsReadView,
    NotificationUnreadCountView,
    AdminNotificationEventListView,
    AdminNotificationStatsView,
)

app_name = 'notification'

urlpatterns = [
    # User endpoints
    path('', NotificationListView.as_view(), name='notification-list'),
    path('unread-count/', NotificationUnreadCountView.as_view(), name='notification-unread-count'),
    path('mark-as-read/', NotificationMarkAsReadView.as_view(), name='notification-mark-as-read'),
    path('mark-all-as-read/', NotificationMarkAllAsReadView.as_view(), name='notification-mark-all-as-read'),
    path('<int:pk>/', NotificationDetailView.as_view(), name='notification-detail'),

    # Admin endpoints
    path('admin/events/', AdminNotificationEventListView.as_view(), name='admin-notification-events'),
    path('admin/stats/', AdminNotificationStatsView.as_view(), name='admin-notification-stats'),
]
