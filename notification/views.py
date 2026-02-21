from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
from django.utils import timezone

from .models import Notification, NotificationEvent
from .services import NotificationService
from .serializers import (
    NotificationSerializer,
    NotificationMarkAsReadSerializer,
    NotificationEventSerializer,
)


class NotificationListView(ListAPIView):
    """List all notifications for the authenticated user."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # Filter by unread if requested
        unread_only = self.request.query_params.get('unread_only', 'false').lower() == 'true'
        if unread_only:
            queryset = queryset.filter(is_read=False)
        
        # Filter by notification type if provided
        notification_type = self.request.query_params.get('type')
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)
        
        return queryset[:50]  # Limit to 50 most recent


class NotificationDetailView(RetrieveAPIView):
    """Get a specific notification detail."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    queryset = Notification.objects.all()

    def get_object(self):
        obj = super().get_object()
        # Ensure user can only access their own notifications
        if obj.user != self.request.user:
            self.permission_denied(self.request)
        return obj


class NotificationMarkAsReadView(APIView):
    """Mark one or all notifications as read."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        serializer = NotificationMarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get('ids', [])

        if notification_ids:
            # Mark specific notifications as read
            updated = Notification.objects.filter(
                user=user,
                id__in=notification_ids,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
        else:
            # Mark all as read
            updated = NotificationService.mark_all_as_read(user)

        return Response({
            'detail': f'{updated} notification(s) marked as read.',
            'marked_count': updated,
        })


class NotificationMarkAllAsReadView(APIView):
    """Mark all notifications as read for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        updated = NotificationService.mark_all_as_read(user)
        
        return Response({
            'detail': 'All notifications marked as read.',
            'marked_count': updated,
        })


class NotificationUnreadCountView(APIView):
    """Get count of unread notifications."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return Response({'unread_count': count})


# Admin Views

class AdminNotificationEventListView(ListAPIView):
    """List all notification events (admin only)."""
    permission_classes = [IsAdminUser]
    serializer_class = NotificationEventSerializer

    def get_queryset(self):
        queryset = NotificationEvent.objects.all().order_by('-created_at')
        
        # Filter by status if provided
        status_param = self.request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by user if provided
        user_param = self.request.query_params.get('user_id')
        if user_param:
            queryset = queryset.filter(user_id=user_param)
        
        # Filter by channel if provided
        channel_param = self.request.query_params.get('channel')
        if channel_param:
            queryset = queryset.filter(channel=channel_param)
        
        return queryset[:100]  # Limit to 100 most recent


class AdminNotificationStatsView(APIView):
    """Get notification statistics (admin only)."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.db.models import Count, Q
        
        # Overall stats
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()
        
        # Event stats
        total_events = NotificationEvent.objects.count()
        sent_events = NotificationEvent.objects.filter(status='sent').count()
        failed_events = NotificationEvent.objects.filter(status='failed').count()
        
        # By type
        notifications_by_type = Notification.objects.values('notification_type').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        return Response({
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            'total_events': total_events,
            'sent_events': sent_events,
            'failed_events': failed_events,
            'success_rate': f'{(sent_events / total_events * 100) if total_events > 0 else 0:.2f}%',
            'notifications_by_type': list(notifications_by_type),
        })
