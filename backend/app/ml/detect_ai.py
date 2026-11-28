from PIL import Image
import time
import torch
from transformers import pipeline
from app.ml.base import MLResult

_MODEL_ID = "Ateeqq/ai-vs-human-image-detector"
_model = None

def _load():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _model = pipeline("image-classification", model=_MODEL_ID, device=device)
    return _model

def detect_ai(image: Image.Image, params: dict) -> MLResult:
    t0 = time.perf_counter()
    try:
        model = _load()

        if image.mode != "RGB":
            image = image.convert("RGB")

        results = model(image, top_k=None)

        ai_prob = 0.0
        for r in results:
            label = r["label"].lower()
            # The new model returns labels like "ai" and "human"
            # We also check for "artificial" and "fake" just to be safe
            if "artificial" in label or "ai" in label or "fake" in label:
                ai_prob = r["score"]
                break

        threshold = float(params.get("threshold", 0.5))
        is_ai = ai_prob >= threshold

        return MLResult(
            ok=True,
            output={"ai_probability": round(ai_prob, 4), "is_ai_generated": is_ai},
            meta={
                "model": _MODEL_ID,
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        )
    except Exception as exc:
        return MLResult(ok=False, error=str(exc))