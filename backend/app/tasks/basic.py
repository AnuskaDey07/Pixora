"""Basic image tasks: resize, format conversion. Queue: light."""
from __future__ import annotations

import io

from app.tasks.celery_app import celery_app
from PIL import Image

from app.extensions import db
from app.models.image import Image as ImageModel
from app.models.job import Job
from app.services import imaging, jobs, storage


def _load_job(job_id: str) -> tuple[Job | None, ImageModel | None]:
    """Fetch job + image from DB. Returns (None, None) if not found."""
    job = Job.query.get(job_id)
    if job is None:
        return None, None
    if job.image_id is None:
        return job, None
    image = ImageModel.query.get(job.image_id)
    return job, image


@celery_app.task(name="app.tasks.basic.resize_task", bind=True, max_retries=2)
def resize_task(self, job_id: str) -> str:
    """Resize an image to the dimensions in job.params.

    Params:
        width  (int, required)
        height (int, required)
        format (str, optional) — 'PNG' | 'JPEG' | 'WEBP', default: same as source
    """
    job, image = _load_job(job_id)
    if job is None:
        return f"job {job_id} not found"
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "image not found"

    try:
        jobs.mark_running(job)

        width = int(job.params["width"])
        height = int(job.params["height"])
        target_format = job.params.get("format")

        # Download original
        raw = storage.download_bytes("uploads", image.original_key)
        src = Image.open(io.BytesIO(raw))
        src.load()

        # Resize
        out = imaging.resize_image(src, width, height)

        # Encode
        if target_format == "JPEG":
            result_bytes = imaging.convert_format(out, "JPEG")
            ext, mime = "jpg", "image/jpeg"
        elif target_format == "WEBP":
            result_bytes = imaging.convert_format(out, "WEBP")
            ext, mime = "webp", "image/webp"
        else:
            result_bytes = imaging.encode_png(out)
            ext, mime = "png", "image/png"

        # Store result
        result_key = storage.make_key(f"resized/{job.user_id}", f"out.{ext}")
        storage.upload_bytes("results", result_key, result_bytes, mime)

        jobs.mark_done(
            job,
            result_key=result_key,
            meta={
                "width": width,
                "height": height,
                "format": ext.upper(),
                "bytes": len(result_bytes),
            },
        )
        return f"ok: {result_key}"

    except KeyError as exc:
        jobs.mark_failed(job, error=f"missing param: {exc}")
        return f"missing param: {exc}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        # Retry once on unexpected failures
        raise self.retry(exc=exc, countdown=5)


@celery_app.task(name="app.tasks.basic.convert_task", bind=True, max_retries=2)
def convert_task(self, job_id: str) -> str:
    """Convert an image to a different format.

    Params:
        format (str, required) — 'PNG' | 'JPEG' | 'WEBP'
    """
    job, image = _load_job(job_id)
    if job is None:
        return f"job {job_id} not found"
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "image not found"

    try:
        jobs.mark_running(job)

        fmt = job.params["format"].upper()
        if fmt not in ("PNG", "JPEG", "WEBP"):
            raise ValueError(f"unsupported format: {fmt}")

        raw = storage.download_bytes("uploads", image.original_key)
        src = Image.open(io.BytesIO(raw))
        src.load()

        result_bytes = imaging.convert_format(src, fmt)
        ext = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}[fmt]
        mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[fmt]

        result_key = storage.make_key(f"converted/{job.user_id}", f"out.{ext}")
        storage.upload_bytes("results", result_key, result_bytes, mime)

        jobs.mark_done(
            job,
            result_key=result_key,
            meta={"format": fmt, "bytes": len(result_bytes)},
        )
        return f"ok: {result_key}"

    except KeyError as exc:
        jobs.mark_failed(job, error=f"missing param: {exc}")
        return f"missing param: {exc}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise self.retry(exc=exc, countdown=5)
