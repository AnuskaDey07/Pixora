"""Image upload and listing endpoints."""
from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from app.api._decorators import require_auth
from app.config import get_settings
from app.extensions import db, limiter
from app.models.image import Image
from app.models.user import User
from app.services import imaging, storage


images_bp = Blueprint("images", __name__, url_prefix="/api/images")


@images_bp.post("/upload")
@require_auth
@limiter.limit("60 per hour")
def upload(user: User):
    settings = get_settings()

    if "file" not in request.files:
        return jsonify(error="no_file"), 400

    file = request.files["file"]
    if not file or file.filename == "":
        return jsonify(error="empty_filename"), 400

    data = file.read()
    if len(data) == 0:
        return jsonify(error="empty_file"), 400
    if len(data) > settings.max_content_length_mb * 1024 * 1024:
        return jsonify(error="file_too_large"), 413

    try:
        img, mime = imaging.validate_image(data)
    except imaging.InvalidImageError as exc:
        return jsonify(error="invalid_image", detail=str(exc)), 415

    safe_name = secure_filename(file.filename) or "image"
    original_key = storage.make_key(f"originals/{user.id}", safe_name)
    thumb_key = storage.make_key(f"thumbs/{user.id}", f"{safe_name}.png")

    thumb_bytes = imaging.make_thumbnail(img)

    storage.upload_bytes("uploads", original_key, data, mime)
    storage.upload_bytes("thumbs", thumb_key, thumb_bytes, "image/png")

    record = Image(
        user_id=user.id,
        original_key=original_key,
        thumb_key=thumb_key,
        filename=safe_name,
        mime=mime,
        size_bytes=len(data),
        width=img.width,
        height=img.height,
    )
    db.session.add(record)
    db.session.commit()

    return jsonify(
        id=str(record.id),
        filename=record.filename,
        width=record.width,
        height=record.height,
        mime=record.mime,
        size_bytes=record.size_bytes,
        thumb_url=storage.presigned_url("thumbs", thumb_key, 3600),
        original_url=storage.presigned_url("uploads", original_key, 3600),
        created_at=record.created_at.isoformat() if record.created_at else None,
    ), 201


@images_bp.get("")
@require_auth
def list_images(user: User):
    limit = min(int(request.args.get("limit", 40)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)

    q = (
        Image.query.filter_by(user_id=user.id)
        .order_by(Image.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = q.all()

    return jsonify(
        images=[
            {
                "id": str(i.id),
                "filename": i.filename,
                "width": i.width,
                "height": i.height,
                "mime": i.mime,
                "size_bytes": i.size_bytes,
                "thumb_url": storage.presigned_url("thumbs", i.thumb_key, 3600) if i.thumb_key else None,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ],
        count=len(items),
    )


@images_bp.get("/<image_id>")
@require_auth
def get_image(user: User, image_id: str):
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        return jsonify(error="invalid_id"), 400

    record = Image.query.filter_by(id=iid, user_id=user.id).first()
    if record is None:
        return jsonify(error="not_found"), 404

    return jsonify(
        id=str(record.id),
        filename=record.filename,
        width=record.width,
        height=record.height,
        mime=record.mime,
        size_bytes=record.size_bytes,
        nsfw_flagged=record.nsfw_flagged,
        nsfw_score=record.nsfw_score,
        thumb_url=storage.presigned_url("thumbs", record.thumb_key, 3600) if record.thumb_key else None,
        original_url=storage.presigned_url("uploads", record.original_key, 3600),
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@images_bp.delete("/<image_id>")
@require_auth
def delete_image(user: User, image_id: str):
    try:
        iid = uuid.UUID(image_id)
    except ValueError:
        return jsonify(error="invalid_id"), 400

    record = Image.query.filter_by(id=iid, user_id=user.id).first()
    if record is None:
        return jsonify(error="not_found"), 404

    storage.delete_object("uploads", record.original_key)
    if record.thumb_key:
        storage.delete_object("thumbs", record.thumb_key)

    db.session.delete(record)
    db.session.commit()

    return jsonify(deleted=True, id=str(iid))
