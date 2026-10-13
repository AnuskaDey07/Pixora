
from pathlib import Path
from ultralytics import YOLO
import cv2

def detect_objects(
    image_path,
    output_dir="outputs",
    confidence=0.25,
    image_size=1280,
    iou=0.5,
    model=None
):
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if model is None:
        model = YOLO("yolo26n.pt")

    result = model.predict(
        source=str(image_path),
        conf=confidence,
        imgsz=image_size,
        iou=iou,
        verbose=False
    )[0]

    output_path = output_dir / f"{image_path.stem}_detected.jpg"

    if not cv2.imwrite(str(output_path), result.plot()):
        raise OSError("Could not save annotated image")

    detections = []

    for box in result.boxes:
        class_id = int(box.cls[0].item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        detections.append({
            "label": result.names[class_id],
            "confidence": round(float(box.conf[0].item()), 4),
            "bbox": {
                "x1": round(x1, 2),
                "y1": round(y1, 2),
                "x2": round(x2, 2),
                "y2": round(y2, 2)
            }
        })

    height, width = result.orig_shape

    return {
        "annotated_image": str(output_path),
        "image_width": width,
        "image_height": height,
        "total_detections": len(detections),
        "detections": detections
    }
