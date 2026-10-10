"""
NSFW image classification starter module.

This module uses a pretrained Hugging Face image-classification model to estimate
whether an image contains NSFW / explicit content. It returns the predicted label
and confidence score. If the result is classified as NSFW, it can optionally save
a fully blurred copy of the image.

Install dependencies:
    pip install transformers torch pillow

Important:
- Model labels and output formats differ by checkpoint. Verify the selected model's
  label mapping and model card before using it in production.
- This starter uses Falconsai/nsfw_image_detection as an example checkpoint.
- A classifier usually scores the whole image; it does not locate the exact explicit
  region. Use a separate region detector if you need localized blurring.
"""

from pathlib import Path
from PIL import Image, ImageFilter
from transformers import pipeline


DEFAULT_MODEL_NAME = "Falconsai/nsfw_image_detection"


def handle_nsfw_image(
    image_path,
    output_dir="outputs",
    threshold=0.60,
    model_name=DEFAULT_MODEL_NAME,
    classifier=None,
    blur_if_nsfw=True,
    blur_radius=24,
):
    """
    Classify an image as NSFW or normal using a pretrained image classifier.

    Args:
        image_path: Input image file path.
        output_dir: Folder where the optional blurred image will be saved.
        threshold: Minimum NSFW score (0.0 to 1.0) to flag the image.
        model_name: Hugging Face image-classification checkpoint.
        classifier: Optional existing transformers pipeline to reuse.
        blur_if_nsfw: If True, save a fully blurred copy when flagged.
        blur_radius: Gaussian blur radius used for the whole image.

    Returns:
        Dictionary with predicted labels/scores and optional output image path.
    """
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0.0 and 1.0")
    if blur_radius <= 0:
        raise ValueError("blur_radius must be greater than 0")

    with Image.open(image_path) as opened_image:
        image = opened_image.convert("RGB")

    if classifier is None:
        classifier = pipeline(
            task="image-classification",
            model=model_name,
        )

    predictions = classifier(image)
    normalized_predictions = []
    nsfw_score = 0.0

    for prediction in predictions:
        label = str(prediction.get("label", "unknown"))
        score = float(prediction.get("score", 0.0))
        normalized_predictions.append({
            "label": label,
            "confidence": round(score, 4),
        })

        # The example checkpoint commonly uses labels "nsfw" and "normal".
        # Case-insensitive matching is used; verify the model card if labels differ.
        if label.strip().lower() in {"nsfw", "explicit", "porn", "unsafe"}:
            nsfw_score = max(nsfw_score, score)

    is_nsfw = nsfw_score >= threshold
    output_path = None

    if is_nsfw and blur_if_nsfw:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{image_path.stem}_nsfw_blurred.jpg"
        blurred = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        blurred.save(output_path, format="JPEG", quality=95)

    return {
        "input_image": str(image_path),
        "model_name": model_name,
        "is_nsfw": is_nsfw,
        "nsfw_score": round(nsfw_score, 4),
        "threshold": threshold,
        "predictions": normalized_predictions,
        "blurred_image": str(output_path) if output_path else None,
        "note": (
            "The classifier scores the whole image; the blur covers the whole image. "
            "This is not a localized body-region detector."
        ),
    }


if __name__ == "__main__":
    # Example:
    # result = handle_nsfw_image("sample.jpg")
    # print(result)
    print("Import handle_nsfw_image() and call it with an image path.")
