"""
Per-host PWA install metadata.

iOS Safari and Android Chrome capture the manifest and apple-touch-icon at
"Add to Home Screen" time (before client-side JS runs). To keep white-label
branding correct across tenant subdomains, these endpoints derive the tenant
from the request `Host` header and return tenant-specific data, falling back
to default Maison branding when no tenant matches.

Endpoints intentionally live at the URL root (no `/api/v1` prefix) because the
browser fetches them from canonical paths like `/manifest.webmanifest` and
`/apple-touch-icon.png`.
"""
from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response

from app.utils.logging import logger
from app.utils.pwa_icons import render_letter_icon_png

from ..services.pwa_service import (
    MAISON_STATIC_APP_ICON,
    MAISON_STATIC_FAVICON_PNG,
    PwaService,
    TenantBrandingSnapshot,
    get_pwa_service,
)

router = APIRouter(tags=["PWA"])


# `Vary: Host` ensures any intermediate cache keys per host so two tenants do
# not share each other's manifest/icons. Short max-age keeps branding updates
# visible without overwhelming the backend.
_MANIFEST_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=300, must-revalidate",
    "Vary": "Host, X-Forwarded-Host, Accept-Encoding",
}
_ICON_CACHE_HEADERS = {
    "Cache-Control": "public, max-age=300, must-revalidate",
    "Vary": "Host, X-Forwarded-Host, Accept-Encoding",
}


def _resolve_host(request: Request) -> Optional[str]:
    """Prefer `X-Forwarded-Host` (nginx) so per-host resolution survives proxying."""
    logger.info(f"All headers: {dict(request.headers)}")
    # return 'bls.usemaison.io'
    forwarded = request.headers.get("x-forwarded-host")
    if forwarded:
        # nginx may concatenate multiple values; use the first.
        return forwarded.split(",")[0].strip()
    host_header = request.headers.get("host")
    if host_header:
        return host_header
    
    return request.url.hostname


def _parse_icon_size(name: str) -> Optional[int]:
    """
    Extract pixel size from icon filename variants.

    Accepts:
      - icon-192.png       -> 192
      - icon-512.png       -> 512
      - icon-maskable-512.png -> 512 (maskable)
      - apple-touch-icon-180x180.png -> 180
    """
    m = re.search(r"(\d{2,4})(?:x\d{2,4})?\.png$", name.lower())
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def _is_maskable(name: str) -> bool:
    return "maskable" in name.lower()


def _icon_response(
    snapshot: Optional[TenantBrandingSnapshot],
    size: int,
    maskable: bool,
    *,
    favicon_shortcut: bool = False,
) -> Response:
    """
    Return a tenant-branded icon at the requested size.

    For the main Maison host (no tenant slug), 302-redirect to static assets in
    the frontend `public/` bundle: app icon → ``/icons/icon.png``; shortcut
    favicon endpoints → ``/favicon-48x48.png``.

    For non-maskable icons on tenant hosts, prefers a 302 redirect to the
    tenant-uploaded favicon so the browser caches the asset directly from its
    CDN. Maskable icons render a letter-mark with the tenant accent color
    because the OS crops them and an uploaded favicon would not respect the
    safe zone. When no tenant matches and a letter-mark is needed, falls back
    to generated artwork.
    """
    if snapshot is None:
        target = MAISON_STATIC_FAVICON_PNG if favicon_shortcut else MAISON_STATIC_APP_ICON
        return RedirectResponse(
            url=target,
            status_code=302,
            headers=_ICON_CACHE_HEADERS,
        )

    if snapshot.favicon_url and not maskable:
        # Cache headers travel with the redirect so the browser can keep the
        # canonical URL warm without re-resolving the tenant on every fetch.
        return RedirectResponse(
            url=snapshot.favicon_url,
            status_code=302,
            headers=_ICON_CACHE_HEADERS,
        )

    letter = snapshot.initial
    background = snapshot.accent_color
    png = render_letter_icon_png(
        letter=letter,
        size=size,
        background_hex=background,
        foreground_hex="#ffffff",
        maskable=maskable,
    )
    return Response(
        content=png,
        media_type="image/png",
        headers=_ICON_CACHE_HEADERS,
    )


