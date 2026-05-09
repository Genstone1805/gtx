from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone

from account.models import ReferralCommission, UserProfile
from order.models import GiftCardOrder


SUCCESSFUL_ORDER_STATUSES = {"Approved", "Completed"}
REFERRAL_COMMISSION_PAID_STATUS = "Paid"


def get_referral_qualifying_amount() -> Decimal:
    return Decimal(str(getattr(settings, "REFERRAL_QUALIFYING_AMOUNT", "100.00")))


def get_referral_commission_percent() -> Decimal:
    return Decimal(str(getattr(settings, "REFERRAL_COMMISSION_PERCENT", "10.00")))


def calculate_referral_commission(amount: Decimal | int) -> Decimal:
    percentage = get_referral_commission_percent()
    raw_amount = Decimal(str(amount)) * percentage / Decimal("100")
    return raw_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def process_referral_commission_for_order(order: GiftCardOrder) -> ReferralCommission | None:
    if order.status not in SUCCESSFUL_ORDER_STATUSES:
        return None

    with transaction.atomic():
        referred_user = UserProfile.objects.select_for_update().get(pk=order.user_id)
        referrer = referred_user.referred_by
        if not referrer or referrer_id_matches(referrer, referred_user):
            return None

        referrer = UserProfile.objects.select_for_update().get(pk=referrer.pk)

        if ReferralCommission.objects.filter(
            referrer=referrer,
            referred_user=referred_user,
        ).exists():
            return None

        total_successful = GiftCardOrder.objects.filter(
            user=referred_user,
            status__in=SUCCESSFUL_ORDER_STATUSES,
        ).aggregate(total=Sum("amount"))["total"] or 0

        qualifying_amount = get_referral_qualifying_amount()
        if Decimal(str(total_successful)) < qualifying_amount:
            return None

        commission_amount = calculate_referral_commission(order.amount)
        try:
            commission = ReferralCommission.objects.create(
                referrer=referrer,
                referred_user=referred_user,
                qualifying_transaction=order,
                amount=commission_amount,
                percentage=get_referral_commission_percent(),
                status=REFERRAL_COMMISSION_PAID_STATUS,
                paid_at=timezone.now(),
                metadata={
                    "qualifying_total": str(total_successful),
                    "threshold": str(qualifying_amount),
                },
            )
        except IntegrityError:
            return None

    from order.signals import recalculate_user_balances

    recalculate_user_balances(referrer)
    return commission


def referrer_id_matches(referrer: UserProfile, referred_user: UserProfile) -> bool:
    return referrer.pk is not None and referrer.pk == referred_user.pk
