import torch
import gc
import time
from PIL import Image, ImageOps
from diffusers import Flux2KleinPipeline
from app.ml.base import MLResult

_model = None
_REPO = "black-forest-labs/FLUX.2-klein-4B"

def _load_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # From your notebook: Klein 4B uses float16 or bfloat16
        native_bf16 = torch.cuda.get_device_capability(0)[0] >= 8 if device == "cuda" else False
        dtype = torch.bfloat16 if native_bf16 else torch.float16
        
        kwargs = dict(torch_dtype=dtype)
        
        # Note: We skip the 4-bit quantization from the notebook for now. 
        # The backend GPU worker should ideally have enough VRAM (22GB+) to run full precision.
        try:
            _model = Flux2KleinPipeline.from_pretrained(_REPO, device_map="cuda", **kwargs)
        except Exception:
            # Fallback for CPU or low VRAM
            _model = Flux2KleinPipeline.from_pretrained(_REPO, **kwargs)
            if device == "cuda":
                _model.enable_model_cpu_offload()
            else:
                _model.to(device)
                
        gc.collect()
        if device == "cuda":
            torch.cuda.empty_cache()
            
    return _model

def img2img(image: Image.Image, params: dict) -> MLResult:
    t0 = time.perf_counter()
    try:
        model = _load_model()
        
        instruction = params.get("prompt", "")
        if not instruction:
            return MLResult(ok=False, error="Missing required parameter: prompt")
            
        # From your notebook's prepare_input function
        img = ImageOps.exif_transpose(image).convert("RGB")
        w, h = img.size
        target = min(1024, max(768, max(w, h)))
        s = target / max(w, h)
        img = img.resize((max(256, round(w * s / 16) * 16), max(256, round(h * s / 16) * 16)), Image.LANCZOS)
        
        # From your notebook's edit function
        keep_hint = " Keep everything else exactly the same, including faces, identity, pose and lighting."
        full_prompt = instruction.strip() + keep_hint
        
        steps = int(params.get("steps", 4))
        guidance = float(params.get("guidance", 1.0))
        seed = int(params.get("seed", -1))
        if seed < 0:
            import random
            seed = random.randint(0, 2**31 - 1)
            
        out = model(
            image=img, 
            prompt=full_prompt, 
            num_inference_steps=steps, 
            guidance_scale=guidance,
            generator=torch.Generator(device="cpu").manual_seed(seed)
        ).images[0]
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return MLResult(
            ok=True,
            output=out,
            meta={
                "model": _REPO, 
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                "seed": seed
            },
        )
    except Exception as exc:
        return MLResult(ok=False, error=str(exc))