@router.get(
    "/manifest.webmanifest",
    summary="Per-host PWA web manifest",
    description=(
        "Returns a Web App Manifest tailored to the request host. On tenant "
        "subdomains the manifest carries the tenant's company name, theme "
        "color, and favicon so installed home-screen apps launch standalone "
        "with white-label branding."
    ),
)
async def get_manifest(
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    manifest = service.build_manifest(snapshot)
    logger.debug(
        f"PWA manifest served host={host!r} slug={(snapshot.slug if snapshot else None)!r}"
    )
    return Response(
        content=_safe_json(manifest),
        # application/manifest+json is the correct type, but `Content-Type` must
        # be served exactly so Android/iOS recognize the document. Some older
        # crawlers also accept `application/json`.
        media_type="application/manifest+json",
        headers=_MANIFEST_CACHE_HEADERS,
    )


def _safe_json(data: dict) -> bytes:
    """Lightweight JSON serializer that avoids importing fastapi's encoder."""
    import json

    return json.dumps(data, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


@router.get(
    "/apple-touch-icon.png",
    summary="Per-host Apple touch icon (default size)",
)
@router.get(
    "/apple-touch-icon-precomposed.png",
    summary="Per-host Apple touch icon (precomposed alias)",
)
async def get_apple_touch_icon_default(
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    # 180x180 is the modern iOS recommendation; iOS will rescale as needed.
    return _icon_response(snapshot, size=180, maskable=False)


@router.get(
    "/apple-touch-icon-{spec}.png",
    summary="Per-host Apple touch icon (size variant)",
    description=(
        "iOS probes well-known size variants like `apple-touch-icon-180x180.png` "
        "and precomposed aliases (`apple-touch-icon-120x120-precomposed.png`) "
        "even when no link tag references them; this catch-all answers all of "
        "them."
    ),
)
async def get_apple_touch_icon_sized(
    spec: str,
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    size = _parse_icon_size(f"icon-{spec}.png") or 180
    # Clamp to a sane range so user-supplied sizes can't blow up Pillow.
    size = max(48, min(size, 1024))
    return _icon_response(snapshot, size=size, maskable=False)


@router.get(
    "/icons/icon-{spec}.png",
    summary="Per-host PWA icon (size variant)",
    description=(
        "Returns the tenant's branded icon at the requested size. Sizes like "
        "192, 512, and `maskable-512` are referenced by the manifest."
    ),
)
async def get_pwa_icon(
    spec: str,
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    name = f"icon-{spec}.png"
    size = _parse_icon_size(name) or 192
    size = max(48, min(size, 1024))
    maskable = _is_maskable(name)
    return _icon_response(snapshot, size=size, maskable=maskable)


@router.get(
    "/favicon-48x48.png",
    summary="Per-host favicon (PNG)",
)
async def get_favicon_png(
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    return _icon_response(snapshot, size=64, maskable=False, favicon_shortcut=True)


@router.get("/manifest.json")
async def get_manifest_json(request: Request, service: PwaService = Depends(get_pwa_service)):
    host = _resolve_host(request)
    host = 'bls.usemaison.io'
    snapshot = service.resolve_branding(host)
    
    
    return snapshot
@router.get(
    "/favicon.ico",
    summary="Per-host favicon (ICO alias)",
)
async def get_favicon_ico(
    request: Request,
    service: PwaService = Depends(get_pwa_service),
):
    # Browsers happily accept a PNG payload under the .ico path; this avoids the
    # extra `pyicon` dependency while still answering the legacy probe.
    host = _resolve_host(request)
    snapshot = service.resolve_branding(host)
    return _icon_response(snapshot, size=64, maskable=False, favicon_shortcut=True)
