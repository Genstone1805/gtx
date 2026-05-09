from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from order.models import GiftCardOrder
from .models import PhoneVerificationRequest, ReferralCommission, UserProfile


class MockTermiiResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


@override_settings(
    TERMII_API_KEY='test-termii-key',
    TERMII_PHONE_OTP_SENDER_ID='TestSender',
    TERMII_PHONE_OTP_BRAND_NAME='GTX',
)
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
        self.assertEqual(call_kwargs['json']['from'], 'TestSender')
        self.assertEqual(call_kwargs['json']['message_type'], 'NUMERIC')
        self.assertEqual(call_kwargs['headers']['Content-Type'], 'application/json')

    @patch('account.views.requests.post')
    def test_verify_phone_number_saves_phone_after_successful_token_check(self, mock_post):
        PhoneVerificationRequest.create_for_user(self.user, '+2348109477743', 'pin-123')
        mock_post.return_value = MockTermiiResponse(
            {
                'pinId': 'pin-123',
                'verified': 'True',
                'msisdn': '2348109477743',
            }
        )

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
        self.assertEqual(call_kwargs['headers']['Content-Type'], 'application/json')

    @patch('account.views.requests.post')
    def test_verify_phone_number_rejects_mismatched_verified_number(self, mock_post):
        PhoneVerificationRequest.create_for_user(self.user, '+2348109477743', 'pin-123')
        mock_post.return_value = MockTermiiResponse(
            {
                'pinId': 'pin-123',
                'verified': 'True',
                'msisdn': '2348109077743',
            }
        )

        response = self.client.post(
            reverse('verify-phone-number'),
            {'code': '123456'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'Verification failed for this phone number. Please request a new code.',
        )

        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone_number)
        self.assertTrue(PhoneVerificationRequest.objects.filter(user=self.user).exists())

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

    @override_settings(TERMII_PHONE_OTP_SENDER_ID='')
    @patch('account.views.requests.post')
    def test_add_phone_number_requires_configured_sender_id(self, mock_post):
        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            'Phone verification is not configured. '
            'Set TERMII_PHONE_OTP_SENDER_ID to an active Termii sender ID.',
        )
        mock_post.assert_not_called()

    @patch('account.views.requests.post')
    def test_add_phone_number_returns_actionable_error_for_unregistered_sender_id(self, mock_post):
        mock_post.return_value = MockTermiiResponse(
            {
                'message': (
                    'ApplicationSenderId not found for applicationId: 37677 '
                    'and senderName: TestSender'
                ),
            },
            status_code=404,
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            "Termii sender ID 'TestSender' is not active for this account. "
            'Set TERMII_PHONE_OTP_SENDER_ID to an approved sender ID from your Termii dashboard.',
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    REFERRAL_QUALIFYING_AMOUNT='100.00',
    REFERRAL_COMMISSION_PERCENT='10.00',
)
class ReferralFlowTests(APITestCase):
    def test_user_gets_referral_code_automatically(self):
        user = UserProfile.objects.create_user(
            email='referrer@example.com',
            password='StrongPassword123',
        )

        self.assertTrue(user.referral_code)
        self.assertEqual(len(user.referral_code), 10)

    def test_signup_accepts_valid_referral_code(self):
        referrer = UserProfile.objects.create_user(
            email='referrer@example.com',
            password='StrongPassword123',
        )

        response = self.client.post(
            reverse('signup'),
            {
                'email': 'referred@example.com',
                'password': 'StrongPassword123',
                'full_name': 'Referred User',
                'referral_code': referrer.referral_code,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        referred = UserProfile.objects.get(email='referred@example.com')
        self.assertEqual(referred.referred_by, referrer)

    def test_signup_rejects_invalid_referral_code(self):
        response = self.client.post(
            reverse('signup'),
            {
                'email': 'referred@example.com',
                'password': 'StrongPassword123',
                'full_name': 'Referred User',
                'referral_code': 'BADCODE123',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('referral_code', response.data)

    def test_referrer_is_not_rewarded_immediately(self):
        referrer = UserProfile.objects.create_user(email='referrer@example.com', password='StrongPassword123')
        UserProfile.objects.create_user(
            email='referred@example.com',
            password='StrongPassword123',
            referred_by=referrer,
        )

        self.assertFalse(ReferralCommission.objects.exists())

    def test_referrer_gets_reward_after_qualifying_successful_transaction_once(self):
        referrer = UserProfile.objects.create_user(email='referrer@example.com', password='StrongPassword123')
        referred = UserProfile.objects.create_user(
            email='referred@example.com',
            password='StrongPassword123',
            referred_by=referrer,
        )

        GiftCardOrder.objects.create(user=referred, type='E-Code', card=None, amount=80, status='Approved')
        self.assertFalse(ReferralCommission.objects.exists())

        qualifying_order = GiftCardOrder.objects.create(
            user=referred,
            type='E-Code',
            card=None,
            amount=20,
            status='Approved',
        )

        commission = ReferralCommission.objects.get()
        self.assertEqual(commission.referrer, referrer)
        self.assertEqual(commission.referred_user, referred)
        self.assertEqual(commission.qualifying_transaction, qualifying_order)
        self.assertEqual(str(commission.amount), '2.00')

        GiftCardOrder.objects.create(user=referred, type='E-Code', card=None, amount=200, status='Approved')
        self.assertEqual(ReferralCommission.objects.count(), 1)

        referrer.refresh_from_db()
        self.assertEqual(str(referrer.withdrawable_balance), '2.00')

    def test_failed_or_pending_transactions_do_not_trigger_reward(self):
        referrer = UserProfile.objects.create_user(email='referrer@example.com', password='StrongPassword123')
        referred = UserProfile.objects.create_user(
            email='referred@example.com',
            password='StrongPassword123',
            referred_by=referrer,
        )

        GiftCardOrder.objects.create(user=referred, type='E-Code', card=None, amount=1000, status='Pending')
        GiftCardOrder.objects.create(user=referred, type='E-Code', card=None, amount=1000, status='Rejected')

        self.assertFalse(ReferralCommission.objects.exists())
