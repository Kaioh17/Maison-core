"""Regression tests for the critical security fixes:
admin role gate, password verify, typed/revocable JWTs, driver onboarding session.

Self-contained: builds its own tenant/admin/rider/driver rows (unique per test) in the test DB.
"""
import uuid
from datetime import datetime, timedelta

import pytest
from fastapi import HTTPException
from jose import jwt

from app.api.core import oauth2
from app.api.routers.dependencies import API_KEY
from app.models.admin import Admin
from app.models.driver import Drivers
from app.models.tenant import Tenants, TenantProfile, TenantStats
from app.models.user import Users
from app.utils.password_utils import hash, verify

KEY = {"X-API-Key": API_KEY}
PASSWORD = "Sup3rSecret!"


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


def access(role, id_, tenant_id):
    return oauth2.create_access_token({"id": str(id_), "role": role, "tenant_id": str(tenant_id)})


@pytest.fixture
def world(db_session):
    n = uuid.uuid4().hex[:8]
    tenant = Tenants(email=f"t{n}@sectests.com", first_name="T", last_name="Enant", password=hash(PASSWORD),
                     phone_no="+15550000000", role="tenant", is_verified=True)
    db_session.add(tenant)
    db_session.flush()
    db_session.add_all([
        TenantProfile(tenant_id=tenant.id, company_name=f"Co {n}", slug=f"co-{n}", city="Testville"),
        TenantStats(tenant_id=tenant.id, drivers_count=0),
    ])
    admin = Admin(first_name="A", last_name="Dmin", email=f"a{n}@sectests.com", password=hash(PASSWORD))
    rider = Users(tenant_id=tenant.id, email=f"r{n}@sectests.com", first_name="R", last_name="Ider",
                  password=hash(PASSWORD), role="rider", phone_no="+15557654321")
    db_session.add_all([admin, rider])
    db_session.commit()
    w = type("W", (), {})()
    w.n, w.tenant, w.admin, w.rider, w.slug = n, tenant, admin, rider, f"co-{n}"
    yield w
    db_session.rollback()
    db_session.query(Admin).filter(Admin.id == admin.id).delete()
    db_session.delete(db_session.get(Tenants, tenant.id))  # cascades profile/stats/users/drivers
    db_session.commit()


def make_driver(db_session, w, *, token="Ab3dE9", driver_type="in_house", registered="pending"):
    d = Drivers(tenant_id=w.tenant.id, email=f"d{uuid.uuid4().hex[:6]}@sectests.com", first_name="Dri", last_name="Ver",
                driver_type=driver_type, driver_token=token, is_registered=registered, is_active=False,
                is_token=False, role="driver", completed_rides=0)
    db_session.add(d)
    db_session.commit()
    return d


# --------------------------------------------------------------------------- 1. admin gate

ADMIN_READS = ["/api/v1/admin/tenants", "/api/v1/admin/logs", "/api/v1/admin/tenants/1"]


@pytest.mark.parametrize("path", ADMIN_READS)
def test_non_admin_roles_cannot_use_admin_api(client, world, path):
    for role, id_ in (("tenant", world.tenant.id), ("rider", world.rider.id)):
        r = client.get(path, headers={**KEY, **bearer(access(role, id_, world.tenant.id))})
        assert r.status_code == 403, (role, path, r.text)


def test_admin_api_needs_a_jwt_not_just_the_public_key(client, world):
    assert client.get("/api/v1/admin/tenants", headers=KEY).status_code == 401
    body = {"email": f"x{world.n}@sectests.com", "first_name": "X", "last_name": "Y", "password": "longenough1"}
    assert client.post("/api/v1/admin/", json=body, headers=KEY).status_code == 401
    rider = bearer(access("rider", world.rider.id, world.tenant.id))
    assert client.post("/api/v1/admin/", json=body, headers={**KEY, **rider}).status_code == 403
    assert client.delete(f"/api/v1/admin/delete/{world.tenant.id}/tenant", headers={**KEY, **rider}).status_code == 403


def test_admin_api_still_works_for_admins(client, world, db_session):
    h = {**KEY, **bearer(access("admin", world.admin.id, "not tennat"))}
    assert client.get("/api/v1/admin/tenants", headers=h).status_code == 200
    body = {"email": f"new{world.n}@sectests.com", "first_name": "N", "last_name": "Ew", "password": "longenough1"}
    assert client.post("/api/v1/admin/", json=body, headers=h).status_code == 201
    db_session.query(Admin).filter(Admin.email == body["email"]).delete()
    db_session.commit()


def test_admin_password_must_be_at_least_8_chars(client, world):
    h = {**KEY, **bearer(access("admin", world.admin.id, "not tennat"))}
    body = {"email": f"s{world.n}@sectests.com", "first_name": "N", "last_name": "Ew", "password": "short"}
    assert client.post("/api/v1/admin/", json=body, headers=h).status_code == 422


