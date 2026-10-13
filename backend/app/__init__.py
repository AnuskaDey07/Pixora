"""Pixora API — application factory."""
from __future__ import annotations

from flask import Flask, jsonify


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="pixora-api")

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
