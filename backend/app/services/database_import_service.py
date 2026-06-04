from __future__ import annotations

import logging
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

from app.services.errors import DatabaseImportError, InvalidRequestError

SQLITE_EXTENSIONS = {".db", ".sqlite", ".sqlite3"}
logger = logging.getLogger(__name__)


def import_sqlite_database(source_path: Path, original_filename: str, import_dir: Path) -> dict[str, object]:
    if not source_path.exists() or source_path.stat().st_size == 0:
        logger.error("sqlite import rejected: empty upload filename=%s", original_filename, stack_info=True)
        raise InvalidRequestError("uploaded database file is empty")

    suffix = Path(original_filename).suffix.lower()
    if suffix not in SQLITE_EXTENSIONS:
        logger.error(
            "sqlite import rejected: unsupported suffix filename=%s suffix=%s",
            original_filename,
            suffix,
            stack_info=True,
        )
        raise InvalidRequestError(
            "only sqlite database files are supported",
            {"allowed_extensions": sorted(SQLITE_EXTENSIONS)},
        )

    logger.info("sqlite import started filename=%s size=%s", original_filename, source_path.stat().st_size)
    _validate_sqlite(source_path)

    import_dir.mkdir(parents=True, exist_ok=True)
    database_id = _build_database_id(original_filename)
    target_path = import_dir / f"{database_id}{suffix}"
    try:
        shutil.copy2(source_path, target_path)
    except OSError:
        logger.exception("sqlite import failed while copying database_id=%s", database_id)
        raise

    tables = _inspect_tables(target_path)
    logger.info("sqlite import succeeded database_id=%s table_count=%s", database_id, len(tables))
    return {
        "database_id": database_id,
        "filename": original_filename,
        "path": str(target_path),
        "tables": tables,
    }


def find_imported_database(database_id: str, import_dir: Path) -> Path:
    for suffix in sorted(SQLITE_EXTENSIONS):
        path = import_dir / f"{database_id}{suffix}"
        if path.is_file():
            logger.debug("imported sqlite database resolved database_id=%s suffix=%s", database_id, suffix)
            return path

    logger.error("imported sqlite database not found database_id=%s", database_id, stack_info=True)
    raise InvalidRequestError("database_id was not found")


def _validate_sqlite(path: Path) -> None:
    try:
        with closing(sqlite3.connect(path)) as connection:
            result = connection.execute("PRAGMA integrity_check").fetchone()
    except sqlite3.DatabaseError as exc:
        logger.exception("sqlite validation failed path=%s", path)
        raise DatabaseImportError("uploaded file is not a valid sqlite database") from exc

    if result is None or result[0] != "ok":
        logger.error("sqlite integrity check failed path=%s result=%s", path, result, stack_info=True)
        raise DatabaseImportError("sqlite database integrity check failed")


def _inspect_tables(path: Path) -> list[dict[str, object]]:
    try:
        with closing(sqlite3.connect(path)) as connection:
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
            return [_inspect_table(connection, table_name) for table_name in table_names]
    except sqlite3.DatabaseError:
        logger.exception("sqlite table inspection failed path=%s", path)
        raise


def _inspect_table(connection: sqlite3.Connection, table_name: str) -> dict[str, object]:
    columns = [
        {
            "name": row[1],
            "type": row[2],
            "nullable": row[3] == 0,
            "primary_key": row[5] > 0,
        }
        for row in connection.execute(f"PRAGMA table_info({_quote_identifier(table_name)})")
    ]
    row_count = connection.execute(f"SELECT COUNT(*) FROM {_quote_identifier(table_name)}").fetchone()[0]
    return {
        "name": table_name,
        "columns": columns,
        "row_count": row_count,
    }


def _quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _build_database_id(original_filename: str) -> str:
    stem = Path(original_filename).stem.lower()
    safe_stem = "".join(character if character.isalnum() else "-" for character in stem).strip("-")
    prefix = safe_stem or "database"
    return f"{prefix}-{uuid4().hex[:8]}"
