from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from slowapi.util import get_remote_address

from app.config import Settings
from app.domain.legal import LEGAL_VERSION, PILOT_DAYS, PILOT_CONTACT_EMAIL
from app.models.legal_acceptance import LegalAcceptance
from app.models.tenant import TenantProfile

settings = Settings()


def is_demo(db, tenant) -> bool:
    slug = settings.demo_tenant_slug
    return bool(slug) and db.query(TenantProfile).filter_by(tenant_id=tenant.id, slug=slug).first() is not None


def has_accepted(db, tenant) -> bool:
    return db.query(LegalAcceptance.id).filter_by(tenant_id=tenant.id, version=LEGAL_VERSION).first() is not None


def pilot_expired(tenant) -> bool:
    return tenant.pilot_ends_at is not None and tenant.pilot_ends_at < datetime.now(timezone.utc)


def pilot_ended_error(tenant) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Your Maison pilot ended on {tenant.pilot_ends_at:%B %d, %Y}. "
        f"To continue or export your data, contact {PILOT_CONTACT_EMAIL}.",
    )


def accept(db, tenant, request, source: str) -> None:
    """Record acceptance of the current version (idempotent) and start the pilot clock on first acceptance."""
    if not has_accepted(db, tenant):
        db.add(LegalAcceptance(
            tenant_id=tenant.id,
            version=LEGAL_VERSION,
            source=source,
            ip_address=get_remote_address(request),
            user_agent=(request.headers.get("user-agent") or "")[:400] or None,
        ))
    if tenant.pilot_ends_at is None:
        tenant.pilot_ends_at = datetime.now(timezone.utc) + timedelta(days=PILOT_DAYS)
    db.commit()


def enforce_on_login(db, tenant, request, legal_version: str | None) -> None:
    """Tenant login gate: the pilot must still be running. Acceptance is collected by the dashboard PilotGate, not at login."""
    if is_demo(db, tenant):
        return
    if pilot_expired(tenant):
        raise pilot_ended_error(tenant)


def status_for(db, tenant) -> dict:
    ends = tenant.pilot_ends_at
    return {
        "current_version": LEGAL_VERSION,
        "accepted": has_accepted(db, tenant) or is_demo(db, tenant),
        "pilot_ends_at": ends,
        "days_left": max((ends - datetime.now(timezone.utc)).days, 0) if ends else None,
        "expired": pilot_expired(tenant) and not is_demo(db, tenant),
        "contact_email": PILOT_CONTACT_EMAIL,
    }
