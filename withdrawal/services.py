from dataclasses import dataclass
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from account.models import UserProfile
from withdrawal.models import Withdrawal, WithdrawalLimitUsage


LIMIT_COUNTED_STATUSES = ("Pending", "Processing", "Approved", "Completed")


@dataclass(frozen=True)
class WithdrawalLimit:
    level: int
    single_debit_limit: Decimal
    daily_debit_limit: Decimal
    daily_withdrawal_count_limit: int


class WithdrawalLimitService:
    LIMITS = {
        1: WithdrawalLimit(1, Decimal("500000.00"), Decimal("1000000.00"), 3),
        2: WithdrawalLimit(2, Decimal("1000000.00"), Decimal("2000000.00"), 3),
        3: WithdrawalLimit(3, Decimal("5000000.00"), Decimal("15000000.00"), 3),
    }

    @classmethod
    def get_user_level(cls, user: UserProfile) -> int:
        level3_credentials = getattr(user, "level3_credentials", None)
        if (
            user.level == "Level 3"
            and level3_credentials
            and level3_credentials.approved
            and level3_credentials.status == "Approved"
        ):
            return 3

        level2_credentials = getattr(user, "level2_credentials", None)
        if (
            user.level in ("Level 2", "Level 3")
            and level2_credentials
            and level2_credentials.approved
            and level2_credentials.status == "Approved"
        ):
            return 2

        if user.is_verified and user.phone_number:
            return 1

        return 0

    @classmethod
    def get_limit_for_user(cls, user: UserProfile) -> WithdrawalLimit:
        level = cls.get_user_level(user)
        if level == 0:
            raise ValidationError({
                "detail": "Complete email and phone verification before making withdrawals."
            })
        return cls.LIMITS[level]

    @classmethod
    def get_today_usage(cls, user: UserProfile) -> tuple[Decimal, int]:
        today = timezone.localdate()
        result = Withdrawal.objects.filter(
            user=user,
            status__in=LIMIT_COUNTED_STATUSES,
            created_at__date=today,
        ).aggregate(total=Sum("amount"))
        total_amount = Decimal(str(result["total"] or "0.00"))
        total_count = Withdrawal.objects.filter(
            user=user,
            status__in=LIMIT_COUNTED_STATUSES,
            created_at__date=today,
        ).count()
        return total_amount, total_count

    @classmethod
    def validate_withdrawal(cls, user: UserProfile, amount: Decimal) -> WithdrawalLimit:
        limit = cls.get_limit_for_user(user)
        amount = Decimal(str(amount))

        if amount > limit.single_debit_limit:
            raise ValidationError({
                "amount": [(
                    f"Your single withdrawal limit is ₦{limit.single_debit_limit:,.2f} "
                    f"for Level {limit.level} verification."
                )]
            })

        today_total, today_count = cls.get_today_usage(user)
        if today_total + amount > limit.daily_debit_limit:
            raise ValidationError({"amount": ["You have exceeded your daily withdrawal limit."]})

        if today_count + 1 > limit.daily_withdrawal_count_limit:
            raise ValidationError({
                "detail": "You have reached the maximum number of withdrawals allowed today."
            })

        return limit

    @classmethod
    def refresh_usage_for_user(cls, user: UserProfile, date=None) -> WithdrawalLimitUsage:
        usage_date = date or timezone.localdate()
        result = Withdrawal.objects.filter(
            user=user,
            status__in=LIMIT_COUNTED_STATUSES,
            created_at__date=usage_date,
        ).aggregate(total=Sum("amount"))
        total_amount = Decimal(str(result["total"] or "0.00"))
        total_count = Withdrawal.objects.filter(
            user=user,
            status__in=LIMIT_COUNTED_STATUSES,
            created_at__date=usage_date,
        ).count()

        with transaction.atomic():
            usage, _ = WithdrawalLimitUsage.objects.update_or_create(
                user=user,
                date=usage_date,
                defaults={
                    "total_amount": total_amount,
                    "total_count": total_count,
                },
            )
        return usage
