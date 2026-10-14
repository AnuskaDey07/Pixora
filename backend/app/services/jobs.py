"""Job lifecycle: create, enqueue, update, query.

Flask endpoints use these helpers to avoid duplicating job bookkeeping.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.extensions import db
from app.models.job import Job


# Job types → Celery queue
JOB_TYPE_QUEUE = {
    "resize": "light",
    "convert": "light",
    "thumbnail": "light",
    "remove_bg": "ml",
    "detect_objects": "ml",
    "detect_nsfw": "ml",
    "detect_ai": "ml",
    "embed": "ml",
    "generate": "gpu",
    "img2img": "gpu",
    "inpaint": "gpu",
    "controlnet": "gpu",
}


# Job types → Celery task name
JOB_TYPE_TASK = {
    "resize": "app.tasks.basic.resize_task",
    "convert": "app.tasks.basic.convert_task",
    # ml/gpu tasks added in later batches
}


def create_job(
    *,
    user_id: str,
    job_type: str,
    image_id: str | None,
    params: dict[str, Any],
) -> Job:
    """Insert a new job row in pending state."""
    if job_type not in JOB_TYPE_QUEUE:
        raise ValueError(f"unknown job type: {job_type}")

    job = Job(
        user_id=user_id,
        image_id=image_id,
        type=job_type,
        status="pending",
        params=params,
        meta={},
    )
    db.session.add(job)
    db.session.commit()
    return job


def enqueue_job(job: Job) -> str | None:
    """Send the job to Celery. Returns the celery task id (or None)."""
    task_name = JOB_TYPE_TASK.get(job.type)
    if task_name is None:
        # Not yet implemented — leave pending. Batch 4 wires real ML.
        return None

    from app.tasks.celery_app import celery_app

    result = celery_app.send_task(
        task_name,
        args=[str(job.id)],
        queue=JOB_TYPE_QUEUE[job.type],
    )
    job.celery_task_id = result.id
    db.session.commit()
    return result.id


def mark_running(job: Job) -> None:
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    db.session.commit()


def mark_done(job: Job, *, result_key: str, meta: dict | None = None) -> None:
    job.status = "done"
    job.result_key = result_key
    job.meta = meta or {}
    job.finished_at = datetime.now(timezone.utc)
    db.session.commit()


def mark_failed(job: Job, *, error: str) -> None:
    job.status = "failed"
    job.error = error[:2000]
    job.finished_at = datetime.now(timezone.utc)
    db.session.commit()


def mark_timeout(job: Job) -> None:
    job.status = "timeout"
    job.error = "job exceeded time limit"
    job.finished_at = datetime.now(timezone.utc)
    db.session.commit()
