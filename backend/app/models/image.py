"""Image model."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.embedding import Embedding
    from app.models.job import Job
    from app.models.user import User


class Image(UUIDMixin, TimestampMixin, db.Model):
    __tablename__ = "images"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    original_key: Mapped[str] = mapped_column(String(512), nullable=False)
    thumb_key: Mapped[str | None] = mapped_column(String(512), nullable=True)

    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)

    # NSFW moderation flag
    nsfw_flagged: Mapped[bool] = mapped_column(default=False, nullable=False)
    nsfw_score: Mapped[float | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="images")
    jobs: Mapped[list["Job"]] = relationship(
        back_populates="image", cascade="all, delete-orphan"
    )
    embedding: Mapped["Embedding | None"] = relationship(
        back_populates="image", cascade="all, delete-orphan", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Image {self.id} {self.width}x{self.height} {self.mime}>"
