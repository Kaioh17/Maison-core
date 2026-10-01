"""Regression tests for the hardening pass:
per-client rate limits, failure-only login lockout, driver code rationing, public endpoint limits,
upload validation, Stripe Connect webhook ownership checks, dev-only docs.

Every test uses its own fake client IP so Redis-backed limits never leak between tests or runs.
"""
import io
import random
import uuid

import pytest
from fastapi import HTTPException, UploadFile
from fastapi.testclient import TestClient
from PIL import Image
from starlette.requests import Request

from app.api.core.rate_limit import ip_and_path, limiter
from app.api.services.helper_service import MAX_IMAGE_BYTES, read_validated_image
from app.api.services.stripe_services.webhooks import WebhookServices
from app.main import app
from app.models.booking import Bookings
from app.models.vehicle import Vehicles

from .test_security_critical import KEY, PASSWORD, make_driver, no_real_email, world  # noqa: F401 (fixtures)


@pytest.fixture
def ip_client():
    ip = "10.{}.{}.{}".format(*(random.randint(1, 254) for _ in range(3)))
    with TestClient(app, client=(ip, 50000)) as c:
        c.ip = ip
        yield c


def request_from(ip, path="/x"):
    return Request({"type": "http", "client": (ip, 1), "path": path, "headers": [], "method": "GET"})


# --------------------------------------------------------------------------- 6. rate limiting

def test_rate_limit_key_is_per_client_not_a_function_repr():
    a, b = ip_and_path(request_from("1.1.1.1")), ip_and_path(request_from("2.2.2.2"))
    assert a == "1.1.1.1:/x" and b == "2.2.2.2:/x"


def test_one_client_cannot_exhaust_the_limit_for_everyone(ip_client):
    other = TestClient(app, client=("10.250.250.250", 1))
    url = "/api/v1/bookings/public_test"
    codes = [ip_client.get(url).status_code for _ in range(125)]
    assert codes[0] == 200 and codes[-1] == 429
    assert other.get(url).status_code == 200


def test_stripe_webhooks_are_not_ip_rate_limited(ip_client):
    for path in ("/api/v1/webhooks", "/api/v1/webhooks/connect/tenant"):
        codes = {ip_client.post(path, content=b"{}", headers={"stripe-signature": "bad"}).status_code for _ in range(130)}
        assert codes == {400}, path  # rejected on signature, never 429


def test_failed_logins_lock_out_but_successes_never_do(ip_client, world):
    ok = {"username": world.rider.email, "password": PASSWORD}
    for _ in range(8):  # more than MAX_ATTEMPTS successful logins in a row
        assert ip_client.post("/api/v1/auth/login/rider", headers=KEY, data=ok).status_code == 200

    bad = {"username": world.rider.email, "password": "wrong-password"}
    codes = [ip_client.post("/api/v1/auth/login/rider", headers=KEY, data=bad).status_code for _ in range(5)]
    assert codes == [403] * 5
    locked = ip_client.post("/api/v1/auth/login/rider", headers=KEY, data=ok)  # even the right password
    assert locked.status_code == 429 and "Retry-After" in locked.headers


def test_login_lockout_is_per_account_and_ip(ip_client, world):
    bad = {"username": world.rider.email, "password": "wrong-password"}
    for _ in range(5):
        ip_client.post("/api/v1/auth/login/rider", headers=KEY, data=bad)
    elsewhere = TestClient(app, client=("10.251.251.251", 1))
    ok = elsewhere.post("/api/v1/auth/login/rider", headers=KEY, data={"username": world.rider.email, "password": PASSWORD})
    assert ok.status_code == 200


def test_one_ip_spraying_many_accounts_is_locked_out(ip_client):
    codes = [ip_client.post("/api/v1/auth/login/rider", headers=KEY,
                            data={"username": f"nobody{i}@sectests.com", "password": "x"}).status_code for i in range(25)]
    assert codes[:20] == [403] * 20 and codes[20:] == [429] * 5


def test_driver_code_guessing_is_rationed(ip_client, world, db_session):
    make_driver(db_session, world)
    url = f"/api/v1/driver/{world.slug}/verify"
    codes = [ip_client.get(url, params={"token": f"wrong{i}"}, headers=KEY).status_code for i in range(10)]
    assert codes == [409] * 10
    # locked: even the correct code is refused now
    assert ip_client.get(url, params={"token": "Ab3dE9"}, headers=KEY).status_code == 429


