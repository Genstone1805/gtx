from django_celery_beat.models import PeriodicTask, IntervalSchedule
from celery import shared_task
import logging

logger = logging.getLogger("__name__")


schedule, created = IntervalSchedule.objects.get_or_create(
  every=10,
  period = IntervalSchedule.SECONDS
)

PeriodicTask.objects.update_or_create(
  interval=schedule,
  name="test task",
  task = "account.tasks.periodictask"
)