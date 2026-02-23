"""
Django signals for automatic balance updates and notifications.
"""
from decimal import Decimal

from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.db.models import Sum

from order.models import GiftCardOrder
from account.models import UserProfile
from notification.services import (
    notify_order_created,
    notify_order_status_changed,
)


PENDING_STATUSES = {'Pending'}
WITHDRAWABLE_STATUSES = {'Approved', 'Completed'}


def _as_decimal(amount: int | float | Decimal) -> Decimal:
    return Decimal(str(amount))


@receiver(pre_save, sender=GiftCardOrder)
def capture_old_order_status(sender, instance, **kwargs):
    """
    Capture the old status before save so post_save can compare transitions.
    """
    if not instance.pk:
        instance._old_status = None
        return

    old_status = GiftCardOrder.objects.filter(pk=instance.pk).values_list('status', flat=True).first()
    instance._old_status = old_status


@receiver(post_save, sender=GiftCardOrder)
def handle_order_created(sender, instance, created, **kwargs):
    """
    Handle order creation side effects:
    - notify user
    - reconcile balances for newly-created orders
    """
    if not created:
        return

    recalculate_user_balances(instance.user)
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
    old_status = getattr(instance, '_old_status', None)
    if old_status is None:
        return

    # Only process if status actually changed
    if old_status == instance.status:
        return

    recalculate_user_balances(instance.user)

    # Send notification about status change
    notify_order_status_changed(
        user=instance.user,
        order=instance,
        new_status=instance.status,
        amount=float(instance.amount),
    )


def recalculate_user_balances(user: UserProfile) -> tuple[Decimal, Decimal]:
    """
    Recalculate user balances from scratch based on their orders.
    This is useful for data consistency checks or migration.

    Returns:
        Tuple of (pending_balance, withdrawable_balance)
    """
    from withdrawal.models import Withdrawal

    with transaction.atomic():
        locked_user = UserProfile.objects.select_for_update().get(pk=user.pk)

        # Pending = sum of orders currently pending review.
        pending_result = GiftCardOrder.objects.filter(
            user_id=locked_user.pk,
            status__in=PENDING_STATUSES
        ).aggregate(total=Sum('amount'))
        pending_balance = _as_decimal(pending_result['total'] or 0)

        # Gross withdrawable = all approved/completed orders.
        gross_withdrawable_result = GiftCardOrder.objects.filter(
            user_id=locked_user.pk,
            status__in=WITHDRAWABLE_STATUSES
        ).aggregate(total=Sum('amount'))
        gross_withdrawable = _as_decimal(gross_withdrawable_result['total'] or 0)

        # Deduct approved withdrawals to get net withdrawable.
        approved_withdrawals_result = Withdrawal.objects.filter(
            user_id=locked_user.pk,
            status='Approved'
        ).aggregate(total=Sum('amount'))
        approved_withdrawals_total = _as_decimal(approved_withdrawals_result['total'] or 0)

        withdrawable_balance = max(
            Decimal('0.00'),
            gross_withdrawable - approved_withdrawals_total
        )

        locked_user.pending_balance = pending_balance
        locked_user.withdrawable_balance = withdrawable_balance
        locked_user.save(update_fields=['pending_balance', 'withdrawable_balance'])

    return pending_balance, withdrawable_balance


@receiver(post_delete, sender=GiftCardOrder)
def handle_order_deleted(sender, instance, **kwargs):
    """
    Keep balances consistent if an order is deleted.
    """
    recalculate_user_balances(instance.user)
