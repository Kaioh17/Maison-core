"""Read-only guard for the demo tenant (settings.demo_tenant_slug).

Registered once as an app-level dependency in main.py, so it covers every present and future route.
A write is refused when the request belongs to the demo tenant, identified by:
  - the access token's tenant (same claim rules as security.get_tenant_id_from_token), or
  - a `slug` path param or `X-Tenant-Slug` header (unauthenticated sign-up / apply / guest flows).
"""
from fastapi import HTTPException, Request, status
from jose import jwt
from app.config import Settings
from app.db.database import SessionLocal
from app.models.tenant import TenantProfile

settings = Settings()

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
# Session handling and non-tenant-data writes: the demo must still be able to sign in/out and chat.
EXEMPT_PREFIXES = ("/api/v1/auth/", "/api/v1/logs/", "/api/v1/ai/chat")

_demo_tenant_id: str | None = None


def _get_demo_tenant_id() -> str | None:
    global _demo_tenant_id
    if _demo_tenant_id is None:  # only a hit is cached, so a demo seeded later is still picked up
        with SessionLocal() as db:
            row = db.query(TenantProfile.tenant_id).filter(TenantProfile.slug == settings.demo_tenant_slug).first()
        if row:
            _demo_tenant_id = str(row[0])
    return _demo_tenant_id


def _token_tenant_id(request: Request) -> str | None:
    scheme, _, token = request.headers.get("authorization", "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.JWTError:
        return None  # the route's own auth will reject it
    tid = payload.get("id") if str(payload.get("role", "")).lower() == "tenant" else payload.get("tenant_id")
    return None if tid is None else str(tid)


def block_demo_writes(request: Request) -> None:
    slug = settings.demo_tenant_slug
    if not slug or request.method in SAFE_METHODS or request.url.path.startswith(EXEMPT_PREFIXES):
        return
    tid = _token_tenant_id(request)
    if (
        request.path_params.get("slug") == slug
        or request.headers.get("x-tenant-slug") == slug
        or (tid is not None and tid == _get_demo_tenant_id())
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="The demo account is read-only.")
