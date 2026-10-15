"""Search endpoints — semantic and similarity. Uses pgvector."""
from __future__ import annotations

import io
import uuid

from flask import Blueprint, jsonify, request
from PIL import Image
from sqlalchemy import func, select

from app.api._decorators import require_auth
from app.extensions import db
from app.ml import _stub as ml
from app.models.embedding import Embedding
from app.models.image import Image as ImageModel
from app.models.user import User
from app.services import storage


search_bp = Blueprint("search", __name__, url_prefix="/api/search")


@search_bp.post("/semantic")
@require_auth
def semantic(user: User):
    """Semantic search over the user's images using a text query.

    Text → CLIP text embedding → nearest image vectors.
    Stub returns zero vectors, so results are effectively random order
    until the real CLIP model lands.
    """
    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    limit = min(int(data.get("limit", 20)), 50)

    if not query:
        return jsonify(error="empty_query"), 400

    # Stub: embed the query as if it were an image (returns zero vector).
    # Real impl: encode text with CLIP's text encoder.
    dummy = Image.new("RGB", (224, 224), (0, 0, 0))
    qres = ml.embed(dummy, {"mode": "text", "text": query})
    if not qres.ok or not qres.output:
        return jsonify(error="embedding_failed"), 500
    qvec = qres.output["vector"]

    # Cosine distance via pgvector. Order by increasing distance.
    stmt = (
        select(
            ImageModel.id,
            ImageModel.filename,
            ImageModel.thumb_key,
            Embedding.vector.cosine_distance(qvec).label("distance"),
        )
        .join(Embedding, Embedding.image_id == ImageModel.id)
        .where(ImageModel.user_id == user.id)
        .order_by("distance")
        .limit(limit)
    )

    rows = db.session.execute(stmt).all()

    return jsonify(
        query=query,
        results=[
            {
                "image_id": str(row.id),
                "filename": row.filename,
                "score": 1.0 - float(row.distance),
                "thumb_url": storage.presigned_url("thumbs", row.thumb_key, 3600)
                if row.thumb_key
                else None,
            }
            for row in rows
        ],
        count=len(rows),
    )


@search_bp.post("/similar")
@require_auth
def similar(user: User):
    """Find images similar to a given image (by its CLIP embedding)."""
    data = request.get_json(silent=True) or {}
    image_id = data.get("image_id")
    limit = min(int(data.get("limit", 20)), 50)

    if not image_id:
        return jsonify(error="missing_image_id"), 400

    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        return jsonify(error="invalid_id"), 400

    ref = ImageModel.query.filter_by(id=iid, user_id=user.id).first()
    if ref is None:
        return jsonify(error="not_found"), 404

    ref_emb = Embedding.query.filter_by(image_id=ref.id).first()
    if ref_emb is None:
        return jsonify(error="no_embedding", hint="run embed job first"), 400

    stmt = (
        select(
            ImageModel.id,
            ImageModel.filename,
            ImageModel.thumb_key,
            Embedding.vector.cosine_distance(ref_emb.vector).label("distance"),
        )
        .join(Embedding, Embedding.image_id == ImageModel.id)
        .where(ImageModel.user_id == user.id)
        .where(ImageModel.id != ref.id)
        .order_by("distance")
        .limit(limit)
    )

    rows = db.session.execute(stmt).all()

    return jsonify(
        reference_id=str(ref.id),
        results=[
            {
                "image_id": str(row.id),
                "filename": row.filename,
                "score": 1.0 - float(row.distance),
                "thumb_url": storage.presigned_url("thumbs", row.thumb_key, 3600)
                if row.thumb_key
                else None,
            }
            for row in rows
        ],
        count=len(rows),
    )
