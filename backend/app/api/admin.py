"""Admin-only endpoints."""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from app.api._decorators import require_admin
from app.extensions import db
from app.models.image import Image
from app.models.job import Job
from app.models.user import User


admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.get("/users")
@require_admin
def list_users(user: User):
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify(
        users=[
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "disabled_at": u.disabled_at.isoformat() if u.disabled_at else None,
            }
            for u in users
        ],
        count=len(users),
    )


@admin_bp.patch("/users/<user_id>")
@require_admin
def update_user(user: User, user_id: str):
    target = User.query.get(user_id)
    if target is None:
        return jsonify(error="user_not_found"), 404
    if str(target.id) == str(user.id):
        return jsonify(error="cannot_modify_self"), 400

    data = request.get_json(silent=True) or {}

    if "is_active" in data:
        target.is_active = bool(data["is_active"])
        target.disabled_at = None if target.is_active else datetime.now(timezone.utc)

    if "role" in data and data["role"] in ("user", "admin"):
        target.role = data["role"]

    db.session.commit()
    return jsonify(
        id=str(target.id),
        email=target.email,
        role=target.role,
        is_active=target.is_active,
    )


@admin_bp.get("/jobs")
@require_admin
def list_all_jobs(user: User):
    limit = min(int(request.args.get("limit", 50)), 200)
    jobs = Job.query.order_by(Job.created_at.desc()).limit(limit).all()
    return jsonify(
        jobs=[
            {
                "id": str(j.id),
                "user_id": str(j.user_id),
                "type": j.type,
                "status": j.status,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "error": j.error,
            }
            for j in jobs
        ],
        count=len(jobs),
    )


@admin_bp.get("/nsfw-queue")
@require_admin
def nsfw_queue(user: User):
    flagged = (
        Image.query.filter(Image.nsfw_flagged.is_(True))
        .order_by(Image.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify(
        images=[
            {
                "id": str(i.id),
                "user_id": str(i.user_id),
                "nsfw_score": i.nsfw_score,
                "thumb_key": i.thumb_key,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in flagged
        ],
        count=len(flagged),
    )
