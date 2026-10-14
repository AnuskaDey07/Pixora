"""Job creation and status endpoints."""
from __future__ import annotations

import uuid

from flask import Blueprint, jsonify, request

from app.api._decorators import require_auth
from app.models.image import Image
from app.models.job import Job
from app.models.user import User
from app.services import jobs as jobs_service, storage


jobs_bp = Blueprint("jobs", __name__, url_prefix="/api/jobs")


def _serialize(job: Job) -> dict:
    result_url = None
    if job.result_key:
        # Results can be in different buckets. Try 'results' first.
        try:
            result_url = storage.presigned_url("results", job.result_key, 3600)
        except Exception:
            result_url = None

    return {
        "id": str(job.id),
        "type": job.type,
        "status": job.status,
        "image_id": str(job.image_id) if job.image_id else None,
        "params": job.params,
        "meta": job.meta,
        "result_url": result_url,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
    }


@jobs_bp.post("")
@require_auth
def create_job(user: User):
    data = request.get_json(silent=True) or {}

    job_type = data.get("type")
    if job_type not in jobs_service.JOB_TYPE_QUEUE:
        return jsonify(
            error="unknown_type",
            allowed=list(jobs_service.JOB_TYPE_QUEUE.keys()),
        ), 400

    image_id = data.get("image_id")
    if image_id is not None:
        try:
            iid = uuid.UUID(image_id)
        except ValueError:
            return jsonify(error="invalid_image_id"), 400
        image = Image.query.filter_by(id=iid, user_id=user.id).first()
        if image is None:
            return jsonify(error="image_not_found"), 404
        image_id = iid
    else:
        image_id = None

    params = data.get("params") or {}
    if not isinstance(params, dict):
        return jsonify(error="params_must_be_object"), 400

    job = jobs_service.create_job(
        user_id=user.id,
        job_type=job_type,
        image_id=image_id,
        params=params,
    )
    jobs_service.enqueue_job(job)

    return jsonify(_serialize(job)), 202


@jobs_bp.get("/<job_id>")
@require_auth
def get_job(user: User, job_id: str):
    try:
        jid = uuid.UUID(job_id)
    except ValueError:
        return jsonify(error="invalid_id"), 400

    job = Job.query.filter_by(id=jid, user_id=user.id).first()
    if job is None:
        return jsonify(error="not_found"), 404

    return jsonify(_serialize(job))


@jobs_bp.get("")
@require_auth
def list_jobs(user: User):
    limit = min(int(request.args.get("limit", 40)), 100)
    offset = max(int(request.args.get("offset", 0)), 0)
    status_filter = request.args.get("status")
    type_filter = request.args.get("type")

    q = Job.query.filter_by(user_id=user.id)
    if status_filter:
        q = q.filter_by(status=status_filter)
    if type_filter:
        q = q.filter_by(type=type_filter)

    q = q.order_by(Job.created_at.desc()).limit(limit).offset(offset)
    items = q.all()

    return jsonify(
        jobs=[_serialize(j) for j in items],
        count=len(items),
    )
