"""Generation tasks: SD, img2img, inpaint, ControlNet. Queue: gpu."""
from __future__ import annotations

import io

from celery import shared_task
from PIL import Image

from app.extensions import db
from app.ml import _stub as ml
from app.models.image import Image as ImageModel
from app.models.job import Job
from app.services import jobs, storage


def _load(job_id: str):
    job = Job.query.get(job_id)
    if job is None:
        return None, None
    image = ImageModel.query.get(job.image_id) if job.image_id else None
    return job, image


def _run_generate(fn, job_id: str, needs_image: bool) -> str:
    job, image = _load(job_id)
    if job is None:
        return f"job {job_id} not found"

    try:
        jobs.mark_running(job)

        src = None
        if needs_image:
            if image is None:
                jobs.mark_failed(job, error="image not found")
                return "no image"
            raw = storage.download_bytes("uploads", image.original_key)
            src = Image.open(io.BytesIO(raw))
            src.load()

        result = fn(src, job.params or {}) if src else fn(None, job.params or {})
        if not result.ok or result.output is None:
            jobs.mark_failed(job, error=result.error or "ml_error")
            return "failed"

        buf = io.BytesIO()
        result.output.save(buf, format="PNG", optimize=True)

        result_key = storage.make_key(f"generated/{job.user_id}", "out.png")
        storage.upload_bytes("results", result_key, buf.getvalue(), "image/png")

        jobs.mark_done(job, result_key=result_key, meta=result.meta or {})
        return f"ok: {result_key}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise


@shared_task(name="app.tasks.generate.generate_task", bind=True, max_retries=1)
def generate_task(self, job_id: str) -> str:
    return _run_generate(ml.generate, job_id, needs_image=False)


@shared_task(name="app.tasks.generate.img2img_task", bind=True, max_retries=1)
def img2img_task(self, job_id: str) -> str:
    return _run_generate(ml.img2img, job_id, needs_image=True)


@shared_task(name="app.tasks.generate.inpaint_task", bind=True, max_retries=1)
def inpaint_task(self, job_id: str) -> str:
    return _run_generate(ml.inpaint, job_id, needs_image=True)


@shared_task(name="app.tasks.generate.controlnet_task", bind=True, max_retries=1)
def controlnet_task(self, job_id: str) -> str:
    return _run_generate(ml.controlnet_scribble, job_id, needs_image=True)
