# Pixora — ML contracts

Every function the web layer calls lives under backend/app/ml/ and obeys base.py.
This file documents each function's params and meta dict.

## Signature convention

    def <name>(image: Image.Image, params: dict) -> MLResult: ...

- Input image: RGB PIL image, already loaded by the Celery task.
- Input params: JSON-serializable dict; keys documented below.
- Output MLResult: always returned; never raise.

## Common meta keys

- model — string, model identifier used
- elapsed_ms — int, wall-clock inference time
- version — string, model version

---

## Feature contracts

### remove_background(image, params)

Params:
- replace_with (str, optional) — "transparent" (default) or hex color

Returns: MLResult.output = RGBA PIL.Image with alpha channel.
Meta: model, elapsed_ms.

---

### inpaint(image, mask, params)

Params:
- prompt (str)
- steps (int, default 30)
- guidance (float, default 7.5)

Returns: MLResult.output = RGB PIL.Image, same size as input.

---

### generate(image, params)  # text-to-image, image ignored

Params:
- prompt (str, required)
- negative_prompt (str, optional)
- width, height (int, defaults 512)
- steps, guidance, seed

Returns: MLResult.output = RGB PIL.Image.

---

### img2img(image, params)

Params:
- prompt (str, required)
- strength (float, 0.0-1.0, default 0.75)
- steps, guidance, seed

Returns: MLResult.output = RGB PIL.Image.

---

### controlnet_scribble(image, params)

Params:
- prompt (str, required)
- control_strength (float, default 1.0)

Returns: MLResult.output = RGB PIL.Image.

---

### detect_nsfw(image, params)

Params: none required.

Returns: MLResult.output = dict: { "nsfw_score": 0.03, "categories": { "explicit": 0.01, "suggestive": 0.02 } }
Meta: model, threshold (float, default 0.5).

---

### detect_ai(image, params)

Params: none required.

Returns: MLResult.output = dict: { "ai_probability": 0.87, "is_ai_generated": true }

---

### detect_objects(image, params)

Params:
- confidence_threshold (float, default 0.25)

Returns: MLResult.output = dict: { "objects": [ { "label": "person", "confidence": 0.92, "bbox": [x1, y1, x2, y2] } ] }

---

### embed(image, params)  # CLIP

Params: none required.

Returns: MLResult.output = dict: { "vector": [0.0123, -0.0456, ...], "dim": 512 }
Vector is L2-normalized, length 512.

---

Skeleton — populated as each model is delivered. ML owner fills this in.
