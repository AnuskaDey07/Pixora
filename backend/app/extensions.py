"""Flask extensions — instantiated once, bound to app in create_app()."""
from __future__ import annotations

import os

from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()

# Limiter uses Redis so rate limits are shared across Gunicorn workers.
# Falls back to in-memory in tests where REDIS_URL isn't set.
_redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=_redis_url,
    default_limits=[],  # no global default; endpoints opt-in
    strategy="fixed-window",
)
