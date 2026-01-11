from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    SignupView, VerifyEmailView, ResendCodeView,
    PasswordResetRequestView, PasswordResetVerifyView,
    LoginView, CreateTransactionPinView, UpdateTransactionPinView,
    SubmitLevel2CredentialsView, SubmitLevel3CredentialsView,
    CurrentUserView, UploadProfilePictureView,
    UpdateProfilePictureView,
    ChangePasswordView
)

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('signup/verify/', VerifyEmailView.as_view(), name='signup-verify'),
    path('signup/resend-code/', ResendCodeView.as_view(), name='resend-code'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password/reset/verify/', PasswordResetVerifyView.as_view(), name='password-reset-verify'),

    # Transaction PIN
    path('pin/create/', CreateTransactionPinView.as_view(), name='pin-create'),
    path('pin/update/', UpdateTransactionPinView.as_view(), name='pin-update'),

    # Level credentials
    path('credentials/level2/', SubmitLevel2CredentialsView.as_view(), name='credentials-level2'),
    path('credentials/level3/', SubmitLevel3CredentialsView.as_view(), name='credentials-level3'),

    # User profile
    path('me/', CurrentUserView.as_view(), name='current-user'),
    path('profile/picture/upload/', UploadProfilePictureView.as_view(), name='profile-picture-upload'),
    path('profile/picture/update/', UpdateProfilePictureView.as_view(), name='profile-picture-update'),
]
