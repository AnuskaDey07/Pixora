"""Pillow-based image helpers.

Pure functions. No DB, no storage. Inputs are bytes or PIL.Images.
"""
from __future__ import annotations

import io
from typing import Literal

from PIL import Image, UnidentifiedImageError

from app.config import get_settings


OutputFormat = Literal["PNG", "JPEG", "WEBP"]


class InvalidImageError(Exception):
    """Raised when bytes cannot be decoded as an image."""


def validate_image(data: bytes) -> tuple[Image.Image, str]:
    """Decode bytes to a PIL.Image. Returns (image, detected_mime).

    Raises InvalidImageError if bytes are not a valid image.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # force decode
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImageError(str(exc)) from exc

    fmt = (img.format or "PNG").upper()
    mime = {
        "PNG": "image/png",
        "JPEG": "image/jpeg",
        "JPG": "image/jpeg",
        "WEBP": "image/webp",
    }.get(fmt, "image/png")

    allowed = get_settings().allowed_mimes_set
    if mime not in allowed:
        raise InvalidImageError(f"unsupported mime: {mime}")

    return img, mime


def make_thumbnail(img: Image.Image, max_side: int = 256) -> bytes:
    """Return PNG-encoded thumbnail bytes."""
    thumb = img.copy()
    thumb.thumbnail((max_side, max_side), Image.LANCZOS)
    if thumb.mode not in ("RGB", "RGBA"):
        thumb = thumb.convert("RGBA")
    buf = io.BytesIO()
    thumb.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def resize_image(img: Image.Image, width: int, height: int) -> Image.Image:
    """Resize to exact dimensions using high-quality resampling."""
    return img.resize((width, height), Image.LANCZOS)


def convert_format(img: Image.Image, target: OutputFormat) -> bytes:
    """Encode a PIL.Image as bytes in the requested format."""
    out = img
    if target == "JPEG" and out.mode in ("RGBA", "P"):
        out = out.convert("RGB")
    buf = io.BytesIO()
    if target == "JPEG":
        out.save(buf, format="JPEG", quality=90, optimize=True)
    elif target == "WEBP":
        out.save(buf, format="WEBP", quality=90, method=6)
    else:
        out.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def encode_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
