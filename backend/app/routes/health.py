from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/api/health")
def health() -> tuple[Any, int]:
    return jsonify({"status": "ok"}), 200
