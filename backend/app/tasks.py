from app.celery_app import celery_app
from app.api.services.reminder_service import run_all


@celery_app.task(name="app.tasks.send_booking_reminders")
def send_booking_reminders():
    run_all()
