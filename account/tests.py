from unittest.mock import patch

from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from order.models import GiftCardOrder
from .models import PhoneVerificationRequest, ReferralCommission, UserProfile


class MockTwilioResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300

    def json(self):
        return self._payload


@override_settings(
    TWILIO_ACCOUNT_SID='ACtest-account-sid',
    TWILIO_AUTH_TOKEN='test-auth-token',
    TWILIO_VERIFY_SERVICE_SID='VAtest-service-sid',
    TWILIO_VERIFY_SERVICE_NAME='',
)
class PhoneVerificationFlowTests(APITestCase):
    verification_sid = f"VE{'1' * 32}"

    def setUp(self):
        self.user = UserProfile.objects.create_user(
            email='tester@example.com',
            password='StrongPassword123',
        )
        self.client.force_authenticate(user=self.user)

    @patch('account.views.requests.post')
    def test_add_phone_number_starts_verification_instead_of_saving_immediately(self, mock_post):
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'pending',
                'to': '+2348109477743',
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
        self.assertEqual(verification_request.pin_id, self.verification_sid)
        self.assertEqual(verification_request.phone_number.as_e164, '+2348109477743')

        call_args, call_kwargs = mock_post.call_args
        self.assertTrue(call_args[0].endswith('/Services/VAtest-service-sid/Verifications'))
        self.assertEqual(call_kwargs['data']['To'], '+2348109477743')
        self.assertEqual(call_kwargs['data']['Channel'], 'sms')
        self.assertEqual(
            call_kwargs['auth'],
            ('ACtest-account-sid', 'test-auth-token'),
        )

    @patch('account.views.requests.post')
    def test_verify_phone_number_saves_phone_after_successful_token_check(self, mock_post):
        PhoneVerificationRequest.create_for_user(
            self.user,
            '+2348109477743',
            self.verification_sid,
        )
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'approved',
                'to': '+2348109477743',
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
        self.assertTrue(call_args[0].endswith('/Services/VAtest-service-sid/VerificationCheck'))
        self.assertEqual(call_kwargs['data']['To'], '+2348109477743')
        self.assertEqual(call_kwargs['data']['Code'], '123456')
        self.assertEqual(
            call_kwargs['auth'],
            ('ACtest-account-sid', 'test-auth-token'),
        )

    @patch('account.views.requests.post')
    def test_verify_phone_number_rejects_mismatched_verification_sid(self, mock_post):
        PhoneVerificationRequest.create_for_user(
            self.user,
            '+2348109477743',
            self.verification_sid,
        )
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': f"VE{'2' * 32}",
                'status': 'approved',
                'to': '+2348109477743',
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
        PhoneVerificationRequest.create_for_user(
            self.user,
            '+2348109477743',
            f"VE{'0' * 32}",
        )
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'pending',
            }
        )

        response = self.client.post(reverse('resend-phone-verification'), {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Verification code resent successfully.')

        verification_request = PhoneVerificationRequest.objects.get(user=self.user)
        self.assertEqual(verification_request.pin_id, self.verification_sid)

    @override_settings(TWILIO_VERIFY_SERVICE_SID='')
    @patch('account.views.requests.post')
    def test_add_phone_number_requires_configured_verify_service(self, mock_post):
        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            'Phone verification is not configured. Set TWILIO_VERIFY_SERVICE_SID or TWILIO_VERIFY_SERVICE_NAME.',
        )
        mock_post.assert_not_called()

    @override_settings(
        TWILIO_ACCOUNT_SID='',
        TWILIO_AUTH_TOKEN='',
        TWILIO_VERIFY_SERVICE_SID='',
        TWILIO_SID='ACalias-account-sid',
        TWILIO_SECRETE='alias-auth-token',
        TWILIO_APP_SID='VAalias-service-sid',
    )
    @patch('account.views.requests.post')
    def test_add_phone_number_accepts_provided_alias_credential_names(self, mock_post):
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'pending',
                'to': '+2348109477743',
            }
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        call_args, call_kwargs = mock_post.call_args
        self.assertTrue(call_args[0].endswith('/Services/VAalias-service-sid/Verifications'))
        self.assertEqual(call_kwargs['auth'], ('ACalias-account-sid', 'alias-auth-token'))

    @override_settings(
        TWILIO_ACCOUNT_SID='',
        TWILIO_AUTH_TOKEN='',
        TWILIO_VERIFY_SERVICE_SID='',
        TWILIO_SID='ACalias-account-sid',
        TWILIO_SECRETE='alias-auth-token',
        TWILIO_VERIFY_SERVICE_NAME='GTX',
    )
    @patch('account.views.requests.get')
    @patch('account.views.requests.post')
    def test_add_phone_number_resolves_twilio_app_name_to_verify_service_sid(self, mock_post, mock_get):
        mock_get.return_value = MockTwilioResponse(
            {
                'services': [
                    {
                        'sid': 'VAresolved-service-sid',
                        'friendly_name': 'GTX',
                    }
                ]
            }
        )
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'pending',
                'to': '+2348109477743',
            }
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        lookup_args, lookup_kwargs = mock_get.call_args
        self.assertTrue(lookup_args[0].endswith('/Services'))
        self.assertEqual(lookup_kwargs['params']['PageSize'], 1000)

        post_args, post_kwargs = mock_post.call_args
        self.assertTrue(post_args[0].endswith('/Services/VAresolved-service-sid/Verifications'))
        self.assertEqual(post_kwargs['auth'], ('ACalias-account-sid', 'alias-auth-token'))

    @override_settings(
        TWILIO_VERIFY_SERVICE_SID='GTX',
        TWILIO_VERIFY_SERVICE_NAME='',
    )
    @patch('account.views.requests.post')
    def test_add_phone_number_rejects_non_sid_service_sid(self, mock_post):
        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            'TWILIO_VERIFY_SERVICE_SID must be the Verify Service SID that starts with VA. '
            'Use TWILIO_VERIFY_SERVICE_NAME for a friendly name.',
        )
        mock_post.assert_not_called()

    @override_settings(
        TWILIO_VERIFY_SERVICE_SID='',
        TWILIO_APP_NAME='VAlegacy-service-sid',
    )
    @patch('account.views.requests.post')
    def test_add_phone_number_accepts_legacy_app_name_when_it_is_a_sid(self, mock_post):
        mock_post.return_value = MockTwilioResponse(
            {
                'sid': self.verification_sid,
                'status': 'pending',
                'to': '+2348109477743',
            }
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        call_args, _ = mock_post.call_args
        self.assertTrue(call_args[0].endswith('/Services/VAlegacy-service-sid/Verifications'))

    @patch('account.views.requests.post')
    def test_add_phone_number_returns_actionable_error_for_invalid_credentials(self, mock_post):
        mock_post.return_value = MockTwilioResponse(
            {
                'code': 20003,
                'message': 'Authentication Error - invalid username',
            },
            status_code=401,
        )

        response = self.client.post(
            reverse('add-phone-number'),
            {'phone_number': '+2348109477743'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            'Twilio authentication failed. '
            'Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN.',
        )

    @patch('account.views.requests.post')
    def test_verify_phone_number_returns_bad_gateway_for_twilio_outage(self, mock_post):
        PhoneVerificationRequest.create_for_user(
            self.user,
            '+2348109477743',
            self.verification_sid,
        )
        mock_post.return_value = MockTwilioResponse(
            {'code': 20500, 'message': 'Internal Server Error'},
            status_code=500,
        )

        response = self.client.post(
            reverse('verify-phone-number'),
            {'code': '123456'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(
            response.data['detail'],
            'Phone verification provider is currently unavailable.',
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
