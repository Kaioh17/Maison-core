"""Payouts over HTTP: route wiring, role gates, and that saving settings never erases driver_pay."""
from datetime import datetime, timezone

import pytest

from app.api.services import tenant_settings_service as tss
from app.api.services.payout_service import PayoutService
from app.models.booking import Bookings
from app.models.tenant_setting import TenantSettings
from app.models.payout import Payout
from app.models.vehicle import Vehicles
from tests.test_security_critical import KEY, access, bearer, make_driver, world  # noqa: F401  (world is a fixture)

CONFIG = {
    "booking": {"allow_guest_bookings": True, "show_vehicle_images": False,
                "allowed_payment_method": {"cash": {"is_allowed": True}},
                "types": {"airport": {"is_deposit_required": False}}},
    "branding": {"button_radius": 8, "font_family": "DM Sans"},
    "features": {"vip_profiles": True, "show_loyalty_banner": False},
}


@pytest.fixture
def setup(client, db_session, world, monkeypatch):  # noqa: F811
    monkeypatch.setattr(tss.tenants.TenantEmailServices, "settings_change_email", lambda *a, **k: None)
    db_session.add(TenantSettings(tenant_id=world.tenant.id, config=CONFIG))
    veh = Vehicles(tenant_id=world.tenant.id, make="M", model="X", year=2020, license_plate=f"P{world.n}", status="available")
    db_session.add(veh)
    db_session.commit()
    s = type("S", (), {})()
    s.t = {**KEY, **bearer(access("tenant", world.tenant.id, world.tenant.id))}
    s.driver = make_driver(db_session, world, registered="registered")
    s.other = make_driver(db_session, world, registered="registered")
    s.d = {**KEY, **bearer(access("driver", s.driver.id, world.tenant.id))}
    s.veh, s.world, s.db = veh, world, db_session
    yield s
    db_session.rollback()
    for model in (Payout, Bookings):  # payouts.tenant_id has no cascade, so clear before the tenant goes
        db_session.query(model).filter(model.tenant_id == world.tenant.id).delete()
    db_session.commit()


def _complete_ride(s, id_offset, fare, method):
    b = Bookings(tenant_id=s.world.tenant.id, driver_id=s.driver.id, vehicle_id=s.veh.id, rider_id=s.world.rider.id,
                 service_type="airport", pickup_location="p", pickup_time=datetime(2026, 1, 1 + id_offset, tzinfo=timezone.utc),
                 dropoff_time=datetime(2026, 1, 1 + id_offset, 1, tzinfo=timezone.utc),
                 estimated_price=fare, payment_method=method, booking_status="completed")
    s.db.add(b)
    s.db.commit()
    PayoutService.record_completion(s.db, b, s.driver)
    s.db.commit()
    return b


def test_saving_other_settings_keeps_driver_pay_and_rule_validates(client, setup):
    s = setup
    rule = {"driver_pay": {"default": {"type": "percent", "value": 70}}}
    r = client.patch("/api/v1/tenant/config/settings", json={"config": rule}, headers=s.t)
    assert r.status_code == 202, r.text
    # an unrelated save (the legacy settings page sends only booking/branding/features)
    r = client.patch("/api/v1/tenant/config/settings", json={"config": CONFIG}, headers=s.t)
    assert r.status_code == 202, r.text
    s.db.expire_all()
    cfg = s.db.get(TenantSettings, s.world.tenant.id).config
    assert cfg["driver_pay"]["default"] == {"type": "percent", "value": 70.0}
    assert cfg["booking"]["types"]["airport"] == {"is_deposit_required": False}
    bad = client.patch("/api/v1/tenant/config/settings", json={"config": {"driver_pay": {"default": {"type": "percent", "value": 150}}}}, headers=s.t)
    assert bad.status_code == 422


def test_ledger_roles_and_isolation(client, setup):
    s = setup
    assert client.get("/api/v1/tenant/payouts", headers=s.t).json()["data"] == {"configured": False, "rows": []}
    client.patch("/api/v1/tenant/config/settings", json={"config": {"driver_pay": {"default": {"type": "percent", "value": 70}}}}, headers=s.t)
    _complete_ride(s, 1, 200, "card")
    _complete_ride(s, 2, 100, "cash")

    data = client.get("/api/v1/tenant/payouts", headers=s.t).json()["data"]
    assert data["configured"] is True
    assert [(r["fare"], r["earning"], r["amount"], r["status"]) for r in data["rows"]] == [(100.0, 70.0, -30.0, "pending"), (200.0, 140.0, 140.0, "pending")]

    mine = client.get("/api/v1/driver/payouts", headers=s.d).json()["data"]["rows"]
    assert len(mine) == 2
    other = {**KEY, **bearer(access("driver", s.other.id, s.world.tenant.id))}
    assert client.get("/api/v1/driver/payouts", headers=other).json()["data"]["rows"] == []

    # roles: tenants are not drivers and drivers are not tenants
    assert client.get("/api/v1/driver/payouts", headers=s.t).status_code == 403
    assert client.get("/api/v1/tenant/payouts", headers=s.d).status_code == 406
    assert client.get("/api/v1/tenant/payouts", headers=KEY).status_code == 401

    ids = [r["payout_id"] for r in data["rows"]]
    assert client.post("/api/v1/tenant/payouts/bulk", json={"payout_ids": ids, "status": "paid"}, headers=s.t).json()["data"]["updated"] == 2
    assert client.patch(f"/api/v1/driver/payouts/{ids[0]}", json={"status": "verified"}, headers=other).status_code == 404
    assert client.patch(f"/api/v1/driver/payouts/{ids[0]}", json={"status": "verified"}, headers=s.d).status_code == 202
    row = [r for r in client.get("/api/v1/tenant/payouts", headers=s.t).json()["data"]["rows"] if r["payout_id"] == ids[0]][0]
    assert (row["status"], row["status_by_role"]) == ("verified", "driver") and row["status_on"]
