"""Demo tenant is read-only via one app-level dependency; real tenants and auth endpoints are untouched."""
import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from app.api.core import demo_guard
from app.api.core.oauth2 import create_access_token


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(demo_guard.settings, "demo_tenant_slug", "demo-slug")
    monkeypatch.setattr(demo_guard, "_get_demo_tenant_id", lambda: "7")
    app = FastAPI(dependencies=[Depends(demo_guard.block_demo_writes)])
    for method in ("get", "post", "delete"):
        getattr(app, method)("/api/v1/things")(lambda: {"ok": True})
    app.post("/api/v1/auth/login/tenant")(lambda: {"ok": True})
    app.post("/api/v1/users/add/{slug}")(lambda slug: {"ok": True})
    router = APIRouter(prefix="/api/v1/tenant")  # real routers are mounted via include_router
    router.patch("/settings")(lambda: {"ok": True})
    app.include_router(router)
    return TestClient(app)


def _bearer(role, id_, tenant_id):
    return {"Authorization": "Bearer " + create_access_token({"id": str(id_), "role": role, "tenant_id": str(tenant_id)})}


def test_demo_writes_blocked_everywhere(client):
    assert client.post("/api/v1/things", headers=_bearer("tenant", 7, 7)).status_code == 403
    assert client.delete("/api/v1/things", headers=_bearer("driver", 99, 7)).status_code == 403  # demo driver
    assert client.patch("/api/v1/tenant/settings", headers=_bearer("tenant", 7, 7)).status_code == 403  # included router
    assert client.post("/api/v1/users/add/demo-slug").status_code == 403  # slug in path
    assert client.post("/api/v1/things", headers={"X-Tenant-Slug": "demo-slug"}).status_code == 403


def test_reads_auth_and_other_tenants_allowed(client):
    assert client.get("/api/v1/things", headers=_bearer("tenant", 7, 7)).status_code == 200
    assert client.post("/api/v1/auth/login/tenant", headers=_bearer("tenant", 7, 7)).status_code == 200
    assert client.post("/api/v1/things", headers=_bearer("tenant", 8, 8)).status_code == 200
    assert client.post("/api/v1/users/add/other").status_code == 200
    assert client.post("/api/v1/things", headers={"Authorization": "Bearer junk"}).status_code == 200  # route auth rejects, not us
