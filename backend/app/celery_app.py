"""Celery app for periodic background jobs. Reuses the existing Redis
instance (already in docker-compose for rate limiting) as broker + result
backend, so no new infra beyond a worker + beat process.

Run locally:
    celery -A app.celery_app worker --beat --loglevel=info
In Docker, the `worker` and `beat` services in docker-compose.yml run this.
"""
from celery import Celery
from celery.schedules import crontab

from app.config import Settings

settings = Settings()

celery_app = Celery("maison", broker=settings.redis_url, backend=settings.redis_url)

# Must run at least as often as reminder_service.POLL_WINDOW_MINUTES so
# consecutive runs overlap and no booking's reminder window is missed.
celery_app.conf.beat_schedule = {
    "send-booking-reminders": {
        "task": "app.tasks.send_booking_reminders",
        "schedule": crontab(minute="*/15"),
    },
}
celery_app.conf.timezone = "UTC"

# Registers the @celery_app.task below with this app.
import app.tasks  # noqa: E402,F401
