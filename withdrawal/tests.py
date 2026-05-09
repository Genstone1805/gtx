from decimal import Decimal

from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from account.models import Level2Credentials, UserProfile
from order.models import GiftCardOrder
from withdrawal.models import Withdrawal


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class WithdrawalLimitTests(APITestCase):
    def create_verified_user(self, email='user@example.com', order_amount=3000000):
        user = UserProfile.objects.create_user(
            email=email,
            password='StrongPassword123',
            is_verified=True,
            phone_number='+2348109477743',
        )
        user.set_transaction_pin('1234')
        user.save()
        GiftCardOrder.objects.create(
            user=user,
            type='E-Code',
            card=None,
            amount=order_amount,
            status='Approved',
        )
        user.refresh_from_db()
        self.client.force_authenticate(user=user)
        return user

    def test_unverified_user_cannot_withdraw(self):
        user = UserProfile.objects.create_user(
            email='user@example.com',
            password='StrongPassword123',
        )
        user.set_transaction_pin('1234')
        user.save()
        GiftCardOrder.objects.create(user=user, type='E-Code', card=None, amount=1000000, status='Approved')
        self.client.force_authenticate(user=user)

        response = self.client.post(
            '/withdrawal/requests/create/',
            {
                'amount': '1000.00',
                'transaction_pin': '1234',
                'bank_name': 'Test Bank',
                'account_name': 'Test User',
                'account_number': '1234567890',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'Complete email and phone verification before making withdrawals.',
        )

    def test_level1_single_withdrawal_limit_is_enforced(self):
        self.create_verified_user()

        response = self.client.post(
            '/withdrawal/requests/create/',
            {
                'amount': '500000.01',
                'transaction_pin': '1234',
                'bank_name': 'Test Bank',
                'account_name': 'Test User',
                'account_number': '1234567890',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('single withdrawal limit', response.data['amount'][0])

    def test_level1_daily_amount_limit_is_enforced(self):
        user = self.create_verified_user()
        Withdrawal.objects.create(
            user=user,
            amount=Decimal('900000.00'),
            status='Pending',
            bank_name='Test Bank',
            account_name='Test User',
            account_number='1234567890',
        )

        response = self.client.post(
            '/withdrawal/requests/create/',
            {
                'amount': '200000.00',
                'transaction_pin': '1234',
                'bank_name': 'Test Bank',
                'account_name': 'Test User',
                'account_number': '1234567890',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['amount'][0], 'You have exceeded your daily withdrawal limit.')

    def test_level1_daily_count_limit_is_enforced(self):
        user = self.create_verified_user()
        for _ in range(3):
            Withdrawal.objects.create(
                user=user,
                amount=Decimal('1000.00'),
                status='Pending',
                bank_name='Test Bank',
                account_name='Test User',
                account_number='1234567890',
            )

        response = self.client.post(
            '/withdrawal/requests/create/',
            {
                'amount': '1000.00',
                'transaction_pin': '1234',
                'bank_name': 'Test Bank',
                'account_name': 'Test User',
                'account_number': '1234567890',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data['detail'],
            'You have reached the maximum number of withdrawals allowed today.',
        )

    def test_level2_limit_allows_amount_above_level1_single_limit(self):
        credentials = Level2Credentials.objects.create(nin='123456789012', nin_image='nin.jpg', approved=True, status='Approved')
        user = self.create_verified_user(order_amount=3000000)
        user.level = 'Level 2'
        user.level2_credentials = credentials
        user.save()

        response = self.client.post(
            '/withdrawal/requests/create/',
            {
                'amount': '750000.00',
                'transaction_pin': '1234',
                'bank_name': 'Test Bank',
                'account_name': 'Test User',
                'account_number': '1234567890',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
