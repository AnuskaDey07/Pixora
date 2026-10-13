"""Celery app + queue routing."""
from __future__ import annotations

import os

from celery import Celery


def _make() -> Celery:
    broker = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/1")
    backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/2")

    app = Celery("pixora", broker=broker, backend=backend)

    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_acks_late=True,
        task_reject_on_worker_lost=True,
        worker_prefetch_multiplier=1,
        task_track_started=True,
        result_expires=3600,
        task_default_queue="light",
        task_routes={
            "app.tasks.basic.*":    {"queue": "light"},
            "app.tasks.search.*":   {"queue": "ml"},
            "app.tasks.detect.*":   {"queue": "ml"},
            "app.tasks.generate.*": {"queue": "gpu"},
        },
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = _make()
