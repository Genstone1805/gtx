from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import PhoneVerificationRequest, UserProfile


class MockTermiiResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


class PhoneVerificationFlowTests(APITestCase):
    def setUp(self):
        self.user = UserProfile.objects.create_user(
            email='tester@example.com',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)

    @patch('account.views.requests.post')
    def test_add_phone_number_starts_verification_instead_of_saving_immediately(self, mock_post):
        mock_post.return_value = MockTermiiResponse(
            {
                'smsStatus': 'Message Sent',
                'pin_id': 'pin-123',
                'status': '200',
            }
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['detail'], 'Verification code sent to your phone number.')

        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone_number)

        verification_request = PhoneVerificationRequest.objects.get(user=self.user)
        self.assertEqual(verification_request.pin_id, 'pin-123')
        self.assertEqual(verification_request.phone_number.as_e164, '+2348109477743')

        call_args, call_kwargs = mock_post.call_args
        self.assertTrue(call_args[0].endswith('/api/sms/otp/send'))
        self.assertEqual(call_kwargs['json']['to'], '2348109477743')

    @patch('account.views.requests.post')
    def test_verify_phone_number_saves_phone_after_successful_token_check(self, mock_post):
        PhoneVerificationRequest.create_for_user(self.user, '+2348109477743', 'pin-123')
        mock_post.return_value = MockTermiiResponse({'verified': 'True'})

        response = self.client.post(
            reverse('verify-phone-number'),
            {'code': '123456'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Phone number verified successfully.')

        self.user.refresh_from_db()
        self.assertEqual(self.user.phone_number.as_e164, '+2348109477743')
        self.assertFalse(PhoneVerificationRequest.objects.filter(user=self.user).exists())

        call_args, call_kwargs = mock_post.call_args
        self.assertTrue(call_args[0].endswith('/api/sms/otp/verify'))
        self.assertEqual(call_kwargs['json']['pin_id'], 'pin-123')
        self.assertEqual(call_kwargs['json']['pin'], '123456')

    @patch('account.views.requests.post')
    def test_resend_phone_verification_replaces_existing_pin_id(self, mock_post):
        PhoneVerificationRequest.create_for_user(self.user, '+2348109477743', 'pin-old')
        mock_post.return_value = MockTermiiResponse(
            {
                'smsStatus': 'Message Sent',
                'pinId': 'pin-new',
                'status': '200',
            }
        )

        response = self.client.post(reverse('resend-phone-verification'), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Verification code resent successfully.')

        verification_request = PhoneVerificationRequest.objects.get(user=self.user)
        self.assertEqual(verification_request.pin_id, 'pin-new')
