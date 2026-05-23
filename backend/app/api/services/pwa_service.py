"""
PWA service: host-aware manifest + icon resolution.

Tenants are served from `<slug>.<MAIN_DOMAIN>` subdomains, so install-time PWA
metadata (manifest, apple-touch-icon) must be resolved per request `Host` header
to deliver correct white-label name/colors/icons to iOS Safari and Android Chrome
at "Add to Home Screen" time. Runtime JS cannot reliably patch these because
both platforms snapshot the metadata before client-side React mounts.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.database import get_base_db
from app.utils.logging import logger

from .helper_service import tenant_branding, tenant_profile, tenant_table, Validations, HTTPException

# Subdomains that are infrastructure / marketing, not tenant slugs.
RESERVED_SUBDOMAIN_LABELS = {"www", "api", "admin"}

# Conservative hex pattern; falls back to defaults when validation fails.
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?$")

# Default Maison brand fallbacks (mirror values used in the frontend shell).
DEFAULT_APP_NAME = "Maison"
DEFAULT_THEME_COLOR = "#0f0d1a"
DEFAULT_BACKGROUND_COLOR = "#0f0d1a"
DEFAULT_ACCENT_COLOR = "#6c63e8"

# Static assets shipped in the frontend `public/` folder for the apex / main
# domain (no tenant slug). nginx serves these from disk; PWA routes 302 here
# when `resolve_branding` returns None so home-screen icons match brand
# artwork instead of server-generated letter marks.
MAISON_STATIC_APP_ICON = "/icons/icon.png"
MAISON_STATIC_FAVICON_PNG = "/favicon-48x48.png"


@dataclass(frozen=True)
class TenantBrandingSnapshot:
    """Subset of tenant fields needed to render PWA metadata for one host."""

    slug: str
    company_name: str
    favicon_url: Optional[str]
    logo_url: Optional[str]
    theme_color: str
    background_color: str
    accent_color: str

    @property
    def display_name(self) -> str:
        return (self.company_name or self.slug or DEFAULT_APP_NAME).strip() or DEFAULT_APP_NAME

    @property
    def short_name(self) -> str:
        """First word of display name capped at 12 characters (manifest convention)."""
        name = self.display_name
        first_word = name.split()[0] if name else DEFAULT_APP_NAME
        return first_word[:12]

    @property
    def initial(self) -> str:
        """First printable character of the display name, used for fallback icons."""
        for ch in self.display_name:
            if ch.strip():
                return ch.upper()
        return "M"


def _normalize_color(value: Optional[str], fallback: str) -> str:
    if not value:
        return fallback
    candidate = value.strip()
    if HEX_COLOR_RE.match(candidate):
        if len(candidate) == 4:
            # Expand #abc -> #aabbcc so downstream consumers always get 6-digit hex.
            return f"#{candidate[1]*2}{candidate[2]*2}{candidate[3]*2}"
        return candidate
    return fallback


def _strip_port(host: str) -> str:
    return host.split(":", 1)[0].lower().strip()


def extract_slug_from_host(host: Optional[str], main_domain: str) -> Optional[str]:
    """
    Resolve tenant slug from a request `Host` header.

    - `acme.usemaison.io`   -> `acme`
    - `acme.localhost`      -> `acme`
    - `usemaison.io` / `www.usemaison.io` / `api.usemaison.io` -> None
    - `localhost`, `127.0.0.1` -> None
    """
    if not host:
        return None
    hostname = _strip_port(host)
    if not hostname:
        return None

    main_domain_norm = (main_domain or "").lower().strip()

    # Exact main domain or bare dev host means no tenant.
    if hostname == main_domain_norm:
        return None
    if hostname in {"localhost", "127.0.0.1"} or hostname.startswith("127.0.0.1"):
        return None

    parts = hostname.split(".")
    if len(parts) < 2:
        return None

    label = parts[0]
    if not label or label in RESERVED_SUBDOMAIN_LABELS:
        return None

    # Accept slug.<main_domain> in prod and slug.localhost in dev.
    rest = ".".join(parts[1:])
    if main_domain_norm and rest == main_domain_norm:
        return label
    if rest == "localhost":
        return label

    # Generic multi-label host (slug.something.tld): treat first label as slug
    # so staging-like hosts still get tenant branding.
    if len(parts) >= 3:
        return label

    return None

from .slug_services import SlugService
from app.schemas.slug import TenantSlugResponse
class PwaService:
    """Resolves tenant branding for PWA endpoints from a request host."""

    def __init__(self, db: Session):
        self.db = db
        self._settings = Settings()

    @property
    def main_domain(self) -> str:
        # `Settings.domain` is the public hostname (e.g. `usemaison.io`). In dev
        # it can include a port (`localhost:3000`); strip it so it matches the
        # bare host extracted from incoming requests.
        raw = (self._settings.domain or "").lower().strip()
        return raw.split(":", 1)[0]

    def resolve_branding(self, host: Optional[str]) -> Optional[TenantBrandingSnapshot]:
        """
        Return tenant branding for the host, or None when the host has no slug
        or the tenant is not active.
        """
        logger.debug(host)
        slug = extract_slug_from_host(host, self.main_domain)

        if not slug:
            return None
        # verified_tenant_id = Validations(self.db)._verify_slug(slug)
        tenant_manifest = SlugService(self.db, current_user=None).verify_slug(slug=slug)
        tenant_manifest = tenant_manifest.data
        if not tenant_manifest:
            raise HTTPException(404, "Slug does not exists")
        logger.debug(tenant_manifest['profile']['company_name'])

        return TenantBrandingSnapshot(
            slug=slug,
            company_name=(tenant_manifest['profile']['company_name'] or "").strip(),
            favicon_url=(tenant_manifest['branding']['favicon_url'] or "").strip() or None,
            logo_url=(tenant_manifest['branding']['logo_url'] or "").strip() or None,
            theme_color=_normalize_color(tenant_manifest['branding']['background_color'], DEFAULT_THEME_COLOR),
            background_color=_normalize_color(tenant_manifest['branding']['background_color'], DEFAULT_BACKGROUND_COLOR),
            accent_color=_normalize_color(tenant_manifest['branding']['primary_color'], DEFAULT_ACCENT_COLOR),
        )
        
        try:
            row = (
                self.db.query(tenant_profile, tenant_branding, tenant_table)
                .join(tenant_branding, tenant_branding.tenant_id == tenant_profile.tenant_id)
                .join(tenant_table, tenant_table.id == tenant_profile.tenant_id)
                .filter(tenant_profile.slug == slug)
                .first()
            )
        except Exception as exc:
            # Failures here must not break PWA install metadata; fall back silently.
            logger.warning(f"PWA branding lookup failed for slug={slug!r}: {exc}")
            return None

        if not row:
            return None

        profile, branding, tenant = row
        # Skip soft-deleted/inactive tenants so we don't serve their branding to
        # the world; the public default Maison branding will be returned instead.
        if getattr(tenant, "is_active", True) is False:
            return None

        return TenantBrandingSnapshot(
            slug=slug,
            company_name=(profile.company_name or "").strip(),
            favicon_url=(branding.favicon_url or "").strip() or None,
            logo_url=(branding.logo_url or profile.logo_url or "").strip() or None,
            theme_color=_normalize_color(branding.background_color, DEFAULT_THEME_COLOR),
            background_color=_normalize_color(branding.background_color, DEFAULT_BACKGROUND_COLOR),
            accent_color=_normalize_color(branding.primary_color, DEFAULT_ACCENT_COLOR),
        )

    def build_manifest(self, snapshot: Optional[TenantBrandingSnapshot]) -> dict:
        """
        Build a JSON-serializable web app manifest tailored to the tenant.
        Falls back to Maison defaults when snapshot is None.
        """
        if snapshot is None:
            name = DEFAULT_APP_NAME
            short_name = DEFAULT_APP_NAME
            theme = DEFAULT_THEME_COLOR
            bg = DEFAULT_BACKGROUND_COLOR
            icons = self._default_icon_entries()
        else:
            name = snapshot.display_name
            short_name = snapshot.short_name
            theme = snapshot.theme_color
            bg = snapshot.background_color
            icons = self._tenant_icon_entries(snapshot)

        return {
            "name": name,
            "short_name": short_name,
            "description": f"{name} — book a ride.",
            "start_url": "/?source=pwa",
            "id": "/?source=pwa",
            "scope": "/",
            "display": "standalone",
            "display_override": ["standalone", "minimal-ui"],
            "orientation": "any",
            "background_color": bg,
            "theme_color": theme,
            "lang": "en",
            "dir": "ltr",
            "categories": ["business", "travel"],
            "icons": icons,
        }

    def _default_icon_entries(self) -> list[dict]:
        # Main Ma domain: ship icons from the frontend bundle (`public/icons/icon.png`).
        # Tenant subdomains use the same manifest shape but resolve icon URLs via
        # the backend `/icons/icon-*.png` handlers (redirect or generated).
        return [
            {
                "src": MAISON_STATIC_APP_ICON,
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": MAISON_STATIC_APP_ICON,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": MAISON_STATIC_APP_ICON,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ]

    def _tenant_icon_entries(self, _snapshot: TenantBrandingSnapshot) -> list[dict]:
        # Manifest entries point at backend routes so each size + maskable flag
        # is handled consistently (`pwa._icon_response`).
        # TODO switch from default maison entry to a 
        logger.debug(f'_snapshpot =  {_snapshot.logo_url}')
        icon_src = _snapshot.logo_url or f"/icons/icon.png"
    
        entries = [
            {
                "src": icon_src,
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": icon_src,
                "sizes": "512x512", 
                "type": "image/png",
                "purpose": "any",
            },
        ]
        
        # Only add maskable if we have a real logo, otherwise use generated
        maskable_src = icon_src or f"/icons/icon.png"
        entries.append({
            "src": maskable_src,
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "maskable",
        })
        
        return entries
        return [
            {
                "src": _snapshot.logo_url,
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": _snapshot.logo_url,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any",
            },
            {
                "src": _snapshot.logo_url,
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "maskable",
            },
        ]


def get_pwa_service(db: Session = Depends(get_base_db)) -> PwaService:
    return PwaService(db=db)
