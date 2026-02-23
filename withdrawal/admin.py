from django.contrib import admin
from .models import Withdrawal, WithdrawalAuditLog


admin.site.register(Withdrawal)
admin.site.register(WithdrawalAuditLog)
