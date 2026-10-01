"""Two-step driver deletion: service-level check with in-memory SQLite and a fake Redis (no DB schema change)."""
import asyncio
from datetime import datetime
import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine, event
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from app.api.services import tenants_service as ts
from app.models.base import Base
from app.models import Drivers, Vehicles, Bookings, Payout
from app.schemas.driver import DriverDeleteConfirm


@compiles(JSONB, "sqlite")
def _jsonb_as_json(*_a, **_k):
    return "JSON"


class FakeRedis(dict):
    def set(self, k, v, ex=None): self[k] = v.encode()
    def delete(self, k): self.pop(k, None)


@pytest.fixture
def svc(monkeypatch):
    monkeypatch.setattr(Vehicles.__table__.c.id, "server_default", None)  # Postgres sequence default, unsupported on SQLite
    engine = create_engine("sqlite://")
    event.listen(engine, "connect", lambda c, _: c.create_function("now", 0, lambda: "2024-01-01 00:00:00"))
    Base.metadata.create_all(engine, tables=[Drivers.__table__, Vehicles.__table__, Bookings.__table__, Payout.__table__])
    db = sessionmaker(bind=engine)()
    monkeypatch.setattr(ts, "redis_client", FakeRedis())
    s = ts.TenantService.__new__(ts.TenantService)  # skip ServiceContext: needs a full tenant row
    s.db, s.tenant_id = db, 1
    return s


def _driver(db, **kw):
    d = Drivers(id=1, tenant_id=1, first_name="A", last_name="B", email="a@b.com", driver_type="outsourced",
                driver_token="t", is_registered="registered", **kw)
    db.add(d); db.commit()
    return d


def _confirm(token, email="a@b.com", ack=True):
    return DriverDeleteConfirm(confirmation_token=token, confirm_email=email, acknowledge_permanent=ack)


def test_two_step_delete(svc):
    d = _driver(svc.db)
    with pytest.raises(ValidationError):
        _confirm("x", ack=False)  # permanence flag is mandatory

    token = asyncio.run(svc.request_driver_deletion(d.id)).data["confirmation_token"]
    with pytest.raises(HTTPException) as e:
        asyncio.run(svc.delete_driver(d.id, _confirm("wrong")))
    assert e.value.status_code == 400
    with pytest.raises(HTTPException) as e:
        asyncio.run(svc.delete_driver(d.id, _confirm(token, email="other@b.com")))
    assert e.value.status_code == 400
    assert svc.db.get(Drivers, d.id)  # still there

    asyncio.run(svc.delete_driver(d.id, _confirm(token)))
    assert svc.db.get(Drivers, d.id) is None
    with pytest.raises(HTTPException):  # token is single use
        asyncio.run(svc.delete_driver(d.id, _confirm(token)))


def test_other_tenant_and_history_blocked(svc):
    d = _driver(svc.db)
    svc.tenant_id = 2
    with pytest.raises(HTTPException) as e:
        asyncio.run(svc.request_driver_deletion(d.id))
    assert e.value.status_code == 404

    svc.tenant_id = 1
    svc.db.add(Bookings(id=1, tenant_id=1, driver_id=d.id, vehicle_id=1, rider_id=1, service_type="x",
                        pickup_location="p", pickup_time=datetime(2024, 1, 1)))
    svc.db.commit()
    with pytest.raises(HTTPException) as e:
        asyncio.run(svc.request_driver_deletion(d.id))
    assert e.value.status_code == 409
