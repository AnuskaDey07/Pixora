"""Search tasks: CLIP embedding on upload. Queue: ml."""
from __future__ import annotations

import io

from celery import shared_task
from PIL import Image

from app.extensions import db
from app.ml import _stub as ml
from app.models.embedding import Embedding
from app.models.image import Image as ImageModel
from app.models.job import Job
from app.services import jobs, storage


@shared_task(name="app.tasks.search.embed_task", bind=True, max_retries=2)
def embed_task(self, job_id: str) -> str:
    job = Job.query.get(job_id)
    if job is None:
        return f"job {job_id} not found"
    if job.image_id is None:
        jobs.mark_failed(job, error="image not found")
        return "no image"

    image = ImageModel.query.get(job.image_id)
    if image is None:
        jobs.mark_failed(job, error="image not found")
        return "no image"

    try:
        jobs.mark_running(job)
        raw = storage.download_bytes("uploads", image.original_key)
        img = Image.open(io.BytesIO(raw))
        img.load()

        result = ml.embed(img, job.params or {})
        if not result.ok or not result.output:
            jobs.mark_failed(job, error=result.error or "ml_error")
            return "failed"

        vector = result.output["vector"]

        # Upsert: one embedding per image
        existing = Embedding.query.filter_by(image_id=image.id).first()
        if existing:
            existing.vector = vector
            existing.model_name = result.meta.get("model", "stub")
        else:
            db.session.add(Embedding(
                image_id=image.id,
                vector=vector,
                dim=len(vector),
                model_name=result.meta.get("model", "stub"),
            ))
        db.session.commit()

        jobs.mark_done(job, result_key="", meta={"dim": len(vector)})
        return f"ok: dim={len(vector)}"
    except Exception as exc:
        jobs.mark_failed(job, error=str(exc))
        raise
