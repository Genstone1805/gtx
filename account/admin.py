from django.contrib import admin
from .models import (
    UserProfile,
    Level2Credentials,
    Level3Credentials,
    EmailVerificationCode,
    PasswordResetCode,
    BankAccountDetails,
)


admin.site.register(UserProfile)
admin.site.register(Level2Credentials)
admin.site.register(Level3Credentials)
admin.site.register(EmailVerificationCode)
admin.site.register(PasswordResetCode)
admin.site.register(BankAccountDetails)
