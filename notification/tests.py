from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from account.models import UserProfile
from notification.models import (
    NotificationEvent,
    PushNotificationSubscriber,
    PushNotificationLog,
)
from notification.services import NotificationService


class NotificationServicePushTests(TestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            email="user@example.com",
            password="password123",
        )

    @staticmethod
    def _expo_token_check(token):
        return isinstance(token, str) and token.startswith("ExponentPushToken")

    @patch("exponent_server_sdk.PushClient")
    def test_send_notification_sends_push_to_active_subscribers(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.user,
            token="ExponentPushToken[test-token]",
            platform="ios",
        )
        push_client.is_exponent_push_token.side_effect = self._expo_token_check
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

    @patch("exponent_server_sdk.PushClient")
    def test_send_notification_deactivates_invalid_expo_tokens(self, push_client):
        subscriber = PushNotificationSubscriber.objects.create(
            user=self.user,
            token="not-a-valid-expo-token",
            platform="android",
        )
        push_client.is_exponent_push_token.side_effect = self._expo_token_check

        notification, event = NotificationService.send_notification(
            user=self.user,
            notification_type="order_created",
            title="Order Received",
            message="Your order has been received.",
            send_email=False,
        )

        # Invalid token must not be sent to Expo, and should be deactivated.
        push_client.return_value.publish_multiple.assert_not_called()
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)
        event.refresh_from_db()
        self.assertEqual(event.metadata["push"]["deactivated"], 1)

    @patch("exponent_server_sdk.PushClient")
    def test_push_client_built_with_timeout(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.user,
            token="ExponentPushToken[test-token]",
            platform="ios",
        )
        push_client.is_exponent_push_token.side_effect = self._expo_token_check
        ticket = Mock()
        ticket.validate_response.return_value = None
        push_client.return_value.publish_multiple.return_value = [ticket]

        NotificationService.send_notification(
            user=self.user,
            notification_type="order_created",
            title="Order Received",
            message="Your order has been received.",
            send_email=False,
        )

        # The client must be constructed with a bounded timeout so a slow Expo
        # endpoint cannot hang the request thread.
        _, kwargs = push_client.call_args
        self.assertIn("timeout", kwargs)
        self.assertIsNotNone(kwargs["timeout"])

    @patch("exponent_server_sdk.PushClient")
    def test_push_writes_debug_log(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.user,
            token="ExponentPushToken[test-token]",
            platform="ios",
        )
        push_client.is_exponent_push_token.side_effect = self._expo_token_check
        ticket = Mock()
        ticket.validate_response.return_value = None
        ticket.is_success.return_value = True
        ticket.status = "ok"
        ticket.id = "receipt-1"
        ticket.message = ""
        ticket.details = None
        push_client.return_value.publish_multiple.return_value = [ticket]

        NotificationService.send_notification(
            user=self.user,
            notification_type="order_created",
            title="Order Received",
            message="Your order has been received.",
            send_email=False,
        )

        log = PushNotificationLog.objects.latest("created_at")
        self.assertEqual(log.status, "success")
        self.assertEqual(log.trigger, "notification")
        self.assertEqual(log.sent, 1)
        self.assertEqual(log.attempted, 1)
        self.assertEqual(len(log.request_payload), 1)
        self.assertEqual(len(log.response), 1)
        self.assertEqual(log.response[0]["token"], "ExponentPushToken[test-token]")

    def test_push_logs_when_user_has_no_tokens(self):
        result = NotificationService.send_notification(
            user=self.user,
            notification_type="order_created",
            title="Order Received",
            message="Your order has been received.",
            send_email=False,
        )
        self.assertIsNotNone(result)
        log = PushNotificationLog.objects.latest("created_at")
        self.assertEqual(log.status, "no_tokens")
        self.assertEqual(log.attempted, 0)


class AdminPushTestEndpointTests(TestCase):
    def setUp(self):
        self.admin = UserProfile.objects.create_superuser(
            email="admin@example.com",
            password="password123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    @staticmethod
    def _expo_token_check(token):
        return isinstance(token, str) and token.startswith("ExponentPushToken")

    @patch("exponent_server_sdk.PushClient")
    def test_admin_can_fire_test_push_and_get_full_behaviour(self, push_client):
        PushNotificationSubscriber.objects.create(
            user=self.admin,
            token="ExponentPushToken[admin-token]",
            platform="android",
        )
        push_client.is_exponent_push_token.side_effect = self._expo_token_check
        ticket = Mock()
        ticket.validate_response.return_value = None
        ticket.is_success.return_value = True
        ticket.status = "ok"
        ticket.id = "receipt-1"
        ticket.message = ""
        ticket.details = None
        push_client.return_value.publish_multiple.return_value = [ticket]

        response = self.client.post(
            reverse("notification:admin-push-test"),
            {"title": "Hi", "body": "Test body"},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["active_tokens"], 1)
        self.assertEqual(data["result"]["sent"], 1)
        self.assertEqual(data["result"]["status"], "success")
        self.assertEqual(data["log"]["trigger"], "test")
        self.assertEqual(data["target_user_email"], "admin@example.com")

    def test_non_admin_cannot_use_test_endpoint(self):
        user = UserProfile.objects.create_user(
            email="regular@example.com", password="password123"
        )
        client = APIClient()
        client.force_authenticate(user=user)
        response = client.post(reverse("notification:admin-push-test"), {}, format="json")
        self.assertEqual(response.status_code, 403)
