from unittest.mock import Mock, patch

from django.test import TestCase

from account.models import UserProfile
from notification.models import NotificationEvent, PushNotificationSubscriber
from notification.services import NotificationService


class NotificationServicePushTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            email="user@example.com",
            password="password123",
        )

    @patch("exponent_server_sdk.PushClient")
    def test_send_notification_sends_push_to_active_subscribers(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.user,
            token="ExponentPushToken[test-token]",
            platform="ios",
        )
        ticket = Mock()
        ticket.validate_response.return_value = None
        push_client.return_value.publish_multiple.return_value = [ticket]

        notification, event = NotificationService.send_notification(
            user=self.user,
            notification_type="order_created",
            title="Order Received",
            message="Your order has been received.",
            send_email=False,
            metadata={"order_id": 123},
        )

        self.assertIsNotNone(notification)
        self.assertIsNotNone(event)
        push_client.return_value.publish_multiple.assert_called_once()
        event.refresh_from_db()
        self.assertEqual(event.metadata["push"]["attempted"], 1)
        self.assertEqual(event.metadata["push"]["sent"], 1)

    @patch("exponent_server_sdk.PushClient")
    def test_send_notification_skips_push_for_registration_and_signin_events(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.user,
            token="ExponentPushToken[test-token]",
            platform="ios",
        )

        for notification_type in ("registration", "signin"):
            NotificationService.send_notification(
                user=self.user,
                notification_type=notification_type,
                title="Auth Event",
                message="Auth event should not push.",
                send_email=False,
            )

        push_client.return_value.publish_multiple.assert_not_called()
        self.assertFalse(
            NotificationEvent.objects.filter(metadata__has_key="push").exists()
        )
