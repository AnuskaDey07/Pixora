"""Background removal — real implementation using rembg + U2Net.

Returns an RGBA PIL.Image with background removed.
Supports optional background replacement:
  params["replace_with"]:
    - a hex color string like "#ffffff" or "white" → solid color fill
    - a PIL.Image or bytes → used as background image (scaled + center-cropped)
    - None / missing → transparent background
"""
from __future__ import annotations

import io
import logging
import time

from PIL import Image

from app.ml.base import MLResult

log = logging.getLogger(__name__)

_session = None


def _load():
    """Load U2Net session once. Cached in module state."""
    global _session
    if _session is None:
        from rembg import new_session
        log.info("remove_bg: loading u2net session")
        _session = new_session("u2net")
        log.info("remove_bg: session ready")
    return _session


def _fit_background(bg: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Scale bg to cover size (like CSS cover), then center-crop."""
    width, height = size
    bg = bg.convert("RGBA")
    scale = max(width / bg.width, height / bg.height)
    new_w = round(bg.width * scale)
    new_h = round(bg.height * scale)
    bg = bg.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - width) // 2
    top = (new_h - height) // 2
    return bg.crop((left, top, left + width, top + height))


def remove_background(image: Image.Image, params: dict) -> MLResult:
    """Remove background, optionally replace it.

    params:
        replace_with: hex color str OR PIL.Image OR bytes.
                      None → transparent background.
    """
    t0 = time.perf_counter()
    try:
        from rembg import remove

        session = _load()

        if image.mode != "RGBA":
            image = image.convert("RGBA")

        # Step 1: remove background (from your notebook)
        foreground = remove(image, session=session)

        # Step 2: optional background replacement (from your notebook)
        replace_with = params.get("replace_with") if params else None
        if replace_with is not None:
            if isinstance(replace_with, (bytes, bytearray)):
                bg_img = Image.open(io.BytesIO(replace_with))
                background = _fit_background(bg_img, foreground.size)
            elif isinstance(replace_with, Image.Image):
                background = _fit_background(replace_with, foreground.size)
            elif isinstance(replace_with, str):
                # solid color fill
                background = Image.new("RGBA", foreground.size, replace_with)
            else:
                return MLResult(
                    ok=False,
                    error=f"Unsupported replace_with type: {type(replace_with).__name__}",
                )

            out = Image.alpha_composite(background, foreground)
        else:
            out = foreground  # transparent background

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return MLResult(
            ok=True,
            output=out,
            meta={
                "model": "u2net",
                "elapsed_ms": elapsed_ms,
                "replaced_bg": replace_with is not None,
            },
        )
    except Exception as exc:
        log.exception("remove_bg: failed")
        return MLResult(ok=False, error=f"{type(exc).__name__}: {exc}")
