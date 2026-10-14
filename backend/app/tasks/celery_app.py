"""Celery app + queue routing."""
from __future__ import annotations

import os

from celery import Celery, Task
from flask import Flask


def _create_flask_app() -> Flask:
    """Import create_app lazily to avoid circular imports."""
    from app import create_app

    return create_app()


class FlaskTask(Task):
    """Celery Task that runs inside a Flask app context."""

    _flask_app: Flask | None = None

    @property
    def flask_app(self) -> Flask:
        if self._flask_app is None:
            self._flask_app = _create_flask_app()
        return self._flask_app

    def __call__(self, *args, **kwargs):
        with self.flask_app.app_context():
            return self.run(*args, **kwargs)


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
        task_soft_time_limit=600,
        task_time_limit=660,
        broker_connection_retry_on_startup=True,
        imports=("app.tasks.basic",),
    )

    # Use FlaskTask as the default base class for all tasks
    app.Task = FlaskTask

    return app


celery_app = _make()
