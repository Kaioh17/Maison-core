"""Cross-tenant isolation suite (directive security-isolation-2026-07, prompt 3).

For every /api/v1 route that accepts a tenant-scoped resource id (driver,
vehicle, booking, rider), authenticate as an actor that legitimately belongs
to tenant A and target a tenant-B resource id instead. A route that isn't
scoped by tenant_id will happily act on tenant B's data -- that's the leak
this suite exists to catch. Every case below expects 403 or 404 (or, for
list/filter endpoints, an empty result); anything else is a finding.

Tenant A is the existing `test_tenant`/`test_driver`/`test_vehicle`/
`test_booking` fixtures from conftest.py (id=1). Tenant B fixtures below
(id=2) are the "other operator".

Routes not covered here are the ones scoped implicitly by the caller's own
JWT (e.g. "get my profile") -- there's no id to substitute, so there's
nothing to isolate-test. Payout data has no direct by-id read/write route
reachable by tenant/driver/rider roles today, so it isn't exercised either.
"""
import pytest
from fastapi import status
from app.api.core.oauth2 import create_access_token
from app.models.tenant import Tenants
from app.models.driver import Drivers
from app.models.user import Users
from app.models.vehicle import Vehicles
from app.models.booking import Bookings
from app.models.ratings import BookingRatings
from app.utils.password_utils import hash