def test_driver_code_still_works_for_a_normal_user(ip_client, world, db_session):
    make_driver(db_session, world)
    url = f"/api/v1/driver/{world.slug}/verify"
    assert ip_client.get(url, params={"token": "nope00"}, headers=KEY).status_code == 409
    assert ip_client.get(url, params={"token": "Ab3dE9"}, headers=KEY).status_code == 200


# --------------------------------------------------------------------------- 7. public endpoints

def test_frontend_logs_cannot_forge_entries(ip_client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    body = {"logs": ["hi\n" + "=" * 80 + "\nFrontend Log Entry - 2099\nSECURITY: fake"], "timestamp": "t",
            "userAgent": "ua\nINJECTED", "url": "http://x/\r\nINJECTED2"}
    assert ip_client.post("/logs/frontend", json=body).status_code == 200
    text = (tmp_path / "logs" / "maison_frontend_log").read_text()
    assert text.count("Frontend Log Entry") == 2  # ours + the escaped forged one on the SAME line
    assert "\nINJECTED" not in text and "\nSECURITY: fake" not in text
    assert "\\x0a" in text


def test_frontend_logs_are_bounded(ip_client, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    base = {"timestamp": "t", "userAgent": "ua", "url": "http://x"}
    assert ip_client.post("/logs/frontend", json={**base, "logs": ["a"] * 201}).status_code == 422
    assert ip_client.post("/logs/frontend", json={**base, "logs": ["a" * 2001]}).status_code == 422
    assert ip_client.post("/logs/frontend", json={**base, "logs": ["a"], "userAgent": "u" * 301}).status_code == 422
    assert ip_client.post("/logs/frontend", json=base | {"logs": ["a"]}, headers={"content-length": "999999"}).status_code in (413, 400)
    assert not (tmp_path / "logs" / "maison_frontend_log").exists()


def test_frontend_log_file_rotates_instead_of_growing(ip_client, tmp_path, monkeypatch):
    from app.api.routers import logs
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(logs, "MAX_LOG_FILE_BYTES", 100)
    body = {"logs": ["x" * 50], "timestamp": "t", "userAgent": "ua", "url": "http://x"}
    for _ in range(3):
        assert ip_client.post("/logs/frontend", json=body).status_code == 200
    assert (tmp_path / "logs" / "maison_frontend_log.1").exists()


def test_qr_endpoint_only_encodes_bounded_http_links(ip_client):
    base = "/api/v1/tools/temp-qr/generate"
    ok = ip_client.get(base, params={"url": "https://example.com/a", "fill_color": "#112233", "back_color": "white"})
    assert ok.status_code == 200 and ok.headers["content-type"] == "image/png" and ok.content[:4] == b"\x89PNG"
    assert ip_client.get(base, params={"url": "javascript:alert(1)"}).status_code == 400
    assert ip_client.get(base, params={"url": "https://x.com/" + "a" * 2100}).status_code == 400
    assert ip_client.get(base, params={"url": "https://x.com", "fill_color": "rgb(1,2,3)"}).status_code == 400
    assert ip_client.get("/api/v1/tools/temp-qr/download", params={"url": "ftp://x.com"}).status_code == 400


def test_qr_endpoint_is_rate_limited(ip_client):
    codes = [ip_client.get("/api/v1/tools/temp-qr/generate", params={"url": "https://example.com"}).status_code for _ in range(32)]
    assert codes[0] == 200 and codes[-1] == 429


def png_bytes(size=(4, 4), fmt="PNG"):
    buf = io.BytesIO()
    Image.new("RGB", size, "red").save(buf, fmt)
    return buf.getvalue()


def upload(data, name="logo.png"):
    return UploadFile(file=io.BytesIO(data), filename=name)


@pytest.mark.anyio
async def test_upload_accepts_real_images_and_renames_safely():
    data, name, mime = await read_validated_image(upload(png_bytes(), "../../etc/My Logo!.php"))
    assert mime == "image/png" and name == "My_Logo_.png" and data[:4] == b"\x89PNG"
    _, name, mime = await read_validated_image(upload(png_bytes(fmt="JPEG"), "photo.png"))
    assert (name, mime) == ("photo.jpg", "image/jpeg")  # extension follows the real content, not the client


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [
    b"<html><script>alert(1)</script></html>",
    b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    b"GIF89a-not-really",
    b"",
])
async def test_upload_rejects_non_images(payload):
    with pytest.raises(HTTPException) as e:
        await read_validated_image(upload(payload, "logo.png"))
    assert e.value.status_code == 415


@pytest.mark.anyio
async def test_upload_rejects_oversize():
    with pytest.raises(HTTPException) as e:
        await read_validated_image(upload(png_bytes() + b"0" * (MAX_IMAGE_BYTES + 1)))
    assert e.value.status_code == 413


@pytest.fixture
def anyio_backend():
    return "asyncio"


# --------------------------------------------------------------------------- 8. Connect webhook

@pytest.fixture
def paid_world(world, db_session):
    world.tenant.profile.stripe_account_id = f"acct_{world.n}"
    veh = Vehicles(tenant_id=world.tenant.id, make="Merc", model="S")
    db_session.add(veh)
    db_session.flush()
    from datetime import datetime, timezone
    b = Bookings(tenant_id=world.tenant.id, vehicle_id=veh.id, rider_id=world.rider.id, service_type="dropoff",
                 pickup_location="A", dropoff_location="B", pickup_time=datetime.now(timezone.utc),
                 estimated_price=200.0, payment_status="pending")
    db_session.add(b)
    db_session.commit()
    world.booking, world.acct = b, f"acct_{world.n}"
    return world


def pay_event(w, *, id="pi_1", amount=5000, ptype="deposit", account=None, **meta):
    return {"id": "evt_" + id, "type": "payment_intent.succeeded", "data": {"object": {
        "id": id, "amount": amount, "customer": "cus_1", "payment_method": "pm_1",
        "metadata": {"rider_id": str(w.rider.id), "booking_id": str(w.booking.id), "payment_type": ptype,
                     "tenant_id": str(w.tenant.id), **meta}}}}


def apply(db, event, account):
    WebhookServices(current_user=None, db=db)._handle_payment_succeeded(event, account)


def reload(db, w):
    db.expire_all()
    return db.get(Bookings, w.booking.id)


def test_payment_from_the_owning_account_is_recorded(db_session, paid_world):
    apply(db_session, pay_event(paid_world), paid_world.acct)
    b = reload(db_session, paid_world)
    assert b.payment_status == "deposit_paid" and b.deposit_intent_id == "pi_1" and b.payment_id == "pm_1"


def test_payment_from_another_connected_account_is_ignored(db_session, paid_world):
    apply(db_session, pay_event(paid_world), "acct_someone_else")
    assert reload(db_session, paid_world).payment_status == "pending"
    apply(db_session, pay_event(paid_world), None)
    assert reload(db_session, paid_world).payment_status == "pending"


@pytest.mark.parametrize("amount", [0, -5, 20001, "5000", None])
def test_implausible_amounts_are_ignored(db_session, paid_world, amount):
    apply(db_session, pay_event(paid_world, amount=amount), paid_world.acct)
    assert reload(db_session, paid_world).payment_status == "pending"


def test_tenant_metadata_mismatch_is_ignored(db_session, paid_world):
    apply(db_session, pay_event(paid_world, tenant_id="999999"), paid_world.acct)
    assert reload(db_session, paid_world).payment_status == "pending"


def test_non_maison_payments_are_ignored_quietly(db_session, paid_world):
    ev = pay_event(paid_world)
    ev["data"]["object"]["metadata"] = {}
    apply(db_session, ev, paid_world.acct)
    assert reload(db_session, paid_world).payment_status == "pending"


def test_replay_is_idempotent_and_status_never_goes_backwards(db_session, paid_world):
    apply(db_session, pay_event(paid_world, id="pi_full", amount=20000, ptype="full"), paid_world.acct)
    apply(db_session, pay_event(paid_world, id="pi_full", amount=20000, ptype="full"), paid_world.acct)
    assert reload(db_session, paid_world).payment_status == "full_paid"
    apply(db_session, pay_event(paid_world, id="pi_late_deposit", ptype="deposit"), paid_world.acct)
    assert reload(db_session, paid_world).payment_status == "full_paid"


def test_unknown_booking_is_a_404_so_stripe_retries(db_session, paid_world):
    ev = pay_event(paid_world, booking_id="99999999")
    with pytest.raises(HTTPException) as e:
        apply(db_session, ev, paid_world.acct)
    assert e.value.status_code == 404


def account_event(w, *, acct, obj_id=None, charges=True):
    return {"id": "evt_acc", "type": "account.updated", "data": {"object": {
        "id": obj_id or acct, "charges_enabled": charges, "metadata": {"tenant_id": str(w.tenant.id)}}}}


def handle_account(db, ev, acct):
    WebhookServices(current_user=None, db=db)._handle_account_event(ev, acct)


def test_account_ready_links_the_tenant(db_session, world):
    world.tenant.is_verified = False
    db_session.commit()
    handle_account(db_session, account_event(world, acct="acct_new"), "acct_new")
    db_session.expire_all()
    p = db_session.get(type(world.tenant.profile), world.tenant.id)
    assert p.stripe_account_id == "acct_new" and p.charges_enabled is True
    assert db_session.get(type(world.tenant), world.tenant.id).is_verified is True


def test_account_event_cannot_repoint_a_linked_tenant(db_session, paid_world):
    handle_account(db_session, account_event(paid_world, acct="acct_attacker"), "acct_attacker")
    db_session.expire_all()
    assert db_session.get(type(paid_world.tenant.profile), paid_world.tenant.id).stripe_account_id == paid_world.acct


def test_account_event_with_mismatched_ids_is_ignored(db_session, world):
    handle_account(db_session, account_event(world, acct="acct_a", obj_id="acct_b"), "acct_a")
    db_session.expire_all()
    assert db_session.get(type(world.tenant.profile), world.tenant.id).stripe_account_id is None


# --------------------------------------------------------------------------- 9. infra hardening

def test_api_docs_and_schema_are_dev_only(ip_client, monkeypatch):
    # The test env runs with ENVIRONMENT=development, so docs exist here; assert the switch is wired to it.
    from app import main
    assert main.is_dev == (main.environment.lower() == "development")
    for route in ("/docs", "/redoc", "/openapi.json"):
        assert (ip_client.get(route).status_code == 200) == main.is_dev


def test_cors_allows_only_known_methods_and_headers(ip_client):
    r = ip_client.options("/api/v1/slug/x", headers={"Origin": "http://localhost:3000",
                          "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "x-evil-header"})
    assert r.status_code == 400  # disallowed header
    r = ip_client.options("/api/v1/slug/x", headers={"Origin": "http://localhost:3000",
                          "Access-Control-Request-Method": "TRACE"})
    assert r.status_code == 400
    r = ip_client.options("/api/v1/slug/x", headers={"Origin": "http://localhost:3000",
                          "Access-Control-Request-Method": "POST", "Access-Control-Request-Headers": "authorization,x-api-key,content-type"})
    assert r.status_code == 200


def test_unknown_email_login_still_verifies_a_hash(ip_client, monkeypatch):
    """Unknown accounts must cost a bcrypt verify like wrong passwords (no timing oracle for enumeration)."""
    from app.api.services import auth_service
    calls = []
    real = auth_service.verify
    monkeypatch.setattr(auth_service, "verify", lambda p, h: calls.append(h) or real(p, h))
    r = ip_client.post("/api/v1/auth/login/rider", headers=KEY, data={"username": "ghost@sectests.com", "password": "x"})
    assert r.status_code == 403 and calls == [auth_service._DUMMY_HASH]


def test_api_key_compare_is_constant_time_and_still_works(ip_client):
    assert ip_client.get("/api/v1/admin/tenants", headers={"X-API-Key": "wrong"}).status_code == 403
    assert ip_client.get("/api/v1/admin/tenants", headers=KEY).status_code == 401  # key ok, JWT missing


def test_rate_limited_responses_still_carry_cors_headers(ip_client):
    h = {"Origin": "http://localhost:3000"}
    last = [ip_client.get("/api/v1/bookings/public_test", headers=h) for _ in range(125)][-1]
    assert last.status_code == 429 and last.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert int(last.headers["retry-after"]) >= 1


def test_limiter_fails_open_and_does_not_swallow_app_errors():
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse
    from starlette.routing import Route
    from app.api.core.rate_limit import DefaultRateLimitMiddleware

    calls = []

    async def ok(request):
        calls.append(1)
        return PlainTextResponse("ok")

    async def boom(request):
        calls.append(1)
        raise RuntimeError("app bug")

    class Broken:
        def hit(self, *a):
            raise ConnectionError("redis down")

    mini = Starlette(routes=[Route("/ok", ok), Route("/boom", boom)])
    mini.add_middleware(DefaultRateLimitMiddleware)
    client = TestClient(mini, raise_server_exceptions=False)
    client.get("/ok")  # builds the stack
    layer = mini.middleware_stack
    while layer is not None and not isinstance(layer, DefaultRateLimitMiddleware):
        layer = getattr(layer, "app", None)
    layer.strategy = Broken()

    calls.clear()
    assert client.get("/ok").status_code == 200 and calls == [1]          # Redis down -> request allowed
    calls.clear()
    assert client.get("/boom").status_code == 500 and calls == [1]        # app ran exactly once, error not retried
