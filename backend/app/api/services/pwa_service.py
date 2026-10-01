"""
PWA service: host-aware manifest + icon resolution.

Tenants are served from `<slug>.<MAIN_DOMAIN>` subdomains, so install-time PWA
metadata (manifest, apple-touch-icon) must be resolved per request `Host` header
to deliver correct white-label name/colors/icons to iOS Safari and Android Chrome
at "Add to Home Screen" time. Runtime JS cannot reliably patch these because
both platforms snapshot the metadata before client-side React mounts.
"""
from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.config import Settings
from app.db.database import get_base_db
from app.utils.pwa_icons import fetch_logo, render_letter_icon_png, render_logo_icon_png

from .slug_services import SlugService

# Subdomains that are infrastructure / marketing, not tenant slugs.
RESERVED_SUBDOMAIN_LABELS = {"www", "api", "admin", "app", "ekko"}

# Conservative hex pattern; falls back to defaults when validation fails.
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?$")

# Default Maison brand (the app's own --bw-bg / --bw-accent dark tokens), used
# for the apex host and for tenants that have branding turned off, exactly like
# the frontend shell does.
DEFAULT_APP_NAME = "Maison"
DEFAULT_THEME_COLOR = "#0B0B0C"
DEFAULT_BACKGROUND_COLOR = "#0B0B0C"
DEFAULT_ACCENT_COLOR = "#6e5bd8"

MAISON_ICON_BYTES = (Path(__file__).resolve().parents[2] / "static" / "maison-icon.png").read_bytes()
MAISON_ICON_VERSION = hashlib.sha1(MAISON_ICON_BYTES).hexdigest()[:10]

# Only these sizes are ever rendered, so the icon cache stays bounded no matter
# what sizes iOS (or a scanner) probes for. Requests snap to the nearest.
ICON_SIZES = (64, 180, 192, 512)

NAME_MAX = 45
SHORT_NAME_MAX = 12

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x1f\x7f-\x9f\u200b\u2028\u2029\ufeff]")


def clean_name(value: Optional[str]) -> str:
    """Strip control/invisible characters and collapse whitespace."""
    return " ".join(_CONTROL_CHARS_RE.sub(" ", value or "").split())


def make_short_name(name: str) -> str:
    """
    Home-screen label: the full name if it fits in 12 characters, else as many
    whole words as fit, else the first 12 characters. Mirrors `shortAppName` in
    the frontend (`src/utils/tenantName.ts`); keep both in sync.
    """
    if len(name) <= SHORT_NAME_MAX:
        return name
    out = ""
    for word in name.split(" "):
        candidate = f"{out} {word}".strip()
        if len(candidate) > SHORT_NAME_MAX:
            break
        out = candidate
    # ponytail: counts code points, so a ZWJ emoji can be cut mid-sequence; the rstrip drops the dangling joiner.
    return out or name[:SHORT_NAME_MAX].rstrip("\u200d\ufe0f ")


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
    # `tenant_branding.updated_on`: logos are re-uploaded to a stable URL, so the
    # URL alone cannot tell caches that the image changed.
    updated_on: str = ""

    @property
    def display_name(self) -> str:
        name = clean_name(self.company_name) or clean_name(self.slug) or DEFAULT_APP_NAME
        if len(name) <= NAME_MAX:
            return name
        return name[:NAME_MAX].rsplit(" ", 1)[0] if " " in name[:NAME_MAX] else name[:NAME_MAX]

    @property
    def short_name(self) -> str:
        return make_short_name(self.display_name)

    @property
    def initial(self) -> str:
        """First letter or digit of the name (emoji and punctuation do not render in the icon font)."""
        for ch in self.display_name:
            if ch.isalnum():
                return ch.upper()
        return "M"

    @property
    def icon_sources(self) -> list[str]:
        """Tenant icon first, then the logo."""
        return [u for u in (self.favicon_url, self.logo_url) if u]

    @property
    def version(self) -> str:
        """Changes whenever anything that affects the rendered icon changes."""
        raw = "|".join([self.favicon_url or "", self.logo_url or "", self.updated_on, self.background_color, self.accent_color, self.initial])
        return hashlib.sha1(raw.encode()).hexdigest()[:10]


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

# Rendered icons by (version, size, maskable). Per-process and bounded; the version
# in the key means a changed logo can never be served from a stale entry.
_ICON_CACHE: "OrderedDict[tuple[str, int, bool], bytes]" = OrderedDict()
_ICON_CACHE_MAX = 256


