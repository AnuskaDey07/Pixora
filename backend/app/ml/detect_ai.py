from PIL import Image
import time
import torch
from transformers import pipeline
from app.ml.base import MLResult

_model = None

def _load():
    global _model
    if _model is None:
        # We pick one of the strong detectors from your notebook
        # Note: In production, ensure this model is downloaded during the Docker build 
        # so it doesn't take 2 minutes on the first request.
        device = 0 if torch.cuda.is_available() else -1
        model_name = "umm-maybe/AI-image-detector" # One of the models from your notebook
        _model = pipeline("image-classification", model=model_name, device=device)
    return _model

def detect_ai(image: Image.Image, params: dict) -> MLResult:
    t0 = time.perf_counter()
    try:
        model = _load()
        
        # Ensure RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
            
        # Run inference (top_k=None gets all scores, similar to your notebook)
        results = model(image, top_k=None)
        
        # Calculate probability based on the notebook's logic
        # 'umm-maybe/AI-image-detector' labels are usually ['artificial', 'human']
        ai_prob = 0.0
        for r in results:
            label = r["label"].lower()
            if "artificial" in label or "ai" in label:
                ai_prob += r["score"]
            elif "human" in label or "real" in label:
                # If we find the real score, AI prob is 1 - real prob
                ai_prob = 1.0 - r["score"]
                
        is_ai = ai_prob > 0.5 # Standard threshold from your notebook

        return MLResult(
            ok=True,
            output={"ai_probability": round(ai_prob, 4), "is_ai_generated": is_ai},
            meta={"model": "umm-maybe/AI-image-detector", "elapsed_ms": int((time.perf_counter() - t0) * 1000)}
        )
    except Exception as exc:
        return MLResult(ok=False, error=str(exc))
