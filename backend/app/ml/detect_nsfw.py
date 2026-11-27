"""NSFW detection with regional blurring using ViT, NudeNet, and YOLO."""
from __future__ import annotations

import io
import time
from typing import Any
import numpy as np
import cv2

from PIL import Image

from app.ml.base import MLResult

_classifier = None
_nudenet_detector = None
_yolo_model = None

_MODEL_ID = "Falconsai/nsfw_image_detection"
_EXPLICIT_CLASSES = [
    'FEMALE_BREAST_EXPOSED', 'FEMALE_GENITALIA_EXPOSED', 
    'MALE_GENITALIA_EXPOSED', 'BUTTOCKS_EXPOSED'
]

def _load():
    global _classifier, _nudenet_detector, _yolo_model
    if _classifier is not None:
        return _classifier, _nudenet_detector, _yolo_model

    import torch
    from transformers import pipeline
    from nudenet import NudeDetector
    from ultralytics import YOLO

    device = 0 if torch.cuda.is_available() else -1
    
    _classifier = pipeline("image-classification", model=_MODEL_ID, device=device)
    _nudenet_detector = NudeDetector()
    _yolo_model = YOLO("yolov8n.pt")
    
    return _classifier, _nudenet_detector, _yolo_model


def detect_nsfw(image: Image.Image, params: dict[str, Any]) -> MLResult:
    start = time.time()
    try:
        classifier, nudenet, yolo = _load()
        threshold = float(params.get("threshold", 0.7))
        
        src = image.convert("RGB")
        
        preds = classifier(src)
        scores = {p["label"]: float(p["score"]) for p in preds}
        nsfw_score = scores.get("nsfw", 0.0)
        is_vulgar = nsfw_score >= threshold
        
        blurred_image = None
        
        if is_vulgar:
            img_cv2 = cv2.cvtColor(np.array(src), cv2.COLOR_RGB2BGR)
            blurred_count = 0
            
            detections = nudenet.detect(img_cv2)
            for detection in detections:
                if detection['class'] in _EXPLICIT_CLASSES:
                    x, y, w, h = detection['box']
                    region = img_cv2[y:y+h, x:x+w]
                    if region.size > 0:
                        img_cv2[y:y+h, x:x+w] = cv2.GaussianBlur(region, (99, 99), 30)
                    blurred_count += 1
            
            if blurred_count == 0:
                results = yolo(img_cv2)
                for box in results[0].boxes:
                    if int(box.cls[0]) == 0:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        region = img_cv2[y1:y2, x1:x2]
                        if region.size > 0:
                            img_cv2[y1:y2, x1:x2] = cv2.GaussianBlur(region, (99, 99), 30)
                        blurred_count += 1
            
            final_img = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
            blurred_image = Image.fromarray(final_img)
        else:
            blurred_image = src

        categories = {
            "explicit": scores.get("nsfw", 0.0) * 0.7,
            "suggestive": scores.get("nsfw", 0.0) * 0.3
        }

        return MLResult(
            ok=True,
            output=blurred_image,
            meta={
                "nsfw_score": nsfw_score,
                "is_vulgar": is_vulgar,
                "categories": categories,
                "model": _MODEL_ID,
                "elapsed_ms": int((time.time() - start) * 1000)
            },
        )
    except Exception as exc:
        return MLResult(ok=False, error=str(exc))
