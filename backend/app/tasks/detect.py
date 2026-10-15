"""Detection tasks: NSFW, AI-generated, objects, background removal. Queue: ml."""
from __future__ import annotations

import io

from celery import shared_task
from PIL import Image

from app.extensions import db
from app.ml import _stub as ml
from app.models.image import Image as ImageModel
from app.models.job import Job
from app.services import jobs, storage


NSFW_FLAG_THRESHOLD = 0.5


def _load(job_id: str):
    job = Job.query.get(job_id)
    if job is None:
        return None, None
    image = ImageModel.query.get(job.image_id) if job.image_id else None
    return job, image


def _run_dict_detect(fn, job_id: str) -> str:
    job, image = _load(job_id)
    if job is None:
        return f"job {job_id} not found"
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "no image"

    try:
        jobs.mark_running(job)
        raw = storage.download_bytes("uploads", image.original_key)
        img = Image.open(io.BytesIO(raw))
        img.load()

        result = fn(img, job.params or {})
        if not result.ok:
            jobs.mark_failed(job, error=result.error or "ml_error")
            return f"failed: {result.error}"

        jobs.mark_done(job, result_key=job.result_key or "", meta=result.output or {})
        return "ok"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise


@shared_task(name="app.tasks.detect.detect_nsfw_task", bind=True, max_retries=1)
def detect_nsfw_task(self, job_id: str) -> str:
    job, image = _load(job_id)
    if job is None:
        return f"job {job_id} not found"
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "no image"

    try:
        jobs.mark_running(job)
        raw = storage.download_bytes("uploads", image.original_key)
        img = Image.open(io.BytesIO(raw))
        img.load()

        result = ml.detect_nsfw(img, job.params or {})
        if not result.ok or not result.output:
            jobs.mark_failed(job, error=result.error or "ml_error")
            return "failed"

        score = float(result.output.get("nsfw_score", 0.0))

        # Write back to the image row
        image.nsfw_score = score
        image.nsfw_flagged = score >= NSFW_FLAG_THRESHOLD
        db.session.commit()

        jobs.mark_done(job, result_key="", meta=result.output)
        return f"ok: score={score:.3f} flagged={image.nsfw_flagged}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise


@shared_task(name="app.tasks.detect.detect_ai_task", bind=True, max_retries=1)
def detect_ai_task(self, job_id: str) -> str:
    return _run_dict_detect(ml.detect_ai, job_id)


@shared_task(name="app.tasks.detect.detect_objects_task", bind=True, max_retries=1)
def detect_objects_task(self, job_id: str) -> str:
    return _run_dict_detect(ml.detect_objects, job_id)


@shared_task(name="app.tasks.detect.remove_bg_task", bind=True, max_retries=1)
def remove_bg_task(self, job_id: str) -> str:
    job, image = _load(job_id)
    if job is None:
        return f"job {job_id} not found"
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "no image"

    try:
        jobs.mark_running(job)
        raw = storage.download_bytes("uploads", image.original_key)
        img = Image.open(io.BytesIO(raw))
        img.load()

        result = ml.remove_background(img, job.params or {})
        if not result.ok or result.output is None:
            jobs.mark_failed(job, error=result.error or "ml_error")
            return "failed"

        buf = io.BytesIO()
        result.output.save(buf, format="PNG", optimize=True)

        result_key = storage.make_key(f"nobg/{job.user_id}", "out.png")
        storage.upload_bytes("results", result_key, buf.getvalue(), "image/png")

        jobs.mark_done(job, result_key=result_key, meta=result.meta or {})
        return f"ok: {result_key}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise
