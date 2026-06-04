from __future__ import annotations

import json
import logging
import sqlite3
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path
from typing import Any

from app.services.database_import_service import find_imported_database
from app.services.errors import AppError, InvalidRequestError, SqlExecuteError, SqlValidateError
from app.services.llm_client import SqlGenerator, extract_sql

FORBIDDEN_SQL_TOKENS = {
    "alter",
    "attach",
    "create",
    "delete",
    "detach",
    "drop",
    "insert",
    "pragma",
    "replace",
    "update",
    "vacuum",
}
logger = logging.getLogger(__name__)


def run_query(
    question: str,
    database_id: str,
    import_dir: Path,
    sql_generator: SqlGenerator,
) -> dict[str, object]:
    if not question.strip():
        logger.error("query rejected: empty question database_id=%s", database_id, stack_info=True)
        raise InvalidRequestError("question is required")
    if not database_id.strip():
        logger.error("query rejected: empty database_id", stack_info=True)
        raise InvalidRequestError("database_id is required")

    logger.info("query started database_id=%s question_length=%s", database_id, len(question))
    database_path = find_imported_database(database_id, import_dir)
    dataset_context = _describe_dataset(database_path)
    logger.debug("dataset context built database_id=%s context_length=%s", database_id, len(dataset_context))
    sql = sql_generator.generate_sql(question.strip(), dataset_context)
    logger.info("sql generated database_id=%s sql_length=%s", database_id, len(sql))
    _validate_readonly_sql(sql)
    columns, rows = _execute_readonly_sql(database_path, sql)
    logger.info("query succeeded database_id=%s column_count=%s row_count=%s", database_id, len(columns), len(rows))
    return {
        "sql": sql,
        "columns": columns,
        "rows": rows,
    }


def stream_query_events(
    question: str,
    database_id: str,
    import_dir: Path,
    sql_generator: SqlGenerator,
) -> Iterator[dict[str, object]]:
    try:
        if not question.strip():
            logger.error("stream query rejected: empty question database_id=%s", database_id, stack_info=True)
            raise InvalidRequestError("question is required")
        if not database_id.strip():
            logger.error("stream query rejected: empty database_id", stack_info=True)
            raise InvalidRequestError("database_id is required")

        database_path = find_imported_database(database_id, import_dir)
        dataset_context = _describe_dataset(database_path)

        final_sql = ""
        stream_fn = getattr(sql_generator, "stream_sql_chunks", None)
        if callable(stream_fn):
            content_parts = []
            for chunk in stream_fn(question.strip(), dataset_context):
                content_parts.append(chunk)
                yield _event("model_delta", content=chunk)
            final_sql = extract_sql("".join(content_parts))
        else:
            final_sql = sql_generator.generate_sql(question.strip(), dataset_context)
            yield _event("model_delta", content=final_sql)

        logger.info("stream sql generated database_id=%s sql_length=%s", database_id, len(final_sql))
        yield _event("sql", sql=final_sql)

        _validate_readonly_sql(final_sql)
        columns, rows = _execute_readonly_sql(database_path, final_sql)
        logger.info("stream query succeeded database_id=%s row_count=%s", database_id, len(rows))
        yield _event("result", sql=final_sql, columns=columns, rows=rows)
        yield _event("done")
    except AppError as exc:
        logger.exception("stream query failed with app error database_id=%s code=%s", database_id, exc.code)
        yield _event("error", code=exc.code, message=exc.message, detail=exc.detail)
    except Exception:
        logger.exception("stream query failed unexpectedly database_id=%s", database_id)
        yield _event("error", code="INTERNAL_ERROR", message="internal server error", detail={})


def _event(event_type: str, **payload: object) -> dict[str, object]:
    return {"type": event_type, **payload}


def format_sse_event(event: dict[str, object]) -> str:
    event_type = str(event["type"])
    data = {key: value for key, value in event.items() if key != "type"}
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _describe_dataset(database_path: Path) -> str:
    try:
        with closing(sqlite3.connect(database_path)) as connection:
            connection.row_factory = sqlite3.Row
            table_names = [
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """
                )
            ]
            descriptions = []
            for table_name in table_names:
                descriptions.append(_describe_table(connection, table_name))
            return "\n".join(descriptions)
    except sqlite3.DatabaseError:
        logger.exception("dataset description failed path=%s", database_path)
        raise


def _describe_table(connection: sqlite3.Connection, table_name: str) -> str:
    quoted_table_name = _quote_identifier(table_name)
    columns = [f"{row[1]} {row[2] or 'TEXT'}" for row in connection.execute(f"PRAGMA table_info({quoted_table_name})")]
    row_count = connection.execute(f"SELECT COUNT(*) FROM {quoted_table_name}").fetchone()[0]
    sample_rows = [dict(row) for row in connection.execute(f"SELECT * FROM {quoted_table_name} LIMIT 3").fetchall()]
    return f"Table: {table_name}\nColumns: {', '.join(columns)}\nRow count: {row_count}\nSample rows: {sample_rows}"


def _validate_readonly_sql(sql: str) -> None:
    normalized = sql.strip().rstrip(";").strip()
    lowered = normalized.lower()
    if not lowered.startswith(("select ", "with ")):
        logger.error("sql validation failed: non-readonly statement sql_length=%s", len(sql), stack_info=True)
        raise SqlValidateError("only select queries are allowed")
    if ";" in normalized:
        logger.error("sql validation failed: multiple statements sql_length=%s", len(sql), stack_info=True)
        raise SqlValidateError("multiple sql statements are not allowed")

    tokens = {token.strip(" \n\t\r(),;") for token in lowered.replace("\n", " ").split()}
    matched_tokens = sorted(tokens & FORBIDDEN_SQL_TOKENS)
    if matched_tokens:
        logger.error(
            "sql validation failed: forbidden tokens tokens=%s sql_length=%s",
            matched_tokens,
            len(sql),
            stack_info=True,
        )
        raise SqlValidateError("sql contains forbidden operation", {"tokens": matched_tokens})


def _execute_readonly_sql(database_path: Path, sql: str) -> tuple[list[str], list[dict[str, Any]]]:
    uri = f"file:{database_path.resolve().as_posix()}?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.execute(sql)
            fetched_rows = cursor.fetchmany(100)
    except sqlite3.DatabaseError as exc:
        logger.exception("readonly sql execution failed path=%s sql_length=%s", database_path, len(sql))
        raise SqlExecuteError("sql execution failed") from exc

    columns = [description[0] for description in cursor.description or []]
    rows = [{column: row[column] for column in columns} for row in fetched_rows]
    return columns, rows


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
