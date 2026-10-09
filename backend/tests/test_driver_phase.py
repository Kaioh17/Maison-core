"""Driver nav app preference and en-route/arrived stamping over HTTP."""
from datetime import datetime, timedelta, timezone

import pytest

from app.models.booking import Bookings
from app.models.vehicle import Vehicles
from tests.test_security_critical import KEY, access, bearer, make_driver, world  # noqa: F401  (world is a fixture)


@pytest.fixture
def setup(client, db_session, world):  # noqa: F811
    veh = Vehicles(tenant_id=world.tenant.id, make="M", model="X", year=2020, license_plate=f"P{world.n}", status="available")
    db_session.add(veh)
    db_session.commit()
    s = type("S", (), {})()
    s.driver = make_driver(db_session, world, registered="registered")
    s.d = {**KEY, **bearer(access("driver", s.driver.id, world.tenant.id))}
    s.veh, s.world, s.db, s.n = veh, world, db_session, 0
    yield s
    db_session.rollback()
    db_session.query(Bookings).filter(Bookings.tenant_id == world.tenant.id).delete()
    db_session.commit()


def _ride(s, status="confirmed", mine=True):
    s.n += 1
    b = Bookings(tenant_id=s.world.tenant.id, driver_id=s.driver.id if mine else None, vehicle_id=s.veh.id,
                 rider_id=s.world.rider.id, service_type="dropoff", pickup_location="1 Main St",
                 pickup_time=datetime.now(timezone.utc) + timedelta(hours=s.n), dropoff_location="2 Oak Ave",
                 dropoff_time=datetime.now(timezone.utc) + timedelta(hours=s.n + 1),
                 booking_status=status, estimated_price=50.0)
    s.db.add(b)
    s.db.commit()
    return b


def test_nav_app_saved_and_validated(client, setup):
    s = setup
    assert client.patch("/api/v1/driver/nav-app", params={"nav_app": "waze"}, headers=s.d).status_code == 200
    assert client.get("/api/v1/driver/info", headers=s.d).json()["data"]["nav_app"] == "waze"
    assert client.patch("/api/v1/driver/nav-app", params={"nav_app": "bing"}, headers=s.d).status_code == 422


def test_phase_stamps_once_and_never_goes_back(client, setup):
    s = setup
    ride = _ride(s)
    url = f"/api/v1/driver/ride/{ride.id}/phase"
    assert client.patch(url, params={"phase": "enroute"}, headers=s.d).status_code == 200
    s.db.refresh(ride)
    started = ride.driver_started_at
    assert started and ride.driver_arrived_at is None
    assert client.patch(url, params={"phase": "arrived"}, headers=s.d).status_code == 200
    assert client.patch(url, params={"phase": "enroute"}, headers=s.d).status_code == 200
    s.db.refresh(ride)
    assert ride.driver_started_at == started and ride.driver_arrived_at is not None
    assert client.patch(url, params={"phase": "flying"}, headers=s.d).status_code == 422


def test_phase_rejects_pending_and_unassigned_rides(client, setup):
    s = setup
    pending, theirs = _ride(s, status="pending"), _ride(s, mine=False)
    assert client.patch(f"/api/v1/driver/ride/{pending.id}/phase", params={"phase": "enroute"}, headers=s.d).status_code == 409
    assert client.patch(f"/api/v1/driver/ride/{theirs.id}/phase", params={"phase": "enroute"}, headers=s.d).status_code == 404
