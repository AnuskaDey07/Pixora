"""NSFW detection using a fine-tuned Vision Transformer."""
from __future__ import annotations

import time
from typing import Any

from PIL import Image

from app.ml.base import MLResult

# Model is cached here so it loads once per worker, not per call.
_classifier = None
_MODEL_ID = "Falconsai/nsfw_image_detection"


def _load():
    """Load the model once and cache it."""
    global _classifier
    if _classifier is not None:
        return _classifier

    import torch
    from transformers import pipeline

    # Use GPU if available, otherwise CPU
    device = 0 if torch.cuda.is_available() else -1
    
    # Load the model
    _classifier = pipeline(
        "image-classification",
        model=_MODEL_ID,
        device=device,
    )
    return _classifier


def detect_nsfw(image: Image.Image, params: dict[str, Any]) -> MLResult:
    """Detect NSFW content and return scores.

    params:
        threshold (float, optional) — score above which is_vulgar is True.
            Default 0.7.

    meta:
        model: str
        elapsed_ms: int
        threshold: float
    """
    start = time.time()
    try:
        classifier = _load()
        src = image.convert("RGB")
        threshold = float(params.get("threshold", 0.7))

        # Run inference
        preds = classifier(src)
        
        # Convert list of dicts to a single dict: {"normal": 0.9, "nsfw": 0.1}
        scores = {p["label"]: float(p["score"]) for p in preds}
        nsfw_score = scores.get("nsfw", 0.0)

        # Build the output exactly as the stub does
        output_data = {
            "nsfw_score": nsfw_score,
            "categories": scores
        }
        
        return MLResult(
            ok=True,
            output=output_data,
            meta={
                "model": _MODEL_ID,
                "elapsed_ms": int((time.time() - start) * 1000),
                "threshold": threshold,
            },
        )
    except Exception as exc:
        # Catch every exception and return a clean error
        return MLResult(ok=False, error=str(exc))