"""Object detection — hybrid YOLO11x (COCO) + YOLOE (curated open vocabulary),
with automatic zoom-out passes for close-up images.

Params (all optional):
  confidence_threshold : float (default 0.3)
  iou                  : float (default 0.5)
  image_size           : int   (default 1024)
  classes              : list[str] | "a, b, c"  -> extra classes added to the open vocabulary
  only_classes         : bool  (default False)  -> open-vocab pass uses ONLY `classes`
  open_vocab           : bool  (default True)   -> False = COCO only (fastest)
  zoom_mode            : "auto" | "always" | "off"  (default "auto")
  max_det              : int   (default 100)
  augment              : bool  (default False)

Returns {"objects": [{"label": str, "confidence": float, "bbox": [x1,y1,x2,y2]}]}
"""
from __future__ import annotations

import logging
import threading
import time

import numpy as np
from PIL import Image

from app.ml.base import MLResult

log = logging.getLogger(__name__)

_COCO_WEIGHTS = "yolo11x.pt"
_YOLOE_WEIGHTS = "yoloe-11l-seg.pt"

# Extra border per side (fraction of image size) used to "zoom out" close-ups.
_PAD_LEVELS = (0.5, 1.0)

# Objects NOT in COCO's 80 classes (COCO is handled by YOLO11x).
# Keep this under ~300 entries: very large vocabularies reduce open-vocab accuracy.
_EXTRA_VOCAB = [
    # animals
    "lion", "tiger", "leopard", "fox", "wolf", "deer", "rabbit", "squirrel", "monkey", "pig",
    "goat", "duck", "chicken", "eagle", "owl", "parrot", "penguin", "dolphin", "shark", "fish",
    "turtle", "snake", "frog", "butterfly", "camel", "panda", "kangaroo", "buffalo", "hamster",
    "crab", "lobster", "jellyfish", "peacock", "swan", "crow", "rat", "lizard", "spider",
    # people / clothing
    "face", "hand", "hat", "cap", "helmet", "sunglasses", "glasses", "shirt", "jacket", "dress",
    "shoe", "boot", "sandal", "sock", "glove", "scarf", "watch", "jewelry", "necklace", "backpack",
    # vehicles / transport
    "van", "taxi", "ambulance", "fire truck", "tractor", "scooter", "rickshaw", "helicopter",
    "ship", "sailboat", "submarine", "wheel", "tire", "license plate", "steering wheel",
    # household / furniture
    "table", "desk", "sofa", "armchair", "stool", "shelf", "cabinet", "drawer", "lamp",
    "chandelier", "curtain", "pillow", "blanket", "carpet", "mirror", "painting", "picture frame",
    "clock", "fan", "air conditioner", "heater", "door", "window", "stairs", "fence", "gate",
    # kitchen / food
    "plate", "bowl", "mug", "glass", "jar", "kettle", "pan", "pot", "frying pan", "chopsticks",
    "pizza", "burger", "bread", "egg", "rice", "noodles", "soup", "salad", "fries", "cookie",
    "ice cream", "chocolate", "tomato", "potato", "onion", "lemon", "grape", "strawberry",
    "watermelon", "pineapple", "mango", "coconut", "mushroom", "coffee", "tea", "juice",
    "water bottle",
    # electronics / office
    "monitor", "headphones", "earbuds", "speaker", "camera", "tablet", "smartwatch", "charger",
    "cable", "printer", "projector", "microphone", "router", "drone", "game controller",
    "notebook", "pen", "pencil", "paper", "envelope", "folder", "calculator", "stapler",
    "scissors",
    # tools / sports / misc
    "hammer", "screwdriver", "wrench", "drill", "ladder", "bucket", "rope", "key", "lock", "coin",
    "wallet", "bag", "box", "bottle", "can", "candle", "balloon", "gift", "flag", "sign",
    "traffic cone", "street light", "mailbox", "fire hydrant", "bench",
    "guitar", "piano", "drum", "violin", "dumbbell", "football", "basketball", "cricket bat",
    "bicycle helmet", "toy", "doll", "book", "newspaper", "poster",
    # outdoors
    "tree", "flower", "plant", "leaf", "grass", "rock", "building", "house", "tower", "bridge",
    "tent", "windmill", "statue", "fountain", "road sign", "pole", "cloud", "mountain",
]

_coco_model = None
_yoloe_model = None
_yoloe_classes: tuple[str, ...] = ()
_lock = threading.Lock()


# --------------------------------------------------------------------------- #
# Model loading
# --------------------------------------------------------------------------- #
def _device():
    try:
        import torch
        return 0 if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _parse_classes(raw) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, str):
        raw = raw.split(",")
    seen, out = set(), []
    for c in raw:
        c = str(c).strip().lower()
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def _get_coco():
    global _coco_model
    if _coco_model is None:
        from ultralytics import YOLO
        log.info("detect_objects: loading %s", _COCO_WEIGHTS)
        _coco_model = YOLO(_COCO_WEIGHTS)
    return _coco_model


def _get_yoloe(names: list[str]):
    global _yoloe_model, _yoloe_classes
    if _yoloe_model is None:
        from ultralytics import YOLOE
        log.info("detect_objects: loading %s", _YOLOE_WEIGHTS)
        _yoloe_model = YOLOE(_YOLOE_WEIGHTS)
    key = tuple(names)
    if key != _yoloe_classes:
        _yoloe_model.set_classes(names, _yoloe_model.get_text_pe(names))
        _yoloe_classes = key
    return _yoloe_model


# --------------------------------------------------------------------------- #
# Inference helpers
# --------------------------------------------------------------------------- #
def _run(model, arr, source: str, **kw) -> list[dict]:
    result = model.predict(source=arr, verbose=False, device=_device(), **kw)[0]
    out = []
    for box in result.boxes:
        cid = int(box.cls[0].item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        out.append({
            "label": result.names[cid],
            "confidence": float(box.conf[0].item()),
            "bbox": [x1, y1, x2, y2],
            "source": source,
        })
    return out


def _run_padded(model, arr, source: str, frac: float, **kw) -> list[dict]:
    """Run detection on a gray-padded copy (zoomed out) and map boxes back."""
    h, w = arr.shape[:2]
    ph, pw = int(h * frac), int(w * frac)
    padded = np.full((h + 2 * ph, w + 2 * pw, 3), 114, dtype=np.uint8)
    padded[ph:ph + h, pw:pw + w] = arr

    out = []
    for d in _run(model, padded, source, **kw):
        x1, y1, x2, y2 = d["bbox"]
        x1, x2 = min(max(x1 - pw, 0), w), min(max(x2 - pw, 0), w)
        y1, y2 = min(max(y1 - ph, 0), h), min(max(y2 - ph, 0), h)
        if x2 - x1 < 2 or y2 - y1 < 2:
            continue
        d["bbox"] = [x1, y1, x2, y2]
        out.append(d)
    return out


def _looks_zoomed(dets: list[dict], w: int, h: int) -> bool:
    """Heuristic: nothing found, or a detection touches the image border."""
    if not dets:
        return True
    m = 0.015
    for d in dets:
        x1, y1, x2, y2 = d["bbox"]
        if x1 <= w * m or y1 <= h * m or x2 >= w * (1 - m) or y2 >= h * (1 - m):
            return True
    return False


# --------------------------------------------------------------------------- #
# Box math + merging
# --------------------------------------------------------------------------- #
def _area(b) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _iou(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = _area(a) + _area(b) - inter
    return inter / union if union > 0 else 0.0


def _containment(inner, outer) -> float:
    """Fraction of `inner` that lies inside `outer`."""
    ix1, iy1 = max(inner[0], outer[0]), max(inner[1], outer[1])
    ix2, iy2 = min(inner[2], outer[2]), min(inner[3], outer[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    area = _area(inner)
    return inter / area if area > 0 else 0.0


def _merge(dets: list[dict], iou_thr: float) -> list[dict]:
    """Greedy merge. COCO detections get a ranking boost so their labels win on overlaps."""
    def rank(d):
        return d["confidence"] + (0.15 if d["source"] == "coco" else 0.0)

    kept: list[dict] = []
    for d in sorted(dets, key=rank, reverse=True):
        dup = False
        for k in kept:
            same_label = d["label"] == k["label"]
            # same object seen by both models, or a duplicate box with the same label
            if _iou(d["bbox"], k["bbox"]) > (iou_thr if same_label else 0.7):
                dup = True
                break
            # lower-confidence box almost entirely inside a kept box of the same label
            if same_label and _containment(d["bbox"], k["bbox"]) > 0.9:
                dup = True
                break
        if not dup:
            kept.append(d)
    return kept


def _drop_fragments(dets: list[dict]) -> list[dict]:
    """Remove partial boxes sitting inside a larger box of the same label."""
    keep = []
    for d in dets:
        frag = False
        for o in dets:
            if o is d or o["label"] != d["label"]:
                continue
            if (
                _containment(d["bbox"], o["bbox"]) > 0.85
                and o["confidence"] >= 0.8 * d["confidence"]
                and _area(o["bbox"]) > _area(d["bbox"]) * 1.2
            ):
                frag = True
                break
        if not frag:
            keep.append(d)
    return keep


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def detect_objects(image: Image.Image, params: dict) -> MLResult:
    t0 = time.perf_counter()
    try:
        if image.mode != "RGB":
            image = image.convert("RGB")

        conf = float(params.get("confidence_threshold", 0.3))
        iou = float(params.get("iou", 0.5))
        imgsz = int(params.get("image_size", 1024))
        max_det = int(params.get("max_det", 100))
        augment = bool(params.get("augment", False))
        open_vocab = bool(params.get("open_vocab", True))
        only = bool(params.get("only_classes", False))
        zoom_mode = str(params.get("zoom_mode", "auto")).lower()  # auto | always | off
        user_classes = _parse_classes(params.get("classes"))

        arr = np.array(image)
        h, w = arr.shape[:2]

        # Open-vocab scores run lower than COCO scores, so give them a lower floor.
        yoloe_floor = max(0.05, conf - 0.1)
        common = dict(iou=iou, imgsz=imgsz, max_det=max_det, augment=augment)

        def detect_all(frac: float) -> list[dict]:
            if frac == 0:
                runner = lambda m, s, **k: _run(m, arr, s, **k)  # noqa: E731
            else:
                runner = lambda m, s, **k: _run_padded(m, arr, s, frac, **k)  # noqa: E731

            found: list[dict] = []
            # Pass 1 — COCO specialist (reliable labels for common objects)
            if not (only and user_classes):
                found += runner(_get_coco(), "coco", conf=conf, agnostic_nms=False, **common)
            # Pass 2 — open vocabulary with a curated list (not noisy prompt-free tags)
            if open_vocab:
                try:
                    vocab = user_classes if (only and user_classes) else \
                        list(dict.fromkeys(user_classes + _EXTRA_VOCAB))
                    found += runner(_get_yoloe(vocab), "yoloe", conf=yoloe_floor,
                                    agnostic_nms=False, **common)
                except Exception:
                    log.exception("detect_objects: open-vocab pass failed; COCO only")
            return found

        used: list[str] = []
        dets: list[dict] = []
        with _lock:  # ultralytics models / set_classes are not thread-safe
            dets += detect_all(0.0)
            if zoom_mode == "always" or (zoom_mode == "auto" and _looks_zoomed(dets, w, h)):
                if zoom_mode != "off":
                    for frac in _PAD_LEVELS:
                        dets += detect_all(frac)
                    used.append(f"zoom-out passes {_PAD_LEVELS}")

        used += ([_COCO_WEIGHTS] if not (only and user_classes) else [])
        used += ([_YOLOE_WEIGHTS] if open_vocab else [])

        # Per-source final threshold
        dets = [
            d for d in dets
            if d["confidence"] >= (conf if d["source"] == "coco" else yoloe_floor)
        ]

        merged = _drop_fragments(_merge(dets, iou))
        merged.sort(key=lambda d: d["confidence"], reverse=True)
        merged = merged[:max_det]

        objects = [
            {
                "label": d["label"],
                "confidence": round(d["confidence"], 4),
                "bbox": [round(v, 2) for v in d["bbox"]],
            }
            for d in merged
        ]

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        return MLResult(
            ok=True,
            output={"objects": objects},
            meta={
                "models": used,
                "elapsed_ms": elapsed_ms,
                "count": len(objects),
                "image_width": image.width,
                "image_height": image.height,
            },
        )
    except Exception as exc:
        log.exception("detect_objects: failed")
        return MLResult(ok=False, error=f"{type(exc).__name__}: {exc}")