"""
Per-host PWA install metadata.

iOS Safari and Android Chrome capture the manifest and apple-touch-icon at
"Add to Home Screen" time (before client-side JS runs). To keep white-label
branding correct across tenant subdomains, these endpoints derive the tenant
from the request `Host` header and return tenant-specific data, falling back
to default Maison branding when no tenant matches.

Endpoints intentionally live at the URL root (no `/api/v1` prefix) because the
browser fetches them from canonical paths like `/manifest.webmanifest` and
`/apple-touch-icon.png`. Handlers are plain `def` (not `async`) because they do
blocking DB, network and Pillow work, which FastAPI then runs in its threadpool.
"""
from __future__ import annotations

import json
import re
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response

from ..services.pwa_service import (
    MAISON_ICON_VERSION,
    PwaService,
    TenantBrandingSnapshot,
    get_pwa_service,
    snap_icon_size,
)

router = APIRouter(tags=["PWA"])


# `Vary: Host` ensures any intermediate cache keys per host so two tenants do
# not share each other's manifest/icons.
_VARY = "Host, X-Forwarded-Host, Accept-Encoding"
_MANIFEST_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=300, must-revalidate",
    "Vary": _VARY,
}
# Icon URLs carry `?v=<version>` (see `PwaService.build_manifest`), so a matching
# request can be cached for a year: a changed logo changes the URL.
_IMMUTABLE = "public, max-age=31536000, immutable"
# Unversioned probes (`/apple-touch-icon.png`, `/favicon.ico`) revalidate via ETag.
_REVALIDATE = "public, max-age=300, must-revalidate"
# A degraded render (logo download failed) must be retried soon, never pinned.
_DEGRADED = "public, max-age=60"


def _resolve_host(request: Request) -> Optional[str]:
    """Prefer `X-Forwarded-Host` (nginx) so per-host resolution survives proxying."""
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        # nginx may concatenate multiple values; use the first.
        return forwarded.split(",")[0].strip()
    return request.headers.get("host") or request.url.hostname


def _parse_icon_size(name: str) -> Optional[int]:
    """
    Extract pixel size from icon filename variants.

    Accepts:
      - icon-192.png       -> 192
      - icon-maskable-512.png -> 512 (maskable)
      - apple-touch-icon-180x180.png -> 180
    """
    m = re.search(r"(\d{2,4})(?:x\d{2,4})?\.png$", name.lower())
    return int(m.group(1)) if m else None


def _icon_response(
    request: Request,
    service: PwaService,
    snapshot: Optional[TenantBrandingSnapshot],
    requested_size: int,
    maskable: bool = False,
) -> Response:
    size = snap_icon_size(requested_size)
    version = snapshot.version if snapshot else MAISON_ICON_VERSION
    png, stable = service.render_icon(snapshot, size, maskable)

    etag = f'"{version}-{size}-{int(maskable)}"'
    if not stable:
        cache_control = _DEGRADED
    elif request.query_params.get("v") == version:
        cache_control = _IMMUTABLE
    else:
        cache_control = _REVALIDATE
    headers = {"Cache-Control": cache_control, "Vary": _VARY}
    if stable:
        headers["ETag"] = etag
        if request.headers.get("if-none-match") == etag:
            return Response(status_code=304, headers=headers)
    return Response(content=png, media_type="image/png", headers=headers)


@router.get(
    "/manifest.webmanifest",
    summary="Per-host PWA web manifest",
    description=(
        "Returns a Web App Manifest tailored to the request host. On tenant "
        "subdomains the manifest carries the tenant's name, brand colors and "
        "icons so installed home-screen apps launch standalone with white-label "
        "branding. Unknown hosts get the default Maison manifest."
    ),
)
def get_manifest(request: Request, service: PwaService = Depends(get_pwa_service)):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    manifest = service.build_manifest(snapshot, is_tenant_app=service.is_tenant_app_host(host))
    return Response(
        content=json.dumps(manifest, separators=(",", ":"), ensure_ascii=False).encode("utf-8"),
        media_type="application/manifest+json",
        headers=_MANIFEST_CACHE_HEADERS,
    )


@router.get("/apple-touch-icon.png", summary="Per-host Apple touch icon (default size)")
@router.get("/apple-touch-icon-precomposed.png", summary="Per-host Apple touch icon (precomposed alias)")
def get_apple_touch_icon_default(request: Request, service: PwaService = Depends(get_pwa_service)):
    snapshot = service.resolve_branding(_resolve_host(request))
    return _icon_response(request, service, snapshot, 180)


@router.get(
    "/apple-touch-icon-{spec}.png",
    summary="Per-host Apple touch icon (size variant)",
    description=(
        "iOS probes well-known size variants like `apple-touch-icon-120x120.png` "
        "and precomposed aliases even when no link tag references them; this "
        "catch-all answers all of them, snapped to a supported size."
    ),
)
def get_apple_touch_icon_sized(spec: str, request: Request, service: PwaService = Depends(get_pwa_service)):
    snapshot = service.resolve_branding(_resolve_host(request))
    return _icon_response(request, service, snapshot, _parse_icon_size(f"icon-{spec}.png") or 180)


@router.get(
    "/icons/icon-{spec}.png",
    summary="Per-host PWA icon (size variant)",
    description="Sizes like `192`, `512` and `maskable-512` are referenced by the manifest.",
)
def get_pwa_icon(spec: str, request: Request, service: PwaService = Depends(get_pwa_service)):
    snapshot = service.resolve_branding(_resolve_host(request))
    return _icon_response(
        request, service, snapshot, _parse_icon_size(f"icon-{spec}.png") or 192, maskable="maskable" in spec.lower()
    )


@router.get("/favicon-48x48.png", summary="Per-host favicon (PNG)")
@router.get("/favicon.ico", summary="Per-host favicon (ICO alias)")
def get_favicon(request: Request, service: PwaService = Depends(get_pwa_service)):
    # Browsers accept a PNG payload under the .ico path.
    snapshot = service.resolve_branding(_resolve_host(request))
    return _icon_response(request, service, snapshot, 64)
