"""Driver pay: earning math, frozen-at-completion ledger, and who may change a payout.

Service-level, in-memory SQLite (same approach as test_driver_deletion): no Postgres, no HTTP.
"""
from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker

from app.api.services.payout_service import PayoutService, driver_earning, pick_rule, ride_net
from app.models import Bookings, Drivers, Payout, Vehicles
from app.models.base import Base
from app.models.tenant import Tenants
from app.models.tenant_setting import TenantSettings
from app.schemas.payout import PayoutUpdate
from app.schemas.tenant_setting import PayRule


@compiles(JSONB, "sqlite")
def _jsonb_as_json(*_a, **_k):
    return "JSON"


# --------------------------------------------------------------------------- pure math

def test_percent_rounds_half_up_per_ride():
    assert driver_earning({"type": "percent", "value": 70}, 200) == 140.0
    assert driver_earning({"type": "percent", "value": 70}, 100.05) == 70.04  # 70.035 -> half up


def test_flat_is_capped_at_the_fare_and_missing_inputs_earn_nothing():
    assert driver_earning({"type": "flat", "value": 25}, 100) == 25.0
    assert driver_earning({"type": "flat", "value": 25}, 10) == 10.0
    assert driver_earning(None, 100) is None
    assert driver_earning({"type": "percent", "value": 70}, None) is None


def test_type_rule_beats_default():
    pay = {"default": {"type": "percent", "value": 70}, "outsourced": {"type": "percent", "value": 75}, "in_house": None}
    assert pick_rule(pay, "outsourced")["value"] == 75
    assert pick_rule(pay, "in_house")["value"] == 70
    assert pick_rule(None, "in_house") is None


def test_cash_nets_the_company_share_against_the_driver():
    # proposal worked example: 70% split, $100 cash ride -> driver keeps $70, owes $30
    assert ride_net(70, 100, "cash") == -30.0
    assert ride_net(140, 200, "card") == 140.0
    assert ride_net(105, 150, "zelle") == 105.0
    assert ride_net(70, 100, None) == 70.0  # unknown method is not assumed to be cash


def test_pay_rule_validation():
    with pytest.raises(ValidationError):
        PayRule(type="percent", value=101)
    with pytest.raises(ValidationError):
        PayRule(type="flat", value=-1)
    assert PayRule(type="flat", value=250).value == 250  # flat dollars may exceed 100


# --------------------------------------------------------------------------- ledger

@pytest.fixture
def db(monkeypatch):
    for t in (Tenants, Vehicles):  # Postgres sequence defaults, unsupported on SQLite
        monkeypatch.setattr(t.__table__.c.id, "server_default", None)
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", lambda c, _: c.create_function("now", 0, lambda: "2024-01-01 00:00:00"))
    Base.metadata.create_all(engine, tables=[
        Tenants.__table__, TenantSettings.__table__, Drivers.__table__, Vehicles.__table__,
        Bookings.__table__, Payout.__table__,
    ])
    s = sessionmaker(bind=engine, expire_on_commit=False)()
    s.add(Tenants(id=1, email="boss@co.com", first_name="B", last_name="Oss", password="x", phone_no="1", role="tenant"))
    s.add(TenantSettings(tenant_id=1, config={}))
    s.add(Drivers(id=1, tenant_id=1, first_name="A", last_name="B", email="a@b.com", driver_type="outsourced",
                  driver_token="t", is_registered="registered"))
    s.add(Drivers(id=2, tenant_id=1, first_name="C", last_name="D", email="c@d.com", driver_type="outsourced",
                  driver_token="t", is_registered="registered"))
    s.commit()
    return s


def _ride(db, id_, fare=200.0, method="card", driver_id=1):
    b = Bookings(id=id_, tenant_id=1, driver_id=driver_id, vehicle_id=1, rider_id=1, service_type="x",
                 pickup_location="p", pickup_time=datetime(2024, 1, 1), estimated_price=fare, payment_method=method,
                 booking_status="completed")
    db.add(b)
    db.commit()
    return b


def _set_rule(db, pct):
    db.get(TenantSettings, 1).config = {"driver_pay": {"default": {"type": "percent", "value": pct}}}
    db.commit()


