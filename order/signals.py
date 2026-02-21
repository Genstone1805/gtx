"""
Django signals for automatic balance updates and notifications.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum, F

from order.models import GiftCardOrder
from account.models import UserProfile
from notification.services import (
    notify_order_created,
    notify_order_status_changed,
    notify_balance_updated,
)


@receiver(post_save, sender=GiftCardOrder)
def handle_order_created(sender, instance, created, **kwargs):
    """Send notification when a new order is created."""
    if created:
        notify_order_created(
            user=instance.user,
            order=instance,
            amount=instance.amount,
        )


@receiver(post_save, sender=GiftCardOrder)
def handle_order_status_change(sender, instance, **kwargs):
    """
    Handle balance updates when order status changes.
    This signal updates pending_balance and withdrawable_balance automatically.
    """
    if not instance.pk:
        return

    # Get the old instance to compare status
    try:
        old_instance = GiftCardOrder.objects.get(pk=instance.pk)
        old_status = old_instance.status
    except GiftCardOrder.DoesNotExist:
        return

    # Only process if status actually changed
    if old_status == instance.status:
        return

    user = instance.user
    amount = instance.amount

    with transaction.atomic():
        # Handle old status reversal
        if old_status == 'Pending':
            # Remove from pending balance
            user.pending_balance = max(0, user.pending_balance - amount)

        elif old_status == 'Approved':
            # Remove from withdrawable balance
            user.withdrawable_balance = max(0, user.withdrawable_balance - amount)

        # Handle new status addition
        if instance.status == 'Pending':
            # Add to pending balance
            user.pending_balance += amount

        elif instance.status == 'Approved':
            # Remove from pending, add to withdrawable
            user.pending_balance = max(0, user.pending_balance - amount)
            user.withdrawable_balance += amount

        user.save()

    # Send notification about status change
    notify_order_status_changed(
        user=user,
        order=instance,
        new_status=instance.status,
        amount=amount,
    )


def recalculate_user_balances(user: UserProfile) -> tuple[float, float]:
    """
    Recalculate user balances from scratch based on their orders.
    This is useful for data consistency checks or migration.

    Returns:
        Tuple of (pending_balance, withdrawable_balance)
    """
    # Calculate pending balance (orders with status 'Pending')
    pending_result = GiftCardOrder.objects.filter(
        user=user,
        status='Pending'
    ).aggregate(total=Sum('amount'))
    pending_balance = pending_result['total'] or 0

    # Calculate withdrawable balance (orders with status 'Approved')
    withdrawable_result = GiftCardOrder.objects.filter(
        user=user,
        status='Approved'
    ).aggregate(total=Sum('amount'))
    withdrawable_balance = withdrawable_result['total'] or 0

    # Update user model
    with transaction.atomic():
        user.pending_balance = pending_balance
        user.withdrawable_balance = withdrawable_balance
        user.save()

    return pending_balance, withdrawable_balance
