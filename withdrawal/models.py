from django.db import models
from django.conf import settings
from django.utils import timezone


class Withdrawal(models.Model):
    """
    Withdrawal request model for users to withdraw their withdrawable balance.
    """
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
        ('Processing', 'Processing'),
        ('Completed', 'Completed'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawals'
    )
    amount = models.DecimalField(
        decimal_places=2,
        max_digits=12,
        help_text="Amount to withdraw"
    )
    
    # Bank account details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=100, blank=True, null=True)
    account_number = models.CharField(max_length=20, blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='Pending'
    )
    
    # Admin fields
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_withdrawals'
    )
    processed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    
    # Transaction reference
    transaction_reference = models.CharField(max_length=100, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='withdrawal_user_created_idx'),
            models.Index(fields=['user', 'status'], name='withdrawal_user_status_idx'),
            models.Index(fields=['status'], name='withdrawal_status_idx'),
        ]

    def __str__(self):
        return f"Withdrawal #{self.id} - {self.user.email} - ${self.amount} - {self.status}"

    def save(self, *args, **kwargs):
        # Ensure amount is always positive
        if self.amount and self.amount < 0:
            raise ValueError("Withdrawal amount cannot be negative")
        super().save(*args, **kwargs)

    def approve(self, admin_user: settings.AUTH_USER_MODEL, transaction_reference: str = None):
        """
        Approve the withdrawal request.
        This should be called within a transaction.
        """
        from order.signals import recalculate_user_balances
        
        if self.status != 'Pending':
            raise ValueError(f"Cannot approve withdrawal with status: {self.status}")
        
        self.status = 'Approved'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.transaction_reference = transaction_reference
        self.save()

        # Recalculate to keep balances consistent with source transactions.
        recalculate_user_balances(self.user)

    def reject(self, admin_user: settings.AUTH_USER_MODEL, reason: str):
        """
        Reject the withdrawal request.
        """
        from order.signals import recalculate_user_balances

        if self.status != 'Pending':
            raise ValueError(f"Cannot reject withdrawal with status: {self.status}")
        
        self.status = 'Rejected'
        self.processed_by = admin_user
        self.processed_at = timezone.now()
        self.rejection_reason = reason
        self.save()

        # Recalculate so rejected amount is returned to withdrawable balance.
        recalculate_user_balances(self.user)

    def can_cancel(self) -> bool:
        """Check if the withdrawal can be cancelled by the user."""
        return self.status == 'Pending'

    def cancel(self):
        """Cancel the withdrawal request."""
        from order.signals import recalculate_user_balances

        if not self.can_cancel():
            raise ValueError(f"Cannot cancel withdrawal with status: {self.status}")
        
        self.status = 'Cancelled'
        self.save()

        # Recalculate so cancelled amount is returned to withdrawable balance.
        recalculate_user_balances(self.user)


class WithdrawalAuditLog(models.Model):
    """
    Audit log for tracking all withdrawal-related actions.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('updated', 'Updated'),
    ]

    withdrawal = models.ForeignKey(
        Withdrawal,
        on_delete=models.CASCADE,
        related_name='audit_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    details = models.TextField(blank=True, null=True)
    previous_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Audit #{self.id} - Withdrawal #{self.withdrawal.id} - {self.action}"
