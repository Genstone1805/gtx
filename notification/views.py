from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, CreateAPIView
from rest_framework.response import Response
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer

from .models import (
    Notification,
    NotificationEvent,
    PushNotificationSubscriber,
    PushNotificationLog,
)
from .services import NotificationService, PushNotificationSender
from .serializers import (
    NotificationSerializer,
    NotificationMarkAsReadSerializer,
    NotificationEventSerializer,
    PushNotificationSubscriberSerializer,
    PushNotificationLogSerializer,
    PushNotificationTestSerializer,
)


class PushNotificationSubscriberView(CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PushNotificationSubscriberSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        platform = serializer.validated_data["platform"]
        device_id = serializer.validated_data.get("device_id", "")

        # A device sends a stable Expo token; re-registering reassigns it to the
        # current user and reactivates it (handles account switch / re-login).
        obj, created = PushNotificationSubscriber.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "platform": platform,
                "device_id": device_id,
                "is_active": True,
            },
        )

        return Response(
            {
                "created": created,
                "message": "token stored/updated",
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class NotificationListView(ListAPIView):
    """List all notifications for the authenticated user."""

    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = Notification.objects.filter(user=user)

        # Filter by unread if requested
        unread_only = (
            self.request.query_params.get("unread_only", "false").lower() == "true"
        )
        if unread_only:
            queryset = queryset.filter(is_read=False)

        # Filter by notification type if provided
        notification_type = self.request.query_params.get("type")
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
    serializer_class = NotificationMarkAsReadSerializer

    @extend_schema(
        request=NotificationMarkAsReadSerializer,
        responses={
            200: inline_serializer(
                name="NotificationMarkAsReadResponse",
                fields={
                    "detail": serializers.CharField(),
                    "marked_count": serializers.IntegerField(),
                },
            )
        },
    )
    def post(self, request):
        user = request.user
        serializer = NotificationMarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        notification_ids = serializer.validated_data.get("ids", [])

        if notification_ids:
            # Mark specific notifications as read
            updated = Notification.objects.filter(
                user=user, id__in=notification_ids, is_read=False
            ).update(is_read=True, read_at=timezone.now())
        else:
            # Mark all as read
            updated = NotificationService.mark_all_as_read(user)

        return Response(
            {
                "detail": f"{updated} notification(s) marked as read.",
                "marked_count": updated,
            }
        )


class NotificationMarkAllAsReadView(APIView):
    """Mark all notifications as read for the authenticated user."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="NotificationMarkAllAsReadResponse",
                fields={
                    "detail": serializers.CharField(),
                    "marked_count": serializers.IntegerField(),
                },
            )
        },
    )
    def post(self, request):
        user = request.user
        updated = NotificationService.mark_all_as_read(user)

        return Response(
            {
                "detail": "All notifications marked as read.",
                "marked_count": updated,
            }
        )


class NotificationUnreadCountView(APIView):
    """Get count of unread notifications."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="NotificationUnreadCountResponse",
                fields={"unread_count": serializers.IntegerField()},
            )
        },
    )
    def get(self, request):
        count = NotificationService.get_unread_count(request.user)
        return Response({"unread_count": count})


# Admin Views


class AdminNotificationEventListView(ListAPIView):
    """List all notification events (admin only)."""

    permission_classes = [IsAdminUser]
    serializer_class = NotificationEventSerializer

    def get_queryset(self):
        queryset = NotificationEvent.objects.all().order_by("-created_at")

        # Filter by status if provided
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        # Filter by user if provided
        user_param = self.request.query_params.get("user_id")
        if user_param:
            queryset = queryset.filter(user_id=user_param)

        # Filter by channel if provided
        channel_param = self.request.query_params.get("channel")
        if channel_param:
            queryset = queryset.filter(channel=channel_param)

        return queryset[:100]  # Limit to 100 most recent


