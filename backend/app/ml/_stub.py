"""Placeholder ML implementations for development.

Every function here mirrors the real signature Tapasi will deliver.
Returns a placeholder image or dict so the web layer can be exercised
end-to-end without models.

Set ML_STUB_MODE=false in .env when real models are wired in.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from app.ml.base import MLResult


def _placeholder(image: Image.Image, label: str) -> Image.Image:
    """Draw a labeled overlay so stub output is obviously fake."""
    out = image.convert("RGB").copy()
    draw = ImageDraw.Draw(out)
    w, h = out.size
    draw.rectangle([(0, 0), (w, 40)], fill=(79, 70, 229))
    draw.text((10, 12), f"[STUB] {label}", fill=(255, 255, 255))
    return out


def remove_background(image: Image.Image, params: dict) -> MLResult:
    """Stub: returns image with fake alpha (RGBA)."""
    return MLResult(
        ok=True,
        output=_placeholder(image, "remove_background").convert("RGBA"),
        meta={"model": "stub", "elapsed_ms": 5},
    )


def inpaint(image: Image.Image, params: dict) -> MLResult:
    """Stub: returns image unchanged with overlay."""
    return MLResult(
        ok=True,
        output=_placeholder(image, "inpaint"),
        meta={"model": "stub", "elapsed_ms": 5},
    )


def generate(image: Image.Image | None, params: dict) -> MLResult:
    """Stub: returns a solid color image with the prompt drawn on it."""
    w = int(params.get("width", 512))
    h = int(params.get("height", 512))
    out = Image.new("RGB", (w, h), (30, 41, 59))
    draw = ImageDraw.Draw(out)
    prompt = params.get("prompt", "(no prompt)")
    draw.text((20, 20), f"[STUB] generate\n{prompt[:60]}", fill=(226, 232, 240))
    return MLResult(
        ok=True,
        output=out,
        meta={"model": "stub", "elapsed_ms": 5, "prompt": prompt},
    )


def img2img(image: Image.Image, params: dict) -> MLResult:
    return MLResult(
        ok=True,
        output=_placeholder(image, "img2img"),
        meta={"model": "stub", "elapsed_ms": 5},
    )


def controlnet_scribble(image: Image.Image, params: dict) -> MLResult:
    return MLResult(
        ok=True,
        output=_placeholder(image, "controlnet_scribble"),
        meta={"model": "stub", "elapsed_ms": 5},
    )


def detect_nsfw(image: Image.Image, params: dict) -> MLResult:
    return MLResult(
        ok=True,
        output={"nsfw_score": 0.02, "categories": {"explicit": 0.01, "suggestive": 0.02}},
        meta={"model": "stub", "threshold": 0.5},
    )


def detect_ai(image: Image.Image, params: dict) -> MLResult:
    return MLResult(
        ok=True,
        output={"ai_probability": 0.5, "is_ai_generated": False},
        meta={"model": "stub"},
    )


def detect_objects(image: Image.Image, params: dict) -> MLResult:
    return MLResult(
        ok=True,
        output={"objects": []},
        meta={"model": "stub"},
    )


def embed(image: Image.Image, params: dict) -> MLResult:
    """Stub: deterministic non-zero 512-dim vector derived from image bytes.

    Real CLIP embeddings capture semantic content. This stub produces a
    reproducible vector so cosine distance is defined (no NaN) and similar
    images rank closer together for demo purposes.
    """
    import hashlib

    h = hashlib.sha256(image.tobytes()[:4096]).digest()
    # Expand the 32-byte hash to 512 floats in [-1, 1]
    vec = [((h[i % len(h)] / 127.5) - 1.0) for i in range(512)]
    # L2 normalize so cosine distance grep -A 15 "def embed" backend/app/ml/_stub.py | head -25= 1 - dot product
    norm = sum(v * v for v in vec) ** 0.5 or 1.0
    vec = [v / norm for v in vec]

    return MLResult(
        ok=True,
        output={"vector": vec, "dim": 512},
        meta={"model": "stub-deterministic"},
    )

