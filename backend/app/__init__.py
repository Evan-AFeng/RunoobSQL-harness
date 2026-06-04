from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from flask import Flask, jsonify

from app.routes.database_routes import database_bp
from app.routes.health import health_bp
from app.routes.query_routes import query_bp
from app.services.errors import AppError


def create_app(config: Mapping[str, Any] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        DATABASE_IMPORT_DIR="instance/databases",
        MAX_CONTENT_LENGTH=50 * 1024 * 1024,
    )
    if config:
        app.config.update(config)

    app.register_blueprint(health_bp)
    app.register_blueprint(database_bp)
    app.register_blueprint(query_bp)

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> tuple[Any, int]:
        return jsonify(error.to_response()), error.status_code

    @app.errorhandler(413)
    def handle_payload_too_large(_: Exception) -> tuple[Any, int]:
        return (
            jsonify(
                {
                    "code": "INVALID_REQUEST",
                    "message": "uploaded database is too large",
                    "detail": {},
                }
            ),
            400,
        )

    @app.errorhandler(Exception)
    def handle_unexpected_error(error: Exception) -> tuple[Any, int]:
        if app.config.get("TESTING"):
            raise error

        return (
            jsonify(
                {
                    "code": "INTERNAL_ERROR",
                    "message": "internal server error",
                    "detail": {},
                }
            ),
            500,
        )

    return app
