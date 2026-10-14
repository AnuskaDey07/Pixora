"""Pixora API — application factory."""
from __future__ import annotations

from flask import Flask, jsonify

from app.config import get_settings
from app.extensions import cors, db, jwt, limiter, migrate


def create_app() -> Flask:
    settings = get_settings()
    app = Flask(__name__)

    app.config["SECRET_KEY"] = settings.secret_key
    app.config["JWT_SECRET_KEY"] = settings.jwt_secret_key
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_size": 5,
        "max_overflow": 10,
    }
    app.config["MAX_CONTENT_LENGTH"] = settings.max_content_length_mb * 1024 * 1024

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    from app import models  # noqa: F401

    from app.api.admin import admin_bp
    from app.api.auth import auth_bp
    from app.api.health import health_bp
    from app.api.images import images_bp
    from app.api.jobs import jobs_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(images_bp)
    app.register_blueprint(jobs_bp)

    @app.errorhandler(404)
    def _not_found(_):
        return jsonify(error="not_found"), 404

    @app.errorhandler(405)
    def _method_not_allowed(_):
        return jsonify(error="method_not_allowed"), 405

    @app.errorhandler(413)
    def _too_large(_):
        return jsonify(error="payload_too_large"), 413

    return app


if __name__ == "__main__":  # pragma: no cover
    create_app().run(host="0.0.0.0", port=5000)
