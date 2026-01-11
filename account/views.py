from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal

from .models import UserProfile, EmailVerificationCode, PasswordResetCode, Level2Credentials, Level3Credentials
from .serializers import (
    SignupSerializer, VerifyCodeSerializer, ResendCodeSerializer,
    PasswordResetRequestSerializer, PasswordResetVerifySerializer,
    LoginSerializer, CreateTransactionPinSerializer, UpdateTransactionPinSerializer,
    Level2CredentialsSerializer, Level3CredentialsSerializer,
    UserProfileSerializer, ProfilePictureSerializer
)


def send_verification_email(user, code):
    """Send verification code email to user."""
    subject = 'Your Verification Code'
    from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
    to_email = user.email

    context = {
        'code': code,
        'user': user,
    }

    text_content = render_to_string('account/verification_code_email.txt', context)
    html_content = render_to_string('account/verification_code_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, 'text/html')
    email.send()


class SignupView(APIView):
    """Handle user signup with email verification code."""

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if not serializer.is_valid(raise_exception=True):
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        full_name = serializer.validated_data.get('full_name', '')

        # Check if user already exists
        try:
            user = UserProfile.objects.get(email=email)
            if user.is_verified:
                return Response(
                    {'detail': 'User with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            # User exists but not verified - resend code
        except UserProfile.DoesNotExist:
            # Create new user
            user = UserProfile.objects.create_user(email=email, password=password)
            user.full_name = full_name
            user.is_verified = False
            user.save()

        # Generate and send verification code
        verification = EmailVerificationCode.create_for_user(user)
        send_verification_email(user, verification.code)

        return Response(
            {
                'detail': 'Verification code sent to your email.',
                'email': email
            },
            status=status.HTTP_201_CREATED
        )


class VerifyEmailView(APIView):
    """Verify email with 6-digit code."""

    def post(self, request):
        serializer = VerifyCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {'detail': 'Email already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check verification code
        try:
            verification = EmailVerificationCode.objects.get(user=user, code=code)
        except EmailVerificationCode.DoesNotExist:
            return Response(
                {'detail': 'Invalid verification code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if verification.is_expired():
            verification.delete()
            return Response(
                {'detail': 'Verification code has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify user
        user.is_verified = True
        user.save()
        verification.delete()

        # Send welcome email
        send_welcome_email(user)

        return Response(
            {'detail': 'Email verified successfully.'},
            status=status.HTTP_200_OK
        )


class ResendCodeView(APIView):
    """Resend verification code."""

    def post(self, request):
        serializer = ResendCodeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if user.is_verified:
            return Response(
                {'detail': 'Email already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate and send new code
        verification = EmailVerificationCode.create_for_user(user)
        send_verification_email(user, verification.code)

        return Response(
            {'detail': 'Verification code sent to your email.'},
            status=status.HTTP_200_OK
        )


def send_password_reset_email(user, code):
    """Send password reset code email to user."""
    subject = 'Password Reset Code'
    from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
    to_email = user.email

    context = {
        'code': code,
        'user': user,
    }

    text_content = render_to_string('account/password_reset_email.txt', context)
    html_content = render_to_string('account/password_reset_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, 'text/html')
    email.send()


def send_welcome_email(user):
    """Send welcome email after successful registration."""
    subject = 'Welcome to GTX!'
    from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
    to_email = user.email

    context = {'user': user}

    text_content = render_to_string('account/welcome_email.txt', context)
    html_content = render_to_string('account/welcome_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, 'text/html')
    email.send()


def send_password_reset_success_email(user):
    """Send email after successful password reset."""
    subject = 'Password Reset Successful'
    from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
    to_email = user.email

    context = {
        'user': user,
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
    }

    text_content = render_to_string('account/password_reset_success_email.txt', context)
    html_content = render_to_string('account/password_reset_success_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, 'text/html')
    email.send()


def send_new_login_email(user, ip_address):
    """Send email when new login is detected."""
    subject = 'New Login Detected'
    from_email = getattr(settings, 'EMAIL_FROM', settings.DEFAULT_FROM_EMAIL)
    to_email = user.email

    context = {
        'user': user,
        'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
        'ip_address': ip_address or 'Unknown',
    }

    text_content = render_to_string('account/new_login_email.txt', context)
    html_content = render_to_string('account/new_login_email.html', context)

    email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    email.attach_alternative(html_content, 'text/html')
    email.send()


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class PasswordResetRequestView(APIView):
    """Request password reset - sends 6-digit code to email."""

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            # Don't reveal if email exists
            return Response(
                {'detail': 'If this email exists, a reset code has been sent.'},
                status=status.HTTP_200_OK
            )

        # Generate and send reset code
        reset_code = PasswordResetCode.create_for_user(user)
        send_password_reset_email(user, reset_code.code)

        return Response(
            {'detail': 'If this email exists, a reset code has been sent.'},
            status=status.HTTP_200_OK
        )


class PasswordResetVerifyView(APIView):
    """Verify reset code and set new password."""

    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {'detail': 'Invalid email or code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check reset code
        try:
            reset_code = PasswordResetCode.objects.get(user=user, code=code)
        except PasswordResetCode.DoesNotExist:
            return Response(
                {'detail': 'Invalid email or code.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if reset_code.is_expired():
            reset_code.delete()
            return Response(
                {'detail': 'Reset code has expired. Please request a new one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Set new password
        user.set_password(new_password)
        user.save()
        reset_code.delete()

        # Send password reset success email
        send_password_reset_success_email(user)

        return Response(
            {'detail': 'Password reset successfully.'},
            status=status.HTTP_200_OK
        )


class LoginView(APIView):
    """Handle user login with new login notification."""

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_verified:
            return Response(
                {'detail': 'Please verify your email before logging in.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.is_active:
            return Response(
                {'detail': 'Your account has been disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        # Update last login and IP
        ip_address = get_client_ip(request)
        user.last_login = timezone.now()
        user.ip_address = ip_address
        user.save()

        # Send new login notification email
        send_new_login_email(user, ip_address)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'email': user.email,
                'full_name': user.full_name,
            }
        }, status=status.HTTP_200_OK)


class CreateTransactionPinView(APIView):
    """Create a 4-digit transaction PIN for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if user.transaction_pin:
            return Response(
                {'detail': 'Transaction PIN already exists. Use update endpoint to change it.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = CreateTransactionPinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user.transaction_pin = serializer.validated_data['pin']
        user.save()

        return Response(
            {'detail': 'Transaction PIN created successfully.'},
            status=status.HTTP_201_CREATED
        )


class UpdateTransactionPinView(APIView):
    """Update the transaction PIN for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.transaction_pin:
            return Response(
                {'detail': 'No transaction PIN exists. Use create endpoint first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateTransactionPinSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        if user.transaction_pin != serializer.validated_data['old_pin']:
            return Response(
                {'detail': 'Current PIN is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.transaction_pin = serializer.validated_data['new_pin']
        user.save()

        return Response(
            {'detail': 'Transaction PIN updated successfully.'},
            status=status.HTTP_200_OK
        )


class SubmitLevel2CredentialsView(APIView):
    """Submit Level 2 credentials (NIN verification) to upgrade account."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        if user.level in ['Level 2', 'Level 3']:
            return Response(
                {'detail': 'You are already Level 2 or higher.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.level2_credentials:
            return Response(
                {'detail': 'Level 2 credentials already submitted. Status: ' + user.level2_credentials.status},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = Level2CredentialsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        credentials = Level2Credentials.objects.create(
            nin=serializer.validated_data['nin'],
            nin_image=serializer.validated_data['nin_image'],
            status='Pending'
        )

        user.level2_credentials = credentials
        user.save()

        return Response(
            {'detail': 'Level 2 credentials submitted successfully. Awaiting approval.'},
            status=status.HTTP_201_CREATED
        )


class SubmitLevel3CredentialsView(APIView):
    """Submit Level 3 credentials (address verification) to upgrade account."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        if user.level == 'Level 3':
            return Response(
                {'detail': 'You are already Level 3.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.level != 'Level 2':
            return Response(
                {'detail': 'You must be Level 2 before applying for Level 3.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.level3_credentials:
            return Response(
                {'detail': 'Level 3 credentials already submitted. Status: ' + user.level3_credentials.status},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = Level3CredentialsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        credentials = Level3Credentials.objects.create(
            house_address_1=serializer.validated_data['house_address_1'],
            house_address_2=serializer.validated_data.get('house_address_2', ''),
            nearest_bus_stop=serializer.validated_data['nearest_bus_stop'],
            city=serializer.validated_data['city'],
            state=serializer.validated_data['state'],
            country=serializer.validated_data['country'],
            proof_of_address_image=serializer.validated_data['proof_of_address_image'],
            face_verification_image=serializer.validated_data['face_verification_image'],
            status='Pending'
        )

        user.level3_credentials = credentials
        user.save()

        return Response(
            {'detail': 'Level 3 credentials submitted successfully. Awaiting approval.'},
            status=status.HTTP_201_CREATED
        )


class CurrentUserView(APIView):
    """Get current authenticated user's details."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UploadProfilePictureView(APIView):
    """Upload profile picture for the authenticated user."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        if user.dp:
            return Response(
                {'detail': 'Profile picture already exists. Use update endpoint to change it.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = ProfilePictureSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user.dp = serializer.validated_data['dp']
        user.save()

        return Response(
            {'detail': 'Profile picture uploaded successfully.'},
            status=status.HTTP_201_CREATED
        )


class UpdateProfilePictureView(APIView):
    """Update profile picture for the authenticated user."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user = request.user

        serializer = ProfilePictureSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Delete old profile picture if exists
        if user.dp:
            user.dp.delete(save=False)

        user.dp = serializer.validated_data['dp']
        user.save()

        return Response(
            {'detail': 'Profile picture updated successfully.'},
            status=status.HTTP_200_OK
        )
