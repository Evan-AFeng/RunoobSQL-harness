from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from flask import Blueprint, current_app, jsonify, request

from app.services.database_import_service import import_sqlite_database
from app.services.errors import InvalidRequestError

database_bp = Blueprint("databases", __name__)


@database_bp.post("/api/databases/import")
def import_database() -> tuple[Any, int]:
    uploaded_file = request.files.get("file")
    if uploaded_file is None or not uploaded_file.filename:
        raise InvalidRequestError("file is required")

    original_filename = Path(uploaded_file.filename).name
    with NamedTemporaryFile(suffix=Path(original_filename).suffix, delete=False) as temp_file:
        temp_path = Path(temp_file.name)
        uploaded_file.save(temp_file)

    try:
        result = import_sqlite_database(
            source_path=temp_path,
            original_filename=original_filename,
            import_dir=Path(current_app.config["DATABASE_IMPORT_DIR"]),
        )
    finally:
        temp_path.unlink(missing_ok=True)

    return jsonify(result), 201