class AdminNotificationStatsView(APIView):
    """Get notification statistics (admin only)."""

    permission_classes = [IsAdminUser]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="AdminNotificationStatsResponse",
                fields={
                    "total_notifications": serializers.IntegerField(),
                    "unread_notifications": serializers.IntegerField(),
                    "total_events": serializers.IntegerField(),
                    "sent_events": serializers.IntegerField(),
                    "failed_events": serializers.IntegerField(),
                    "success_rate": serializers.CharField(),
                    "notifications_by_type": serializers.ListField(
                        child=serializers.DictField()
                    ),
                },
            )
        },
    )
    def get(self, request):
        from django.db.models import Count, Q

        # Overall stats
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()

        # Event stats
        total_events = NotificationEvent.objects.count()
        sent_events = NotificationEvent.objects.filter(status="sent").count()
        failed_events = NotificationEvent.objects.filter(status="failed").count()

        # By type
        notifications_by_type = (
            Notification.objects.values("notification_type")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )

        return Response(
            {
                "total_notifications": total_notifications,
                "unread_notifications": unread_notifications,
                "total_events": total_events,
                "sent_events": sent_events,
                "failed_events": failed_events,
                "success_rate": f"{(sent_events / total_events * 100) if total_events > 0 else 0:.2f}%",
                "notifications_by_type": list(notifications_by_type),
            }
        )


class AdminPushNotificationLogListView(ListAPIView):
    """
    List push notification debug logs (admin only).

    Each entry captures the request sent to Expo, the response received,
    per-token results, collected errors and the final status.

    Query params:
      - status: success | partial | failed | no_tokens | skipped
      - trigger: notification | test
      - user_id: filter by target user
    """

    permission_classes = [IsAdminUser]
    serializer_class = PushNotificationLogSerializer

    def get_queryset(self):
        queryset = PushNotificationLog.objects.all().order_by("-created_at")

        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        trigger_param = self.request.query_params.get("trigger")
        if trigger_param:
            queryset = queryset.filter(trigger=trigger_param)

        user_param = self.request.query_params.get("user_id")
        if user_param:
            queryset = queryset.filter(user_id=user_param)

        return queryset[:100]  # Limit to 100 most recent


class AdminPushNotificationTestView(APIView):
    """
    Fire a test push notification and return the full push behaviour (admin only).

    Sends to the active Expo tokens of the target user (defaults to the
    requesting admin), then returns the exact request/response/errors/status -
    the same detail that is persisted to PushNotificationLog and visible in the
    Django admin.
    """

    permission_classes = [IsAdminUser]
    serializer_class = PushNotificationTestSerializer

    @extend_schema(
        request=PushNotificationTestSerializer,
        responses={
            200: inline_serializer(
                name="AdminPushNotificationTestResponse",
                fields={
                    "target_user_id": serializers.IntegerField(),
                    "target_user_email": serializers.CharField(),
                    "active_tokens": serializers.IntegerField(),
                    "result": serializers.DictField(),
                    "log": PushNotificationLogSerializer(),
                },
            )
        },
    )
    def post(self, request):
        from django.contrib.auth import get_user_model

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        User = get_user_model()
        user_id = validated.get("user_id")
        if user_id:
            try:
                target_user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                raise ValidationError({"user_id": "No user with this id."})
        else:
            target_user = request.user

        active_tokens = PushNotificationSubscriber.objects.filter(
            user=target_user, is_active=True
        ).count()

        result = PushNotificationSender.send(
            user=target_user,
            title=validated.get("title") or "Test Push Notification",
            body=validated.get("body") or "This is a test push notification from the backend.",
            data={"type": "test", **(validated.get("payload") or {})},
            trigger="test",
        )

        log = None
        log_id = result.get("log_id")
        if log_id:
            log = PushNotificationLog.objects.filter(pk=log_id).first()

        return Response(
            {
                "target_user_id": target_user.id,
                "target_user_email": getattr(target_user, "email", None),
                "active_tokens": active_tokens,
                "result": result,
                "log": PushNotificationLogSerializer(log).data if log else None,
            }
        )
