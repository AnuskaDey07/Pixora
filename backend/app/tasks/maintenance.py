"""Periodic maintenance tasks."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import and_

from app.extensions import db
from app.models.job import Job
from app.services import jobs


STUCK_THRESHOLD = timedelta(minutes=15)


@shared_task(name="app.tasks.maintenance.reconcile_stuck_jobs")
def reconcile_stuck_jobs() -> dict:
    """Flip 'running' jobs older than the threshold to 'timeout'."""
    cutoff = datetime.now(timezone.utc) - STUCK_THRESHOLD

    stuck = (
        Job.query
        .filter(
            and_(
                Job.status == "running",
                Job.started_at.isnot(None),
                Job.started_at < cutoff,
            )
        )
        .all()
    )

    for job in stuck:
        jobs.mark_timeout(job)

    return {"reconciled": len(stuck), "cutoff": cutoff.isoformat()}
