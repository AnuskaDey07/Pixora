"""CLIP embedding for an image — used for semantic + similarity search."""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.image import Image


EMBEDDING_DIM = 512


class Embedding(UUIDMixin, TimestampMixin, db.Model):
    __tablename__ = "embeddings"

    image_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    vector: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False, default=EMBEDDING_DIM)
    model_name: Mapped[str] = mapped_column(nullable=False, default="clip-vit-base-patch32")

    image: Mapped["Image"] = relationship(back_populates="embedding")

    def __repr__(self) -> str:
        return f"<Embedding image={self.image_id} dim={self.dim}>"