NOT_YOURS = (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


# --- tenant B fixtures ("the other operator") ---------------------------

@pytest.fixture
def test_tenant_b(db_session):
    tenant = Tenants(
        id=2, company_name="Rival Co", email="rival@company.com",
        password=hash("testpassword123"), role="tenant", is_active=True,
        first_name="Rival", last_name="Co", phone_no="+10000000000",
        slug="rivalco", address="1 Rival St", city="Rival City",
        drivers_count=0, is_verified=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_driver_b(db_session, test_tenant_b):
    driver = Drivers(
        id=2, tenant_id=test_tenant_b.id, first_name="Rival", last_name="Driver",
        email="driver@rival.com", phone_no="+10000000001", is_active=True,
        driver_type="standard", completed_rides="0", driver_token="rival_driver_token",
        is_registered="registered", status="available",
    )
    db_session.add(driver)
    db_session.commit()
    db_session.refresh(driver)
    return driver


@pytest.fixture
def test_user_b(db_session, test_tenant_b):
    user = Users(
        id=2, tenant_id=test_tenant_b.id, first_name="Rival", last_name="Rider",
        email="rider@rival.com", phone_no="+10000000002", password="testpassword123",
        role="rider", tier="free",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_vehicle_b(db_session, test_tenant_b, test_driver_b):
    vehicle = Vehicles(
        id=2, tenant_id=test_tenant_b.id, driver_id=test_driver_b.id,
        make="Rival", model="Rival Model", year=2021, license_plate="RIVAL1",
        status="available",
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle


@pytest.fixture
def test_booking_b(db_session, test_tenant_b, test_driver_b, test_user_b):
    booking = Bookings(
        id=2, tenant_id=test_tenant_b.id, driver_id=test_driver_b.id,
        rider_id=test_user_b.id, service_type="standard",
        pickup_location="1 Rival St", pickup_time="2024-01-01T10:00:00",
        dropoff_location="2 Rival Ave", dropoff_time="2024-01-01T11:00:00",
        city="Rival City", booking_status="pending", estimated_price=25.00,
        notes="Rival booking",
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)
    return booking


@pytest.fixture
def booking_rating_b(db_session, test_tenant_b, test_user_b, test_booking_b):
    """A rating that exists for tenant B -- proves scoped code can't see it.

    conftest's autouse cleanup_db doesn't truncate booking_ratings, so this
    fixture cleans up after itself instead of leaking rows across tests.
    """
    rating = BookingRatings(
        tenant_id=test_tenant_b.id, rider_id=test_user_b.id,
        booking_id=test_booking_b.id, rating_value=5.0,
    )
    db_session.add(rating)
    db_session.commit()
    db_session.refresh(rating)
    yield rating
    db_session.query(BookingRatings).filter(BookingRatings.id == rating.id).delete()
    db_session.commit()


@pytest.fixture
def test_vehicle_a_unassigned(db_session, test_tenant):
    """A tenant-A vehicle with no driver -- test_vehicle already has one
    assigned (test_driver), which would trip the "already assigned" guard
    before the assignment code ever reaches the tenant check under test."""
    vehicle = Vehicles(
        id=101, tenant_id=test_tenant.id, driver_id=None,
        make="Toyota", model="Corolla", year=2022, license_plate="FREE001",
        status="available",
    )
    db_session.add(vehicle)
    db_session.commit()
    db_session.refresh(vehicle)
    return vehicle


@pytest.fixture
def driver_b_token(test_driver_b):
    return create_access_token(
        data={"id": str(test_driver_b.id), "role": "driver", "tenant_id": str(test_driver_b.tenant_id)}
    )


@pytest.fixture
def rider_a_token(test_user):
    """Rider on tenant A, correctly-shaped token. conftest's `user_token`
    fixture stamps role="user", which doesn't match oauth2.role_table_map's
    "rider" key and never authenticates -- not reused here for that reason."""
    return create_access_token(
        data={"id": str(test_user.id), "role": "rider", "tenant_id": str(test_user.tenant_id)}
    )


# --- isolation tests ------------------------------------------------------

class TestCrossTenantIsolation:

    # drivers

    def test_driver_cannot_decide_other_tenants_booking(self, client, driver_token, test_booking_b):
        headers = {"Authorization": f"Bearer {driver_token}"}
        resp = client.patch(
            f"/api/v1/driver/ride/{test_booking_b.id}/decision",
            params={"action": "confirmed", "approve_action": True},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    # vehicles

    def test_tenant_cannot_list_other_tenants_vehicle_by_id(self, client, tenant_token, test_vehicle_b):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.get("/api/v1/vehicles", params={"vehicle_id": test_vehicle_b.id}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        ids = [v["id"] for v in resp.json()["data"]]
        assert test_vehicle_b.id not in ids

    def test_tenant_cannot_delete_other_tenants_vehicle(self, client, tenant_token, test_vehicle_b):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.delete(f"/api/v1/vehicles/{test_vehicle_b.id}", headers=headers)
        assert resp.status_code in NOT_YOURS, resp.text

    def test_tenant_cannot_upload_image_to_other_tenants_vehicle(self, client, tenant_token, test_vehicle_b):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.patch(
            f"/api/v1/vehicles/add/image/{test_vehicle_b.id}",
            data={"image_type": ["exterior"]},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    # bookings (rider)

    def test_rider_cannot_approve_other_tenants_booking(self, client, rider_a_token, test_booking_b):
        headers = {"Authorization": f"Bearer {rider_a_token}"}
        resp = client.patch(
            f"/api/v1/bookings/{test_booking_b.id}",
            json={"is_approved": True, "payment_method": "card"},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_rider_cannot_cancel_other_tenants_booking(self, client, rider_a_token, test_booking_b):
        headers = {"Authorization": f"Bearer {rider_a_token}"}
        resp = client.patch(
            f"/api/v1/bookings/rider/{test_booking_b.id}/cancel",
            json={"acknowledge_warning": True},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_rider_cannot_read_other_tenants_booking_rating(self, client, rider_a_token, booking_rating_b):
        headers = {"Authorization": f"Bearer {rider_a_token}"}
        resp = client.get(f"/api/v1/bookings/{booking_rating_b.booking_id}/ratings", headers=headers)
        assert resp.status_code in NOT_YOURS, resp.text

    # tenant-side driver / vehicle assignment

    def test_tenant_cannot_assign_driver_to_other_tenants_booking(
        self, client, tenant_token, test_booking_b, test_driver
    ):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.patch(
            f"/api/v1/tenant/bookings/{test_booking_b.id}/assign-driver",
            json={"driver_id": test_driver.id, "override": True},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_tenant_cannot_assign_other_tenants_driver_to_own_booking(
        self, client, tenant_token, test_booking, test_driver_b
    ):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.patch(
            f"/api/v1/tenant/bookings/{test_booking.id}/assign-driver",
            json={"driver_id": test_driver_b.id},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_tenant_cannot_assign_other_tenants_driver_to_own_vehicle(
        self, client, tenant_token, test_vehicle_a_unassigned, test_driver_b
    ):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.patch(
            f"/api/v1/tenant/vehicles/{test_vehicle_a_unassigned.id}/assign/{test_driver_b.id}",
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_tenant_cannot_unassign_driver_on_other_tenants_vehicle(self, client, tenant_token, test_vehicle_b):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.patch(
            f"/api/v1/tenant/vehicles/{test_vehicle_b.id}/unassign/driver",
            params={"override": True},
            headers=headers,
        )
        assert resp.status_code in NOT_YOURS, resp.text

    def test_tenant_cannot_see_other_tenants_driver_by_id(self, client, tenant_token, test_driver_b):
        headers = {"Authorization": f"Bearer {tenant_token}"}
        resp = client.get("/api/v1/tenant/drivers", params={"driver_id": test_driver_b.id}, headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        ids = [d["id"] for d in resp.json()["data"]]
        assert test_driver_b.id not in ids
