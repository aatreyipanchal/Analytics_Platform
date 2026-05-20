from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_routes = {"app.workers.tasks.*": "main-queue"}
celery_app.conf.task_always_eager = settings.CELERY_TASK_ALWAYS_EAGER
celery_app.conf.beat_schedule = {
    "evaluate-alerts-every-minute": {
        "task": "app.workers.tasks.evaluate_alerts_task",
        "schedule": 60.0,
    },
}
celery_app.autodiscover_tasks(["app.workers.tasks"])
