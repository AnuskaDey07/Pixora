"""Auth decorators and helpers."""
from __future__ import annotations

from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.models.user import User


def current_user() -> User | None:
    """Load the User row for the current JWT. Returns None if invalid."""
    try:
        verify_jwt_in_request()
    except Exception:
        return None
    user_id = get_jwt_identity()
    if not user_id:
        return None
    return User.query.get(user_id)


def require_auth(fn):
    """Require a valid access token. Injects `user` into kwargs."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify(error="unauthorized"), 401
        if not user.is_active:
            return jsonify(error="account_disabled"), 403
        kwargs["user"] = user
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    """Require role=admin. Use only inside /api/admin/* blueprints."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            return jsonify(error="unauthorized"), 401
        if not user.is_active:
            return jsonify(error="account_disabled"), 403
        if user.role != "admin":
            return jsonify(error="forbidden"), 403
        kwargs["user"] = user
        return fn(*args, **kwargs)

    return wrapper
