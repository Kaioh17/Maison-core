"""
PWA icon rendering (Pillow).

Every icon is a solid, full-bleed square PNG: iOS fills transparent pixels with
black and Android masks maskable icons itself, so rounded corners or alpha would
only make the result worse. Sources, best first: the tenant's uploaded icon or
logo (`render_logo_icon_png`), then a single-letter mark (`render_letter_icon_png`).
"""
from __future__ import annotations

import ipaddress
import math
import socket
from functools import lru_cache
from io import BytesIO
from typing import Optional
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageOps, ImageStat

from app.utils.logging import logger

# Logos smaller than this would upscale into mush at 192/512.
MIN_LOGO_PX = 64
MAX_LOGO_BYTES = 5 * 1024 * 1024
# Android maskable safe zone: a circle whose diameter is 80% of the canvas.
SAFE_ZONE = 0.8

_WHITE = (255, 255, 255)
_INK = (17, 17, 17)


def _hex_to_rgb(color: str, fallback: tuple[int, int, int] = (15, 13, 26)) -> tuple[int, int, int]:
    """Parse `#rrggbb` (or `#rgb`) into an `(r, g, b)` tuple."""
    if not color:
        return fallback
    c = color.strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return fallback
    try:
        return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))
    except ValueError:
        return fallback


def _luminance(rgb: tuple[int, int, int]) -> float:
    def channel(v: int) -> float:
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    hi, lo = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _best_contrast(against: tuple[int, int, int]) -> tuple[int, int, int]:
    return max((_WHITE, _INK), key=lambda c: _contrast(c, against))


@lru_cache(maxsize=8)
def _load_font(size_px: int) -> ImageFont.ImageFont:
    """
    Find a usable TrueType font; fall back to Pillow's default bitmap font if
    no system fonts are available (e.g., minimal Docker images).
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/local/share/fonts/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "C:\\Windows\\Fonts\\arialbd.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size_px)
        except OSError:
            continue
    logger.warning("PWA icon: no TrueType font found; using bitmap default font")
    return ImageFont.load_default()


def _png(image: Image.Image) -> bytes:
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def render_letter_icon_png(letter: str, size: int, background_hex: str) -> bytes:
    """Single-letter mark, sized to sit inside the maskable safe zone."""
    char = (letter or "M").strip() or "M"
    char = char[0].upper()

    bg = _hex_to_rgb(background_hex, fallback=(15, 13, 26))
    image = Image.new("RGB", (size, size), bg)

    font = _load_font(max(8, int(size * 0.5)))
    draw = ImageDraw.Draw(image)
    bbox = draw.textbbox((0, 0), char, font=font)
    x = (size - (bbox[2] - bbox[0])) / 2 - bbox[0]
    y = (size - (bbox[3] - bbox[1])) / 2 - bbox[1]
    draw.text((x, y), char, font=font, fill=_best_contrast(bg))
    return _png(image)


def render_logo_icon_png(data: bytes, size: int, brand_hex: str, maskable: bool = False) -> Optional[bytes]:
    """
    Square icon from an uploaded logo, or None when the logo is unusable
    (undecodable, too small, or blank) so the caller can fall back.

    - Transparent logos sit on `brand_hex`, flipped to white/ink when the logo
      would vanish against it (a white logo on a white brand colour).
    - Opaque logos keep their own background colour (sampled from the corner).
    - The artwork is trimmed to its content and scaled to fit the safe zone, so
      non-square logos are centred instead of stretched or cropped.
    """
    try:
        with Image.open(BytesIO(data)) as im:
            im.load()
            logo = ImageOps.exif_transpose(im).convert("RGBA")
    except (OSError, ValueError, Image.DecompressionBombError):
        return None
    if max(logo.size) < MIN_LOGO_PX:
        return None

    alpha = logo.getchannel("A")
    opaque = alpha.getextrema()[0] >= 250
    if opaque:
        bg = logo.getpixel((0, 0))[:3]
        solid = Image.new("RGB", logo.size, bg)
        content = ImageChops.difference(logo.convert("RGB"), solid).convert("L").point(lambda d: 255 if d > 24 else 0)
        box = content.getbbox()
    else:
        box = alpha.point(lambda a: 255 if a > 16 else 0).getbbox()
        mask = alpha.point(lambda a: 255 if a > 128 else 0)
        bg = _hex_to_rgb(brand_hex)
        if mask.getbbox():
            avg = tuple(int(v) for v in ImageStat.Stat(logo.convert("RGB"), mask=mask).mean)
            if _contrast(bg, avg) < 1.5:
                bg = _best_contrast(avg)
    if box is None:
        return None

    w, h = logo.size
    if opaque and not maskable and 0.95 <= w / h <= 1.05:
        # Already a designed square icon: fill the canvas.
        return _png(logo.convert("RGB").resize((size, size), Image.LANCZOS))

    logo = logo.crop(box)
    w, h = logo.size
    # Maskable: the whole artwork must sit inside the safe circle, so bound its diagonal.
    scale = SAFE_ZONE * size / (math.hypot(w, h) if maskable else max(w, h))
    fitted = logo.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    canvas = Image.new("RGB", (size, size), bg)
    canvas.paste(fitted, ((size - fitted.width) // 2, (size - fitted.height) // 2), fitted)
    return _png(canvas)


def fetch_logo(url: str, trusted_host: str = "") -> Optional[bytes]:
    """
    Download a logo, or None on any failure. `logo_url` is tenant-controlled, so
    only public https hosts are fetched (plus our own storage host, which may be
    local in dev), with no redirects, a short timeout and a size cap.
    """
    # ponytail: resolve-then-fetch leaves a DNS-rebinding gap; pin the resolved IP if this ever fetches non-storage hosts.
    parsed = urlparse(url)
    host = parsed.hostname
    if not host:
        return None
    try:
        if host != trusted_host:
            if parsed.scheme != "https":
                return None
            for info in socket.getaddrinfo(host, parsed.port or 443, type=socket.SOCK_STREAM):
                if not ipaddress.ip_address(info[4][0]).is_global:
                    return None
        with httpx.stream("GET", url, timeout=5.0, follow_redirects=False, headers={"Accept": "image/*"}) as resp:
            if resp.status_code != 200:
                return None
            body = bytearray()
            for chunk in resp.iter_bytes():
                body += chunk
                if len(body) > MAX_LOGO_BYTES:
                    return None
            return bytes(body)
    except (httpx.HTTPError, OSError, ValueError) as exc:
        logger.warning(f"PWA icon: could not fetch logo {url!r}: {exc}")
        return None
