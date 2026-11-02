"""Object detection — real implementation using Ultralytics YOLO.

Returns {"objects": [{"label": str, "confidence": float, "bbox": [x1,y1,x2,y2]}]}
"""
from __future__ import annotations

import logging
import time

from PIL import Image

from app.ml.base import MLResult

log = logging.getLogger(__name__)

_MODEL_NAME = "yolo11n.pt"
_model = None


def _load():
    global _model
    if _model is None:
        from ultralytics import YOLO
        log.info("detect_objects: loading %s", _MODEL_NAME)
        _model = YOLO(_MODEL_NAME)
        log.info("detect_objects: model ready")
    return _model


def detect_objects(image: Image.Image, params: dict) -> MLResult:
    t0 = time.perf_counter()
    try:
        model = _load()

        if image.mode != "RGB":
            image = image.convert("RGB")

        conf = float(params.get("confidence_threshold", 0.25))
        imgsz = int(params.get("image_size", 1280))
        iou = float(params.get("iou", 0.5))

        import numpy as np
        arr = np.array(image)

        result = model.predict(
            source=arr,
            conf=conf,
            imgsz=imgsz,
            iou=iou,
            verbose=False,
        )[0]

        objects = []
        for box in result.boxes:
            class_id = int(box.cls[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            objects.append({
                "label": result.names[class_id],
                "confidence": round(float(box.conf[0].item()), 4),
                "bbox": [round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            })

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return MLResult(
            ok=True,
            output={"objects": objects},
            meta={
                "model": _MODEL_NAME,
                "elapsed_ms": elapsed_ms,
                "count": len(objects),
                "image_width": image.width,
                "image_height": image.height,
            },
        )
    except Exception as exc:
        log.exception("detect_objects: failed")
        return MLResult(ok=False, error=f"{type(exc).__name__}: {exc}")
