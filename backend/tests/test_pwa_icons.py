"""PWA icon + name handling: every input must yield a usable icon or a clean fallback.

Pure unit tests, no DB or network.
"""
from io import BytesIO

import pytest
from PIL import Image

from app.api.services.pwa_service import TenantBrandingSnapshot, make_short_name
from app.utils.pwa_icons import fetch_logo, render_letter_icon_png, render_logo_icon_png


def _png(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _open(data: bytes) -> Image.Image:
    return Image.open(BytesIO(data)).convert("RGB")


def _distinct_colors(img: Image.Image) -> int:
    return len(img.getcolors(maxcolors=1_000_000) or [])


def _snapshot(name: str, **kw) -> TenantBrandingSnapshot:
    base = dict(slug="acme", company_name=name, favicon_url=None, logo_url=None,
                theme_color="#000000", background_color="#000000", accent_color="#7c3aed")
    return TenantBrandingSnapshot(**{**base, **kw})


@pytest.mark.parametrize("size,maskable", [(192, False), (512, False), (512, True), (180, False)])
def test_non_square_transparent_logo_is_centred_and_square(size, maskable):
    logo = Image.new("RGBA", (500, 200), (0, 0, 0, 0))
    logo.paste((200, 30, 30, 255), (50, 50, 450, 150))
    out = _open(render_logo_icon_png(_png(logo), size, "#101010", maskable))
    assert out.size == (size, size)
    assert out.getpixel((size // 2, size // 2)) == (200, 30, 30)  # logo content is centred, not cropped away
    assert out.getpixel((2, 2)) == (16, 16, 16)  # solid brand background, no transparency


def test_maskable_artwork_stays_inside_safe_circle():
    # Transparent corners so the logo is not treated as a full-bleed icon.
    logo = Image.new("RGBA", (300, 300), (0, 0, 0, 0))
    logo.paste((255, 0, 0, 255), (50, 50, 250, 250))
    out = _open(render_logo_icon_png(_png(logo), 512, "#101010", maskable=True))
    # Square artwork's diagonal is capped at 80% of the canvas: side ~ 0.566, so it never reaches the corners.
    assert out.getpixel((40, 40)) == (16, 16, 16)
    assert out.getpixel((256, 256)) == (255, 0, 0)


def test_white_logo_on_white_brand_does_not_vanish():
    logo = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    logo.paste((255, 255, 255, 255), (50, 50, 150, 150))
    out = _open(render_logo_icon_png(_png(logo), 192, "#ffffff"))
    assert _distinct_colors(out) >= 2  # logo is visible against the flipped background


def test_opaque_square_icon_fills_canvas():
    icon = Image.new("RGBA", (256, 256), (10, 120, 200, 255))
    icon.paste((255, 255, 255, 255), (96, 96, 160, 160))
    out = _open(render_logo_icon_png(_png(icon), 192, "#000000"))
    assert out.getpixel((0, 0)) == (10, 120, 200)
    assert out.getpixel((96, 96)) == (255, 255, 255)


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"not an image",
        b"<svg xmlns='http://www.w3.org/2000/svg'/>",
        _png(Image.new("RGBA", (16, 16), (255, 0, 0, 255))),  # tiny
        _png(Image.new("RGBA", (300, 300), (0, 0, 0, 0))),  # fully transparent
        _png(Image.new("RGBA", (300, 300), (255, 255, 255, 255))),  # blank opaque
    ],
)
def test_unusable_logo_returns_none_so_caller_falls_back(data):
    assert render_logo_icon_png(data, 192, "#000000") is None


def test_letter_icon_is_readable_on_light_and_dark_brand():
    for bg in ("#ffffff", "#000000", "#7c3aed"):
        assert _distinct_colors(_open(render_letter_icon_png("A", 192, bg))) >= 2


@pytest.mark.parametrize(
    "url", ["http://example.com/a.png", "https://127.0.0.1/a.png", "https://localhost/a.png",
            "https://169.254.169.254/latest/meta-data", "file:///etc/passwd", "not a url", ""],
)
def test_fetch_logo_refuses_private_and_non_https_targets(url):
    assert fetch_logo(url) is None


@pytest.mark.parametrize(
    "name,expected",
    [
        ("BHS", "BHS"),
        ("Elvis Executive Cars", "Elvis"),
        ("Jane Skyline Chauffeur LLC", "Jane Skyline"),
        ("Supercalifragilistic Limousines", "Supercalifrag"[:12]),
        ("Café & Co", "Café & Co"),
    ],
)
def test_short_name_is_at_most_12_chars(name, expected):
    assert make_short_name(name) == expected
    assert len(make_short_name(name)) <= 12


def test_names_are_sanitised_and_never_empty():
    assert _snapshot("   ").display_name == "acme"  # empty name -> slug
    assert _snapshot("A\x00B​\n C").display_name == "A B C"
    assert len(_snapshot("word " * 30).display_name) <= 45
    assert _snapshot("\U0001F697\U0001F697").initial == "M"  # emoji-only name cannot render a letter
    assert _snapshot("Élite Cars").initial == "É"
    assert _snapshot("Tom & Jerry <b>").display_name == "Tom & Jerry <b>"  # JSON-encoded later, never HTML


def test_icon_version_changes_when_logo_is_reuploaded_to_same_url():
    a = _snapshot("Acme", logo_url="https://x/y.png", updated_on="2026-01-01")
    b = _snapshot("Acme", logo_url="https://x/y.png", updated_on="2026-02-01")
    assert a.version != b.version
