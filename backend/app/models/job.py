"""Job model — tracks every asynchronous operation."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.image import Image
    from app.models.user import User


# Terminal states — a job in one of these is finished forever
TERMINAL_STATES = {"done", "failed", "timeout"}
ALL_STATES = {"pending", "running", *TERMINAL_STATES}


class Job(UUIDMixin, TimestampMixin, db.Model):
    __tablename__ = "jobs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )

    params: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    result_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    celery_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    user: Mapped["User"] = relationship(back_populates="jobs")
    image: Mapped["Image | None"] = relationship(back_populates="jobs")

    __table_args__ = (
        Index("ix_jobs_user_status", "user_id", "status"),
        Index("ix_jobs_type_status", "type", "status"),
    )

    def __repr__(self) -> str:
        return f"<Job {self.id} type={self.type} status={self.status}>"
