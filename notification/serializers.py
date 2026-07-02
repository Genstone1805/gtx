from rest_framework import serializers
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from .models import (
    Notification,
    NotificationEvent,
    PushNotificationSubscriber,
    PushNotificationLog,
)


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification model."""

    notification_type_display = serializers.CharField(
        source="get_notification_type_display", read_only=True
    )
    priority_display = serializers.CharField(
        source="get_priority_display", read_only=True
    )
    created_at_formatted = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "notification_type",
            "notification_type_display",
            "title",
            "message",
            "priority",
            "priority_display",
            "is_read",
            "created_at",
            "created_at_formatted",
            "read_at",
            "object_id",
            "content_type",
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_created_at_formatted(self, obj) -> str:
        return obj.created_at.strftime("%Y-%m-%d %H:%M")


class NotificationMarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read."""

    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of notification IDs to mark as read. If not provided, marks all as read.",
    )


class NotificationEventSerializer(serializers.ModelSerializer):
    """Serializer for notification event model (admin only)."""

    event_type_display = serializers.SerializerMethodField()
    channel_display = serializers.CharField(
        source="get_channel_display", read_only=True
    )
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = NotificationEvent
        fields = [
            "id",
            "user",
            "user_email",
            "event_type",
            "event_type_display",
            "title",
            "message",
            "channel",
            "channel_display",
            "status",
            "status_display",
            "error_message",
            "created_at",
            "sent_at",
            "metadata",
        ]
        read_only_fields = fields

    @extend_schema_field(OpenApiTypes.STR)
    def get_event_type_display(self, obj) -> str:
        return obj.event_type.replace("_", " ").title()


class PushNotificationSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushNotificationSubscriber
        fields = ["token", "platform", "device_id"]


class PushNotificationLogSerializer(serializers.ModelSerializer):
    """Full debug record of a single push attempt."""

    user_email = serializers.EmailField(source="user.email", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    trigger_display = serializers.CharField(source="get_trigger_display", read_only=True)

    class Meta:
        model = PushNotificationLog
        fields = [
            "id",
            "user",
            "user_email",
            "trigger",
            "trigger_display",
            "status",
            "status_display",
            "title",
            "body",
            "attempted",
            "sent",
            "failed",
            "deactivated",
            "tokens",
            "request_payload",
            "response",
            "errors",
            "created_at",
        ]
        read_only_fields = fields


class PushNotificationTestSerializer(serializers.Serializer):
    """Input for the admin push-debug endpoint."""

    user_id = serializers.IntegerField(
        required=False,
        help_text="Target user id. Defaults to the requesting admin's own account.",
    )
    title = serializers.CharField(
        required=False, default="Test Push Notification", max_length=255
    )
    body = serializers.CharField(
        required=False, default="This is a test push notification from the backend.",
    )
    payload = serializers.DictField(
        required=False, default=dict, help_text="Optional JSON data payload sent with the push."
    )