def _complete(db, booking, driver_id=1):
    PayoutService.record_completion(db, booking, db.get(Drivers, driver_id))
    db.commit()


def test_no_rule_means_no_earning_and_no_payout(db):
    b = _ride(db, 1)
    _complete(db, b)
    assert b.driver_earning is None
    assert db.query(Payout).count() == 0


def test_completion_freezes_earning_and_later_policy_changes_do_not_touch_it(db):
    _set_rule(db, 70)
    old = _ride(db, 1, 200, "card")
    _complete(db, old)
    _set_rule(db, 50)  # tenant changes policy
    new = _ride(db, 2, 100, "cash")
    _complete(db, new)
    assert old.driver_earning == 140.0  # history kept
    assert new.driver_earning == 50.0
    nets = {p.booking_id: p.amount for p in db.query(Payout)}
    assert nets == {1: 140.0, 2: -50.0}
    _complete(db, old)  # replay is a no-op (also guarded by the unique constraint)
    assert db.query(Payout).count() == 2


def test_operator_driving_their_own_ride_earns_nothing(db):
    _set_rule(db, 70)
    db.get(Drivers, 1).email = "BOSS@co.com"
    b = _ride(db, 1)
    _complete(db, b)
    assert b.driver_earning is None and db.query(Payout).count() == 0


def _svc(db, role, uid):
    s = PayoutService.__new__(PayoutService)
    s.db, s.role, s.tenant_id, s.time_now = db, role, 1, datetime(2024, 2, 1)
    s.current_user = SimpleNamespace(id=uid)
    if role == "driver":
        s.driver_id = uid
    return s


def _payout(db, status="pending"):
    _set_rule(db, 70)
    b = _ride(db, 1)
    _complete(db, b)
    p = db.query(Payout).one()
    p.status = status
    db.commit()
    return p


def test_driver_can_verify_only_a_paid_payout_and_must_explain_a_dispute(db):
    p = _payout(db, "pending")
    drv = _svc(db, "driver", 1)
    with pytest.raises(HTTPException) as e:
        drv.update(p.id, PayoutUpdate(status="verified"))
    assert e.value.status_code == 409
    with pytest.raises(HTTPException) as e:
        drv.update(p.id, PayoutUpdate(status="disputed"))
    assert e.value.status_code == 422
    drv.update(p.id, PayoutUpdate(status="disputed", note="Short by $20"))
    assert (p.status, p.status_by_role, p.status_by_id, p.note) == ("disputed", "driver", 1, "Short by $20")
    p.status = "paid"
    drv.update(p.id, PayoutUpdate(status="verified"))
    assert p.status == "verified" and p.status_on is not None


def test_driver_cannot_adjust_set_paid_or_touch_another_drivers_payout(db):
    p = _payout(db)
    with pytest.raises(HTTPException) as e:
        _svc(db, "driver", 1).update(p.id, PayoutUpdate(adjustment=5))
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        _svc(db, "driver", 1).update(p.id, PayoutUpdate(status="paid"))
    assert e.value.status_code == 403
    with pytest.raises(HTTPException) as e:
        _svc(db, "driver", 2).update(p.id, PayoutUpdate(status="disputed", note="x"))
    assert e.value.status_code == 404


def test_tenant_adjusts_only_open_payouts_and_bulk_marks_paid(db):
    p = _payout(db)
    t = _svc(db, "tenant", 1)
    t.update(p.id, PayoutUpdate(adjustment=12.5, note="fuel"))
    assert p.adjustment == 12.5
    t.bulk_update(SimpleNamespace(payout_ids=[p.id], status="paid", note=None))
    assert (p.status, p.status_by_role) == ("paid", "tenant")
    with pytest.raises(HTTPException) as e:  # paid is history
        t.update(p.id, PayoutUpdate(adjustment=1))
    assert e.value.status_code == 409


def test_other_tenants_payouts_are_invisible(db):
    p = _payout(db)
    t = _svc(db, "tenant", 9)
    t.tenant_id = 2
    with pytest.raises(HTTPException) as e:
        t.update(p.id, PayoutUpdate(status="paid"))
    assert e.value.status_code == 404
    assert t.bulk_update(SimpleNamespace(payout_ids=[p.id], status="paid", note=None)).data["updated"] == 0
    assert t.list().data["rows"] == []
