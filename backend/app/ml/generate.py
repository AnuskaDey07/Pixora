import torch
import gc
import time
from PIL import Image
from diffusers import (StableDiffusionXLPipeline, AutoencoderKL, DPMSolverMultistepScheduler)
from app.ml.base import MLResult

_model = None
_BASE_MODEL = "SG161222/RealVisXL_V5.0"
_VAE_MODEL = "madebyollin/sdxl-vae-fp16-fix"

def _load(cls, repo, **kw):
    """Load fp16 weights if the repo has them, otherwise the default weights. Uses little CPU memory."""
    try:
        return cls.from_pretrained(repo, variant="fp16", use_safetensors=True, low_cpu_mem_usage=True, **kw)
    except Exception:
        return cls.from_pretrained(repo, use_safetensors=True, low_cpu_mem_usage=True, **kw)

def _load_model():
    global _model
    if _model is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        # fp16-safe VAE
        vae = AutoencoderKL.from_pretrained(_VAE_MODEL, torch_dtype=dtype).to(device)
        gc.collect()

        pipe_args = dict(vae=vae, torch_dtype=dtype, add_watermarker=False)
        pipe, on_gpu = None, False
        
        if device == "cuda":
            try:
                pipe = _load(StableDiffusionXLPipeline, _BASE_MODEL, device_map="cuda", **pipe_args)
                on_gpu = True
            except Exception:
                pass # Fallback to normal loading below
                
        if pipe is None:
            pipe = _load(StableDiffusionXLPipeline, _BASE_MODEL, **pipe_args)
            
        if not on_gpu:
            pipe.to(device)

        # Sampler recommended by the model's author
        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config, algorithm_type="sde-dpmsolver++", use_karras_sigmas=True)
            
        if device == "cuda":
            pipe.vae.enable_tiling()

        _model = pipe
        
    return _model

def generate(image: Image.Image, params: dict) -> MLResult:
    # The `image` argument is ignored for text-to-image
    t0 = time.perf_counter()
    try:
        model = _load_model()
        
        prompt = params.get("prompt", "")
        if not prompt:
            return MLResult(ok=False, error="Missing required parameter: prompt")
            
        steps = int(params.get("steps", 30))
        guidance = float(params.get("guidance", 7.5))
        width = int(params.get("width", 1024)) # SDXL uses 1024 by default
        height = int(params.get("height", 1024))
        
        result = model(
            prompt=prompt, 
            num_inference_steps=steps, 
            guidance_scale=guidance,
            width=width,
            height=height
        )
        
        output_image = result.images[0]

        return MLResult(
            ok=True,
            output=output_image,
            meta={
                "model": _BASE_MODEL, 
                "elapsed_ms": int((time.perf_counter() - t0) * 1000),
            },
        )
    except Exception as exc:
        return MLResult(ok=False, error=str(exc))
