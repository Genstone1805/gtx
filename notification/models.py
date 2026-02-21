from django.db import models
from django.conf import settings
from django.utils import timezone


class Notification(models.Model):
    """
    In-app notification model for user notifications.
    """
    NOTIFICATION_TYPES = [
        ('order_created', 'Order Created'),
        ('order_approved', 'Order Approved'),
        ('order_rejected', 'Order Rejected'),
        ('order_assigned', 'Order Assigned'),
        ('order_completed', 'Order Completed'),
        ('withdrawal_created', 'Withdrawal Requested'),
        ('withdrawal_approved', 'Withdrawal Approved'),
        ('withdrawal_rejected', 'Withdrawal Rejected'),
        ('kyc_approved', 'KYC Approved'),
        ('kyc_rejected', 'KYC Rejected'),
        ('balance_updated', 'Balance Updated'),
        ('general', 'General'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    # Optional reference to related objects
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_type = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='notification_user_created_idx'),
            models.Index(fields=['user', 'is_read'], name='notification_user_read_idx'),
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
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    CHANNEL_CHOICES = [
        ('email', 'Email'),
        ('in_app', 'In-App'),
        ('both', 'Both'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_events'
    )
    event_type = models.CharField(max_length=50)
    title = models.CharField(max_length=255)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=CHANNEL_CHOICES)
    status = models.CharField(max_length=10, choices=EVENT_STATUS, default='pending')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.event_type} - {self.user.email} - {self.status}"
