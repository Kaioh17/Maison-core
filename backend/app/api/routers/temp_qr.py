from io import BytesIO
import re

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response

from app.api.core.rate_limit import limiter
from app.utils.qr_code import custom_qrcode


router = APIRouter(
    prefix="/api/v1/tools/temp-qr",
    tags=["Tools"],
)

HEX_COLOR_RE = re.compile(r"^#?[0-9a-fA-F]{3}([0-9a-fA-F]{3})?$")
NAMED_COLOR_RE = re.compile(r"^[a-zA-Z]{3,20}$")
MAX_URL_LENGTH = 2048


def validate_target_url(url: str) -> str:
    """This endpoint is public, so only bounded http(s) links are encoded."""
    url = url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")
    if len(url) > MAX_URL_LENGTH:
        raise HTTPException(status_code=400, detail=f"url must be at most {MAX_URL_LENGTH} characters")
    if not re.match(r"^https?://", url, re.IGNORECASE):
        raise HTTPException(status_code=400, detail="url must start with http:// or https://")
    return url


def normalize_color_value(value: str) -> str:
    color = value.strip()
    if not color:
        raise HTTPException(status_code=400, detail="Color value cannot be empty")

    if HEX_COLOR_RE.fullmatch(color):
        return color if color.startswith("#") else f"#{color}"
    if NAMED_COLOR_RE.fullmatch(color):
        return color.lower()

    raise HTTPException(status_code=400, detail="Colors must be hex (#rrggbb) or a simple color name")


@router.get(
    "/editor",
    response_class=HTMLResponse,
    summary="Temporary QR editor",
    description=(
        "Temporary side editor for generating QR images with custom URL and colors. "
        "This route is isolated from the primary QR code generation flow."
    ),
)
async def temp_qr_editor() -> str:
    return """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Temporary QR Editor</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; max-width: 900px; }
    h1 { margin-bottom: 8px; }
    .row { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin: 10px 0; }
    input[type="text"] { width: 100%; max-width: 620px; padding: 8px; }
    .panel { border: 1px solid #ddd; border-radius: 8px; padding: 14px; margin-top: 12px; }
    button { padding: 8px 12px; cursor: pointer; }
    #preview { margin-top: 16px; width: 300px; height: 300px; object-fit: contain; border: 1px solid #eee; }
    .hint { color: #666; font-size: 14px; }
  </style>
</head>
<body>
  <h1>Temporary QR Editor</h1>
  <p class="hint">Isolated route for quick QR customization (URL + colors).</p>

  <div class="panel">
    <div class="row">
      <label for="url"><strong>URL:</strong></label>
      <input id="url" type="text" value="https://example.com" />
    </div>
    <div class="row">
      <label for="fill"><strong>Fill color:</strong></label>
      <input id="fill" type="color" value="#000000" />
      <label for="bg"><strong>Background color:</strong></label>
      <input id="bg" type="color" value="#ffffff" />
      <button id="generate" type="button">Generate</button>
    </div>
    <div class="row">
      <a id="download" href="#" download="temp-qr.png">Download PNG</a>
    </div>
    <img id="preview" alt="QR Preview" />
  </div>

  <script>
    const urlInput = document.getElementById("url");
    const fillInput = document.getElementById("fill");
    const bgInput = document.getElementById("bg");
    const generateButton = document.getElementById("generate");
    const preview = document.getElementById("preview");
    const download = document.getElementById("download");

    function updatePreview() {
      const url = encodeURIComponent(urlInput.value.trim());
      const fill = encodeURIComponent(fillInput.value);
      const bg = encodeURIComponent(bgInput.value);
      const src = `/api/v1/tools/temp-qr/generate?url=${url}&fill_color=${fill}&back_color=${bg}&_=${Date.now()}`;
      preview.src = src;
      download.href = src;
    }

    generateButton.addEventListener("click", updatePreview);
    updatePreview();
  </script>
</body>
</html>
"""


@router.get(
    "/generate",
    summary="Generate temporary QR PNG",
    description="Generate a QR PNG from a custom URL with custom fill and background colors.",
)
@limiter.limit("30/minute")
async def temp_qr_generate(
    request: Request,
    url: str = Query(..., description="Target URL encoded into the QR code."),
    fill_color: str = Query("black", description="Foreground color (e.g. black or #000000)."),
    back_color: str = Query("white", description="Background color (e.g. white or #ffffff)."),
):
    url = validate_target_url(url)

    try:
        normalized_fill = normalize_color_value(fill_color)
        normalized_background = normalize_color_value(back_color)
        image = custom_qrcode(
            url=url,
            fill_color=normalized_fill,
            back_color=normalized_background,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid QR input") from exc

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return Response(content=buffer.getvalue(), media_type="image/png")


@router.get(
    "/download",
    summary="Download temporary QR PNG",
    description="Generate and download a QR PNG from a custom URL with custom fill and background colors.",
)
@limiter.limit("30/minute")
async def temp_qr_download(
    request: Request,
    url: str = Query(..., description="Target URL encoded into the QR code."),
    fill_color: str = Query("black", description="Foreground color (e.g. black or #000000)."),
    back_color: str = Query("white", description="Background color (e.g. white or #ffffff)."),
):
    url = validate_target_url(url)

    try:
        normalized_fill = normalize_color_value(fill_color)
        normalized_background = normalize_color_value(back_color)
        image = custom_qrcode(
            url=url,
            fill_color=normalized_fill,
            back_color=normalized_background,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid QR input") from exc

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={"Content-Disposition": 'attachment; filename="temp-qr.png"'},
    )
