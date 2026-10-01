"""Driver pay ledger.

The platform records and calculates; it does not move money between operator and driver and is not
the judge of disputes. bookings.driver_earning (frozen at completion) is the source of truth for what
a ride earned, and each payout row carries who changed its status and when.
"""
from decimal import Decimal, ROUND_HALF_UP

from fastapi import Depends, HTTPException, status

from app.db.database import get_db
from app.models.booking import Bookings
from app.models.driver import Drivers
from app.models.payout import Payout
from app.models.tenant_setting import TenantSettings
from ..core import deps
from .helper_service import success_resp
from .service_context import ServiceContext

# Only a rider paying the driver in person leaves the money with the driver. Card, Zelle and
# card-at-pickup are assumed to settle to the company (see the Payouts "make it easier" advice).
DRIVER_HELD_METHODS = {"cash"}
MAX_ROWS = 5000  # ponytail: newest 5000 payout rows; add date-range paging if a tenant outgrows it
DRIVER_STATUSES = {"verified", "disputed"}


def _cents(x) -> Decimal:
    return Decimal(str(x)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def pick_rule(driver_pay: dict | None, driver_type: str | None) -> dict | None:
    """Type rule (in_house / outsourced) beats default. None means no policy is set."""
    if not driver_pay:
        return None
    return driver_pay.get(driver_type or "") or driver_pay.get("default")


def driver_earning(rule: dict | None, fare: float | None) -> float | None:
    if not rule or fare is None:
        return None
    value = Decimal(str(rule["value"]))
    raw = Decimal(str(fare)) * value / 100 if rule["type"] == "percent" else value
    return float(min(_cents(raw), _cents(fare)))  # never more than the rider paid


def ride_net(earning: float, fare: float, payment_method: str | None) -> float:
    """+ = company owes driver, - = driver owes company. Cash: driver keeps their share, hands in the rest."""
    if payment_method in DRIVER_HELD_METHODS:
        return float(_cents(earning) - _cents(fare))
    return float(_cents(earning))


class PayoutService(ServiceContext):
    def __init__(self, db, current_user):
        super().__init__(db=db, current_user=current_user)

    @staticmethod
    def record_completion(db, booking: Bookings, driver: Drivers) -> None:
        """Freeze the driver's earning and open a pending payout. Called once, when a ride completes."""
        if booking.driver_earning is not None:
            return
        cfg = db.query(TenantSettings).filter(TenantSettings.tenant_id == booking.tenant_id).first()
        rule = pick_rule(((cfg.config if cfg else None) or {}).get("driver_pay"), driver.driver_type)
        # An operator driving their own rides (be_driver reuses the tenant's email) pays nobody.
        if driver.email.lower() == (booking.tenant.email or "").lower():
            return
        earning = driver_earning(rule, booking.estimated_price)
        if earning is None:
            return
        booking.driver_earning = earning
        db.add(Payout(
            driving_id=driver.id, booking_id=booking.id, tenant_id=booking.tenant_id,
            amount=ride_net(earning, booking.estimated_price, booking.payment_method),
        ))

    def _configured(self) -> bool:
        cfg = self.db.query(TenantSettings).filter(TenantSettings.tenant_id == self.tenant_id).first()
        return bool(((cfg.config if cfg else None) or {}).get("driver_pay"))

    def list(self, driver_id: int | None = None):
        q = (
            self.db.query(Payout, Bookings, Drivers)
            .join(Bookings, Bookings.id == Payout.booking_id)
            .join(Drivers, Drivers.id == Payout.driving_id)
            .filter(Payout.tenant_id == self.tenant_id)
        )
        if self.role == "driver":
            driver_id = self.driver_id
        if driver_id:
            q = q.filter(Payout.driving_id == driver_id)
        rows = [
            {
                "booking_id": b.id, "payout_id": p.id, "driver_id": d.id,
                "driver_name": f"{d.first_name} {d.last_name}".strip(),
                "pickup_time": b.pickup_time, "fare": b.estimated_price or 0.0,
                "payment_method": b.payment_method, "earning": b.driver_earning or 0.0,
                "amount": p.amount, "adjustment": p.adjustment, "status": p.status,
                "status_by_role": p.status_by_role, "status_on": p.status_on, "note": p.note,
            }
            for p, b, d in q.order_by(Bookings.pickup_time.desc()).limit(MAX_ROWS)
        ]
        return success_resp(data={"configured": self._configured(), "rows": rows})

    def _stamp(self, p: Payout, new_status: str | None, note: str | None):
        if new_status:
            p.status = new_status
        if note is not None:
            p.note = note.strip() or None
        p.status_by_role, p.status_by_id, p.status_on = self.role, self.current_user.id, self.time_now

    def _get(self, payout_id: int) -> Payout:
        q = self.db.query(Payout).filter(Payout.id == payout_id, Payout.tenant_id == self.tenant_id)
        if self.role == "driver":
            q = q.filter(Payout.driving_id == self.driver_id)
        p = q.first()
        if not p:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Payout not found")
        return p

    def update(self, payout_id: int, payload):
        p = self._get(payout_id)
        if self.role == "driver":
            if payload.adjustment is not None or payload.status not in DRIVER_STATUSES:
                raise HTTPException(status.HTTP_403_FORBIDDEN, "Drivers can only verify or dispute a payout")
            if payload.status == "verified" and p.status != "paid":
                raise HTTPException(status.HTTP_409_CONFLICT, "Only a payout marked paid can be verified")
            if payload.status == "disputed" and not (payload.note or "").strip():
                raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Say what is wrong when disputing a payout")
        elif payload.adjustment is not None:
            # Money figures on a paid/verified line are history; reopen it (set pending) to change them.
            if p.status not in ("pending", "disputed"):
                raise HTTPException(status.HTTP_409_CONFLICT, "Reopen the payout before adjusting it")
            p.adjustment = float(_cents(payload.adjustment))
        self._stamp(p, payload.status, payload.note)
        self.db.commit()
        return success_resp(msg="Payout updated", data={"payout_id": p.id, "status": p.status})

    def bulk_update(self, payload):
        rows = self.db.query(Payout).filter(
            Payout.tenant_id == self.tenant_id, Payout.id.in_(payload.payout_ids)
        ).all()
        for p in rows:
            self._stamp(p, payload.status, payload.note)
        self.db.commit()
        return success_resp(msg="Payouts updated", data={"updated": len(rows)})


def get_payout_service(db=Depends(get_db), current_user=Depends(deps.get_current_user)):
    return PayoutService(db=db, current_user=current_user)
