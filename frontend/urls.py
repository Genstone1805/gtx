from django.urls import path
from . import views

app_name = 'frontend'

urlpatterns = [
    # Main pages
    path('', views.IndexView.as_view(), name='index'),
    path('create-gift-card/', views.CreateGiftCardView.as_view(), name='create-gift-card'),
    path('create-gift-store/', views.CreateGiftStoreView.as_view(), name='create-gift-store'),
    path('update-gift-card/', views.UpdateGiftCardView.as_view(), name='update-gift-card'),
    path('update-gift-store/', views.UpdateGiftStoreView.as_view(), name='update-gift-store'),

    # Auth pages
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/signup/', views.SignupView.as_view(), name='signup'),
    path('auth/verify/', views.VerifyView.as_view(), name='verify'),
    path('auth/forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),

    # Profile pages
    path('profile/dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('profile/profile-picture/', views.ProfilePictureView.as_view(), name='profile-picture'),
    path('profile/transaction-pin/', views.TransactionPinView.as_view(), name='transaction-pin'),

    # Credentials pages
    path('credentials/level2/', views.Level2CredentialsView.as_view(), name='credentials-level2'),
    path('credentials/level3/', views.Level3CredentialsView.as_view(), name='credentials-level3'),

    # Admin pages
    path('admin/dashboard/', views.AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/pending-level2/', views.PendingLevel2View.as_view(), name='pending-level2'),
    path('admin/pending-level3/', views.PendingLevel3View.as_view(), name='pending-level3'),
]