def snap_icon_size(requested: int) -> int:
    return min(ICON_SIZES, key=lambda s: abs(s - requested))


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

    def is_tenant_app_host(self, host: Optional[str]) -> bool:
        """True for the tenant-operator dashboard host, `app.{main_domain}`."""
        if not host:
            return False
        return _strip_port(host) == f"app.{self.main_domain}"

    def resolve_branding(self, host: Optional[str]) -> Optional[TenantBrandingSnapshot]:
        """
        Return tenant branding for the host, or None when the host has no slug or
        the tenant is unknown/inactive (callers then serve default Maison branding,
        so an install never breaks on a bad slug).
        """
        slug = extract_slug_from_host(host, self.main_domain)
        if not slug:
            return None
        try:
            data = SlugService(self.db, current_user=None).verify_slug(slug=slug).data
        except HTTPException:
            return None
        profile, branding = data["profile"], data["branding"]
        # Mirror the frontend: tenant colours apply only when branding is enabled.
        enabled = bool(branding.get("enable_branding"))
        background = _normalize_color(branding.get("background_color"), DEFAULT_BACKGROUND_COLOR) if enabled else DEFAULT_BACKGROUND_COLOR
        accent = _normalize_color(branding.get("primary_color"), DEFAULT_ACCENT_COLOR) if enabled else DEFAULT_ACCENT_COLOR
        return TenantBrandingSnapshot(
            slug=slug,
            company_name=profile.get("company_name") or "",
            favicon_url=(branding.get("favicon_url") or "").strip() or None,
            logo_url=(branding.get("logo_url") or "").strip() or None,
            theme_color=background,
            background_color=background,
            accent_color=accent,
            updated_on=str(branding.get("updated_on") or branding.get("created_on") or ""),
        )

    def build_manifest(self, snapshot: Optional[TenantBrandingSnapshot], *, is_tenant_app: bool = False) -> dict:
        """
        Build a JSON-serializable web app manifest tailored to the tenant.
        Falls back to Maison defaults when snapshot is None. `is_tenant_app`
        is set for the `app.{main_domain}` operator dashboard host so the
        installed PWA opens straight at the dashboard (ProtectedRoute already
        bounces an unauthenticated visit to /tenant/login) instead of the
        generic root, which would otherwise show the marketing landing page.
        """
        if snapshot is None:
            name = "Maison for Business" if is_tenant_app else DEFAULT_APP_NAME
            short_name = DEFAULT_APP_NAME
            theme = DEFAULT_THEME_COLOR
            bg = DEFAULT_BACKGROUND_COLOR
            version = MAISON_ICON_VERSION
        else:
            name = snapshot.display_name
            short_name = snapshot.short_name
            theme = snapshot.theme_color
            bg = snapshot.background_color
            version = snapshot.version

        start_url = "/tenant/overview" if is_tenant_app else "/?source=pwa"
        # Unique per tenant even if two tenants are ever served from one origin.
        app_id = f"/?tenant={snapshot.slug}" if snapshot else start_url
        description = (
            "Manage your fleet, drivers, and bookings."
            if is_tenant_app
            else f"{name} \u2014 book a ride."
        )
        icon = lambda path, sizes, purpose: {"src": f"/icons/{path}?v={version}", "sizes": sizes, "type": "image/png", "purpose": purpose}

        return {
            "id": app_id,
            "name": name,
            "short_name": short_name,
            "description": description,
            "start_url": start_url,
            "scope": "/",
            "display": "standalone",
            "background_color": bg,
            "theme_color": theme,
            "lang": "en",
            "dir": "ltr",
            "categories": ["business", "travel"],
            "icons": [
                icon("icon-192.png", "192x192", "any"),
                icon("icon-512.png", "512x512", "any"),
                icon("icon-maskable-512.png", "512x512", "maskable"),
            ],
        }

    def render_icon(self, snapshot: Optional[TenantBrandingSnapshot], size: int, maskable: bool) -> tuple[bytes, bool]:
        """
        Icon PNG for the host, falling back tenant icon -> logo -> initials on the
        brand colour -> Maison icon. Returns `(png, stable)`; `stable` is False when
        a logo exists but could not be downloaded, so callers must not cache that
        result for long (the real icon may appear on the next attempt).
        """
        version = snapshot.version if snapshot else MAISON_ICON_VERSION
        key = (version, size, maskable)
        cached = _ICON_CACHE.get(key)
        if cached is not None:
            _ICON_CACHE.move_to_end(key)
            return cached, True

        stable = True
        png: Optional[bytes] = None
        if snapshot is None:
            png = render_logo_icon_png(MAISON_ICON_BYTES, size, DEFAULT_BACKGROUND_COLOR, maskable)
        else:
            trusted_host = urlparse(self._settings.supabase_url).hostname or ""
            for url in snapshot.icon_sources:
                data = fetch_logo(url, trusted_host)
                if data is None:
                    stable = False
                    continue
                png = render_logo_icon_png(data, size, snapshot.background_color, maskable)
                if png:
                    break
            if png is None:
                png = render_letter_icon_png(snapshot.initial, size, snapshot.accent_color)
        if png is None:
            png = render_letter_icon_png("M", size, DEFAULT_ACCENT_COLOR)

        if stable:
            _ICON_CACHE[key] = png
            while len(_ICON_CACHE) > _ICON_CACHE_MAX:
                _ICON_CACHE.popitem(last=False)
        return png, stable


def get_pwa_service(db: Session = Depends(get_base_db)) -> PwaService:
    return PwaService(db=db)
