"""Timed booking reminders, sent by email only.

Two kinds, both one-shot per booking (tracked via boolean flags on
`Bookings` so a periodic run never double-sends):

- Ride reminders to the driver: 24h and 1h before pickup, only once the
  booking is `confirmed` and has a driver -- "if applicable".
- Confirm-booking reminders to the tenant (and driver, if one's assigned)
  when a booking is still `pending` as pickup gets close.

Runs outside any request, so it opens its own DB session rather than going
through ServiceContext (which needs a logged-in tenant/driver/rider).
Scheduled via app.celery_app's beat schedule; run_all() is also safe to call
ad hoc (e.g. `python -m app.api.services.reminder_service`).
"""
from datetime import datetime, timedelta, timezone

from app.db.database import SessionLocal
from app.utils.logging import logger
from .helper_service import booking_table, driver_table, tenant_table, tenant_profile, user_table
from .email_services import drivers, tenants

# ponytail: fixed lead times / poll window, not per-tenant configurable --
# add a tenant_settings knob if operators ever ask to tune these.
CONFIRM_REMINDER_HOURS = 6  # nudge to confirm once pickup is this close and still pending
# Must be >= the beat schedule's run interval (see celery_app.py) so two
# consecutive runs always overlap and no booking's reminder window is missed.
POLL_WINDOW_MINUTES = 20


def _slug_and_tenant(db, tenant_id):
    profile = db.query(tenant_profile).filter(tenant_profile.tenant_id == tenant_id).first()
    tenant = db.query(tenant_table).filter(tenant_table.id == tenant_id).first()
    slug = profile.slug if profile else None
    return slug, tenant


def _send_ride_reminders(db, hours_before: int, flag_attr: str):
    now = datetime.now(timezone.utc)
    window_start = now + timedelta(hours=hours_before)
    window_end = window_start + timedelta(minutes=POLL_WINDOW_MINUTES)

    due = (
        db.query(booking_table)
        .filter(
            booking_table.booking_status == "confirmed",
            booking_table.driver_id.isnot(None),
            booking_table.pickup_time >= window_start,
            booking_table.pickup_time < window_end,
            getattr(booking_table, flag_attr).is_(False),
        )
        .all()
    )
    for bk in due:
        driver = db.query(driver_table).filter(driver_table.id == bk.driver_id).first()
        rider = db.query(user_table).filter(user_table.id == bk.rider_id).first()
        slug, _ = _slug_and_tenant(db, bk.tenant_id)
        if not driver or not slug:
            continue
        try:
            drivers.DriverEmailServices(
                to_email=driver.email, from_email="notifications", display_name=slug
            ).ride_reminder_email(
                booking_obj=bk,
                slug=slug,
                hours_before=hours_before,
                rider_name=getattr(rider, "full_name", None),
                rider_phone=getattr(rider, "phone_no", None),
            )
            setattr(bk, flag_attr, True)
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to send {hours_before}h ride reminder for booking {bk.id}")


def _send_confirm_reminders(db):
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=CONFIRM_REMINDER_HOURS)

    due = (
        db.query(booking_table)
        .filter(
            booking_table.booking_status == "pending",
            booking_table.pickup_time >= now,
            booking_table.pickup_time < cutoff,
            booking_table.confirm_reminder_sent.is_(False),
        )
        .all()
    )
    for bk in due:
        slug, tenant = _slug_and_tenant(db, bk.tenant_id)
        rider = db.query(user_table).filter(user_table.id == bk.rider_id).first()
        driver = db.query(driver_table).filter(driver_table.id == bk.driver_id).first() if bk.driver_id else None
        if not slug or not tenant:
            continue
        try:
            tenants.TenantEmailServices(
                to_email=tenant.email, from_email="notifications", display_name=slug
            ).confirm_booking_reminder_email(
                booking_obj=bk,
                tenant_obj=tenant,
                slug=slug,
                rider_name=getattr(rider, "full_name", None),
                driver_name=getattr(driver, "full_name", None) if driver else None,
            )
            if driver:
                drivers.DriverEmailServices(
                    to_email=driver.email, from_email="notifications", display_name=slug
                ).confirm_booking_reminder_email(booking_obj=bk, slug=slug)
            bk.confirm_reminder_sent = True
            db.commit()
        except Exception:
            db.rollback()
            logger.exception(f"Failed to send confirm reminder for booking {bk.id}")


def run_all():
    """One pass over due reminders: 24h + 1h ride reminders, then pending-confirmation nudges."""
    db = SessionLocal()
    try:
        _send_ride_reminders(db, 24, "reminder_24h_sent")
        _send_ride_reminders(db, 1, "reminder_1h_sent")
        _send_confirm_reminders(db)
    finally:
        db.close()


if __name__ == "__main__":
    # Self-check: a pass runs end-to-end against the configured DB without raising.
    run_all()
    print("reminder pass complete")
