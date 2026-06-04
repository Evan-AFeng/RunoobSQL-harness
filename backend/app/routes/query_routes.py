from __future__ import annotations

from pathlib import Path
from typing import Any

from flask import Blueprint, Response, current_app, jsonify, request, stream_with_context

from app.configs.llm import load_llm_config
from app.services.errors import InvalidRequestError
from app.services.llm_client import OpenAiCompatibleClient
from app.services.query_service import format_sse_event, run_query, stream_query_events

query_bp = Blueprint("query", __name__)


@query_bp.post("/api/query")
def query() -> tuple[Any, int]:
    payload = request.get_json(silent=True) or {}
    question = payload.get("question")
    database_id = payload.get("database_id")
    if not isinstance(question, str):
        raise InvalidRequestError("question is required")
    if not isinstance(database_id, str):
        raise InvalidRequestError("database_id is required")

    sql_generator = current_app.config.get("SQL_GENERATOR")
    if sql_generator is None:
        sql_generator = OpenAiCompatibleClient(load_llm_config())

    result = run_query(
        question=question,
        database_id=database_id,
        import_dir=Path(current_app.config["DATABASE_IMPORT_DIR"]),
        sql_generator=sql_generator,
    )
    return jsonify(result), 200


@query_bp.get("/api/query/stream")
def query_stream() -> Response:
    question = request.args.get("question", "")
    database_id = request.args.get("database_id", "")
    sql_generator = current_app.config.get("SQL_GENERATOR")
    if sql_generator is None:
        sql_generator = OpenAiCompatibleClient(load_llm_config())

    import_dir = Path(current_app.config["DATABASE_IMPORT_DIR"])

    def generate() -> Any:
        for event in stream_query_events(
            question=question,
            database_id=database_id,
            import_dir=import_dir,
            sql_generator=sql_generator,
        ):
            yield format_sse_event(event)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
