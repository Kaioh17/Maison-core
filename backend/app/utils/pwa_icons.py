"""
Generate fallback PWA icon PNGs using Pillow.

Used when no tenant favicon URL is available (e.g., main domain, tenant has not
uploaded an icon yet). Produces a rounded-square background with a single-letter
mark, which mirrors the SVG fallback used by `useFavicon.ts`.
"""
from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from app.utils.logging import logger


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


def _rounded_mask(size: int, radius: int) -> Image.Image:
    """Single-channel rounded-square mask used to clip the icon background."""
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=radius, fill=255)
    return mask


def render_letter_icon_png(
    letter: str,
    size: int,
    background_hex: str,
    foreground_hex: Optional[str] = None,
    maskable: bool = False,
) -> bytes:
    """
    Render a single-letter PNG icon.

    - `maskable=True` keeps the artwork inside the safe zone (80% of canvas)
      so the mark survives platform-specific maskable cropping.
    """
    char = (letter or "M").strip() or "M"
    char = char[0].upper()

    bg = _hex_to_rgb(background_hex, fallback=(15, 13, 26))
    fg_rgb = _hex_to_rgb(foreground_hex or "#ffffff", fallback=(255, 255, 255))

    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Maskable icons must keep important art inside the inner 80% safe zone.
    if maskable:
        # Fill the whole canvas; the platform crops it. No rounded corners.
        background = Image.new("RGBA", (size, size), bg + (255,))
        image.alpha_composite(background)
        text_box = size * 0.6  # letter target height inside safe zone
    else:
        radius = max(1, int(size * 0.22))
        background = Image.new("RGBA", (size, size), bg + (255,))
        mask = _rounded_mask(size, radius)
        image.paste(background, (0, 0), mask)
        text_box = size * 0.62

    font_size = max(8, int(text_box))
    font = _load_font(font_size)

    draw = ImageDraw.Draw(image)
    # textbbox is the modern (Pillow 10+) replacement for textsize and gives
    # accurate metrics across font types.
    bbox = draw.textbbox((0, 0), char, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = (size - text_w) / 2 - bbox[0]
    text_y = (size - text_h) / 2 - bbox[1]
    draw.text((text_x, text_y), char, font=font, fill=fg_rgb + (255,))

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()
