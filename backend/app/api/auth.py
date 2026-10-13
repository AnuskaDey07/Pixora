"""Authentication endpoints."""
from __future__ import annotations

import re

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from app.api._decorators import require_auth
from app.extensions import db, limiter
from app.models.user import User
from app.services.security import (
    decode_token,
    hash_password,
    make_access_token,
    make_refresh_token,
    verify_password,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email))


@auth_bp.post("/register")
@limiter.limit("10 per hour")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not _validate_email(email):
        return jsonify(error="invalid_email"), 400
    if len(password) < 8:
        return jsonify(error="password_too_short", min_length=8), 400

    user = User(
        email=email,
        password_hash=hash_password(password),
        role="user",
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(error="email_taken"), 409

    return jsonify(
        id=str(user.id),
        email=user.email,
        role=user.role,
    ), 201


@auth_bp.post("/login")
@limiter.limit("30 per hour")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if user is None or not verify_password(password, user.password_hash):
        return jsonify(error="invalid_credentials"), 401
    if not user.is_active:
        return jsonify(error="account_disabled"), 403

    return jsonify(
        access_token=make_access_token(str(user.id), user.role),
        refresh_token=make_refresh_token(str(user.id)),
        user={"id": str(user.id), "email": user.email, "role": user.role},
    ), 200


@auth_bp.post("/refresh")
@limiter.limit("60 per hour")
def refresh():
    data = request.get_json(silent=True) or {}
    token = data.get("refresh_token") or ""
    if not token:
        return jsonify(error="missing_refresh_token"), 400
    try:
        payload = decode_token(token)
    except Exception:
        return jsonify(error="invalid_refresh_token"), 401
    if payload.get("type") != "refresh":
        return jsonify(error="wrong_token_type"), 401

    user = User.query.get(payload["sub"])
    if user is None or not user.is_active:
        return jsonify(error="invalid_user"), 401

    return jsonify(access_token=make_access_token(str(user.id), user.role)), 200


@auth_bp.get("/me")
@require_auth
def me(user: User):
    return jsonify(
        id=str(user.id),
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )
