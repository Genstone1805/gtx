import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

from withdrawal.services import WithdrawalLimitService


logger = logging.getLogger(__name__)


@shared_task(name="withdrawal.tasks.refresh_daily_withdrawal_limits")
def refresh_daily_withdrawal_limits():
    usage_date = timezone.localdate()
    User = get_user_model()
    refreshed = 0

    for user in User.objects.all().iterator():
        WithdrawalLimitService.refresh_usage_for_user(user, date=usage_date)
        refreshed += 1

    logger.info("Refreshed withdrawal limit usage for %s users on %s", refreshed, usage_date)
    return {"date": str(usage_date), "refreshed": refreshed}
