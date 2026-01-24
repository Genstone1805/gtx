from django.views.generic import TemplateView


# Main pages
class IndexView(TemplateView):
    template_name = 'index.html'


class CreateGiftCardView(TemplateView):
    template_name = 'create-gift-card.html'


class CreateGiftStoreView(TemplateView):
    template_name = 'create-gift-store.html'


class UpdateGiftCardView(TemplateView):
    template_name = 'update-gift-card.html'


class UpdateGiftStoreView(TemplateView):
    template_name = 'update-gift-store.html'


# Auth pages
class LoginView(TemplateView):
    template_name = 'auth/login.html'


class SignupView(TemplateView):
    template_name = 'auth/signup.html'


class VerifyView(TemplateView):
    template_name = 'auth/verify.html'


class ForgotPasswordView(TemplateView):
    template_name = 'auth/forgot-password.html'


class ResetPasswordView(TemplateView):
    template_name = 'auth/reset-password.html'


# Profile pages
class DashboardView(TemplateView):
    template_name = 'profile/dashboard.html'


class ProfilePictureView(TemplateView):
    template_name = 'profile/profile-picture.html'


class TransactionPinView(TemplateView):
    template_name = 'profile/transaction-pin.html'


# Credentials pages
class Level2CredentialsView(TemplateView):
    template_name = 'credentials/level2.html'


class Level3CredentialsView(TemplateView):
    template_name = 'credentials/level3.html'


# Admin pages
class AdminDashboardView(TemplateView):
    template_name = 'admin/dashboard.html'


class PendingLevel2View(TemplateView):
    template_name = 'admin/pending-level2.html'


class PendingLevel3View(TemplateView):
    template_name = 'admin/pending-level3.html'
