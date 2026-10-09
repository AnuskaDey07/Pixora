
from pathlib import Path
from PIL import Image
from rembg import remove


def remove_background(image_path, output_dir="outputs"):
    """
    Remove an image background and save a transparent PNG.
    Returns the output file path.
    """
    image_path = Path(image_path)

    if not image_path.is_file():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Image.open(image_path) as image:
        image = image.convert("RGBA")
        result = remove(image)

    output_path = output_dir / f"{image_path.stem}_no_background.png"
    result.save(output_path, format="PNG")

    return str(output_path)
