from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    In-app notification model for user notifications.
    """

    NOTIFICATION_TYPES = [
        ("order_created", "Order Created"),
        ("order_approved", "Order Approved"),
        ("order_rejected", "Order Rejected"),
        ("order_assigned", "Order Assigned"),
        ("order_completed", "Order Completed"),
        ("withdrawal_created", "Withdrawal Requested"),
        ("withdrawal_approved", "Withdrawal Approved"),
        ("withdrawal_rejected", "Withdrawal Rejected"),
        ("kyc_approved", "KYC Approved"),
        ("kyc_rejected", "KYC Rejected"),
        ("balance_updated", "Balance Updated"),
        ("general", "General"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(
        max_length=10, choices=PRIORITY_CHOICES, default="medium"
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Optional reference to related objects
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["user", "-created_at"], name="notification_user_created_idx"
            ),
            models.Index(fields=["user", "is_read"], name="notification_user_read_idx"),
        ]

    def mark_as_read(self):
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.notification_type} - {self.user.email}"


class NotificationEvent(models.Model):
    """
    Event log for tracking all notification events (for auditing and debugging).
    """

    EVENT_STATUS = [
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
    ]

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("in_app", "In-App"),
        ("both", "Both"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notification_events",
    )
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=10, choices=EVENT_STATUS, default="pending")
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_type} - {self.user.email} - {self.status}"


class PushNotificationSubscriber(models.Model):
    PLATFORM_CHOICES = (
        ("ios", "iOS"),
        ("android", "Android"),
        ("web", "Web"),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="push_tokens"
    )

    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)

    device_id = models.CharField(max_length=120, null=True, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PushNotificationLog(models.Model):
    """
    Debug log for every Expo push attempt.

    Captures the full picture of a push send - the request that went to Expo,
    the response that came back, per-token results, any errors, and the final
    status - so push behaviour can be inspected and debugged from the admin.
    """

    STATUS_CHOICES = [
        ("success", "Success"),          # all targeted tokens delivered
        ("partial", "Partial"),          # some delivered, some failed
        ("failed", "Failed"),            # nothing delivered
        ("no_tokens", "No Tokens"),      # user had no active tokens
        ("skipped", "Skipped"),          # send was not attempted
    ]

    TRIGGER_CHOICES = [
        ("notification", "Notification"),  # fired alongside an in-app notification
        ("test", "Test Endpoint"),         # fired manually from the debug endpoint
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="push_logs",
    )
    trigger = models.CharField(
        max_length=20, choices=TRIGGER_CHOICES, default="notification"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="skipped"
    )

    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)

    # Counts
    attempted = models.PositiveIntegerField(default=0)
    sent = models.PositiveIntegerField(default=0)
    failed = models.PositiveIntegerField(default=0)
    deactivated = models.PositiveIntegerField(default=0)

    # Full debug payloads (all JSON-serializable)
    tokens = models.JSONField(default=list, blank=True)            # tokens targeted
    request_payload = models.JSONField(default=list, blank=True)   # what was sent to Expo
    response = models.JSONField(default=list, blank=True)          # per-token Expo response
    errors = models.JSONField(default=list, blank=True)            # collected errors

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="pushlog_created_idx"),
            models.Index(fields=["status"], name="pushlog_status_idx"),
        ]

    def __str__(self):
        who = self.user.email if self.user else "unknown"
        return f"push[{self.status}] -> {who} ({self.sent}/{self.attempted})"