# --------------------------------------------------------------------------- 3. password verify

def test_stored_hash_is_not_a_password():
    h = hash(PASSWORD)
    assert verify(PASSWORD, h)
    assert not verify(h, h)  # pass-the-hash
    assert not verify("wrong-password", h)


def test_missing_or_garbage_hash_fails_closed():
    assert not verify(PASSWORD, None)
    assert not verify(PASSWORD, "")
    assert not verify(PASSWORD, "not-a-bcrypt-hash")


def test_login_rejects_the_hash_as_password(client, world):
    r = client.post("/api/v1/auth/login/rider", headers=KEY,
                    data={"username": world.rider.email, "password": world.rider.password})
    assert r.status_code == 403
    ok = client.post("/api/v1/auth/login/rider", headers=KEY, data={"username": world.rider.email, "password": PASSWORD})
    assert ok.status_code == 200 and "access_token" in ok.json()


# --------------------------------------------------------------------------- 5. token hygiene

def login_cookie(client, world):
    r = client.post("/api/v1/auth/login/rider", headers=KEY, data={"username": world.rider.email, "password": PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()["access_token"], r.cookies.get("refresh_token")


def test_refresh_token_cannot_be_used_as_access_token(client, world):
    access_tok, refresh_tok = login_cookie(client, world)
    assert client.get("/api/v1/users/", headers=bearer(access_tok)).status_code == 200
    assert client.get("/api/v1/users/", headers=bearer(refresh_tok)).status_code == 401


def test_access_token_cannot_be_used_to_refresh(client, world):
    access_tok, _ = login_cookie(client, world)
    r = client.post("/api/v1/auth/refresh/manual", headers={**KEY, "Cookie": f"refresh_token={access_tok}"})
    assert r.status_code == 401


def test_untyped_and_non_expiring_tokens_are_rejected(client, world):
    claims = {"id": str(world.rider.id), "role": "rider", "tenant_id": str(world.tenant.id)}
    old_style = jwt.encode({**claims, "exp": datetime.utcnow() + timedelta(hours=1)}, oauth2.SECRET_KEY, oauth2.ALGORITHM)
    no_exp = jwt.encode({**claims, "type": "access"}, oauth2.SECRET_KEY, oauth2.ALGORITHM)
    for tok in (old_style, no_exp):
        assert client.get("/api/v1/users/", headers=bearer(tok)).status_code == 401


def test_logout_revokes_the_refresh_token(client, world):
    _, refresh_tok = login_cookie(client, world)
    cookie = {"Cookie": f"refresh_token={refresh_tok}"}
    assert client.post("/api/v1/auth/refresh", headers={**KEY, **cookie}).status_code == 200
    assert client.post("/api/v1/auth/logout", headers={**KEY, **cookie}).status_code == 200
    assert client.post("/api/v1/auth/refresh", headers={**KEY, **cookie}).status_code == 401
    assert client.post("/api/v1/auth/refresh/manual", headers={**KEY, **cookie}).status_code == 401


def test_refresh_without_tracked_jti_is_rejected(client, world):
    forged = jwt.encode({"id": str(world.rider.id), "role": "rider", "tenant_id": str(world.tenant.id),
                         "auto_refresh": True, "type": "refresh", "jti": "never-issued",
                         "exp": datetime.utcnow() + timedelta(days=1)}, oauth2.SECRET_KEY, oauth2.ALGORITHM)
    r = client.post("/api/v1/auth/refresh", headers={**KEY, "Cookie": f"refresh_token={forged}"})
    assert r.status_code == 401


# --------------------------------------------------------------------------- 4. driver onboarding

@pytest.fixture(autouse=True)
def no_real_email(monkeypatch):
    from app.api.services import driver_service

    class Mail:
        def __init__(self, *a, **k): ...
        def __getattr__(self, name):
            return lambda *a, **k: None

    monkeypatch.setattr(driver_service.drivers, "DriverEmailServices", Mail)


def reg_body(d, **over):
    return {"email": d.email, "first_name": "Dri", "last_name": "Ver", "phone_no": "+15551234567",
            "license_number": f"LIC{uuid.uuid4().hex[:6]}", "password": "Passw0rd!x", **over}


def verify_code(client, w, token):
    return client.get(f"/api/v1/driver/{w.slug}/verify", params={"token": token}, headers=KEY)


def test_register_requires_an_onboarding_session(client, world, db_session):
    d = make_driver(db_session, world)
    # exactly what the attacker knew before the fix: tenant id, name, email. No code.
    r = client.patch("/api/v1/driver/register", params={"tenant_id": world.tenant.id}, json=reg_body(d))
    assert r.status_code == 401
    db_session.refresh(d)
    assert d.password is None and d.is_registered == "pending"
    # tokens of other kinds are not onboarding sessions
    for tok in (access("rider", world.rider.id, world.tenant.id), access("driver", d.id, world.tenant.id)):
        assert client.patch("/api/v1/driver/register", json=reg_body(d), headers=bearer(tok)).status_code == 401


def test_blank_code_never_matches_an_unapproved_application(client, world, db_session):
    d = make_driver(db_session, world, token="")  # applied, not approved yet
    assert verify_code(client, world, "").status_code == 409
    assert verify_code(client, world, "   ").status_code == 409
    assert verify_code(client, world, "wrong1").status_code == 409
    db_session.refresh(d)
    assert d.is_token is False


def test_unknown_slug_is_a_clean_failure(client, world):
    r = client.get("/api/v1/driver/no-such-slug/verify", params={"token": "Ab3dE9"}, headers=KEY)
    assert r.status_code == 409


def test_full_onboarding_flow_activates_the_driver(client, world, db_session):
    d = make_driver(db_session, world)
    # cannot sign in before finishing onboarding (no password yet)
    assert client.post("/api/v1/auth/login/driver", headers=KEY,
                       data={"username": d.email, "password": "Passw0rd!x"}).status_code == 403

    v = verify_code(client, world, "Ab3dE9")
    assert v.status_code == 200, v.text
    data = v.json()["data"]
    assert data["email"] == d.email and data["onboarding_token"]
    assert [t["key"] for t in data["tasks"]] == ["profile", "password"]
    assert not any(t["done"] for t in data["tasks"])
    session = bearer(data["onboarding_token"])

    # the session is not a login: it cannot reach authenticated routes
    assert client.get("/api/v1/driver/info", headers=session).status_code == 401
    # progress endpoint works with the session
    assert client.get("/api/v1/driver/onboarding", headers=session).status_code == 200
    assert client.get("/api/v1/driver/onboarding").status_code == 401

    # a different email than the invited one is refused
    bad = client.patch("/api/v1/driver/register", json=reg_body(d, email="someone.else@sectests.com"), headers=session)
    assert bad.status_code == 404

    ok = client.patch("/api/v1/driver/register", json=reg_body(d), headers=session)
    assert ok.status_code == 202, ok.text
    db_session.refresh(d)
    assert d.is_registered == "registered" and d.is_active is True and d.is_token is True
    assert d.password and d.password != "Passw0rd!x"

    # the code and the session are single use
    assert client.patch("/api/v1/driver/register", json=reg_body(d), headers=session).status_code == 401
    assert verify_code(client, world, "Ab3dE9").status_code == 409

    # and the driver can now sign in
    login = client.post("/api/v1/auth/login/driver", headers=KEY, data={"username": d.email, "password": "Passw0rd!x"})
    assert login.status_code == 200, login.text


def test_reissued_code_invalidates_old_sessions(client, world, db_session):
    d = make_driver(db_session, world)
    session = bearer(verify_code(client, world, "Ab3dE9").json()["data"]["onboarding_token"])
    d.driver_token = "NewC0de"  # tenant re-approves / re-invites
    db_session.commit()
    assert client.patch("/api/v1/driver/register", json=reg_body(d), headers=session).status_code == 401


def test_outsourced_driver_must_register_a_vehicle(client, world, db_session):
    d = make_driver(db_session, world, driver_type="outsourced")
    v = verify_code(client, world, "Ab3dE9").json()["data"]
    assert [t["key"] for t in v["tasks"]] == ["profile", "password", "vehicle"]
    r = client.patch("/api/v1/driver/register", json=reg_body(d), headers=bearer(v["onboarding_token"]))
    assert r.status_code == 406
    db_session.refresh(d)
    assert d.is_registered == "pending" and d.password is None


def test_onboarding_session_cannot_be_forged_for_another_driver(client, world, db_session):
    victim = make_driver(db_session, world)
    forged = jwt.encode({"type": "driver_onboarding", "id": str(victim.id), "tenant_id": str(world.tenant.id),
                         "tk": "0" * 16, "exp": datetime.utcnow() + timedelta(hours=1)}, "wrong-key", oauth2.ALGORITHM)
    assert client.patch("/api/v1/driver/register", json=reg_body(victim), headers=bearer(forged)).status_code == 401
    right_key = jwt.encode({"type": "driver_onboarding", "id": str(victim.id), "tenant_id": str(world.tenant.id),
                            "tk": "0" * 16, "exp": datetime.utcnow() + timedelta(hours=1)}, oauth2.SECRET_KEY, oauth2.ALGORITHM)
    # validly signed but bound to a code fingerprint that does not match the driver's code
    assert client.patch("/api/v1/driver/register", json=reg_body(victim), headers=bearer(right_key)).status_code == 401


def test_onboarding_token_helper_rejects_wrong_type():
    with pytest.raises(HTTPException) as e:
        oauth2.verify_driver_onboarding_token(oauth2.create_access_token({"id": "1", "role": "driver"}))
    assert e.value.status_code == 401
