from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.database_import_service import import_sqlite_database
from app.services.errors import DatabaseImportError, InvalidRequestError


def _create_sqlite_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)")
        connection.execute("INSERT INTO users (name) VALUES (?)", ("Ada",))
        connection.commit()


def test_import_sqlite_database_copies_file_and_returns_schema(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.db"
    import_dir = tmp_path / "imports"
    _create_sqlite_database(source_path)

    result = import_sqlite_database(source_path, "sample.db", import_dir)

    target_path = Path(str(result["path"]))
    assert target_path.exists()
    assert result["filename"] == "sample.db"
    assert result["database_id"]
    assert result["tables"] == [
        {
            "name": "users",
            "columns": [
                {
                    "name": "id",
                    "type": "INTEGER",
                    "nullable": True,
                    "primary_key": True,
                },
                {
                    "name": "name",
                    "type": "TEXT",
                    "nullable": False,
                    "primary_key": False,
                },
            ],
            "row_count": 1,
        }
    ]


def test_import_rejects_non_sqlite_extension(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.txt"
    source_path.write_text("not sqlite", encoding="utf-8")

    with pytest.raises(InvalidRequestError) as exc_info:
        import_sqlite_database(source_path, "sample.txt", tmp_path / "imports")

    assert exc_info.value.code == "INVALID_REQUEST"


def test_import_rejects_invalid_sqlite_content(tmp_path: Path) -> None:
    source_path = tmp_path / "broken.db"
    source_path.write_text("not sqlite", encoding="utf-8")

    with pytest.raises(DatabaseImportError) as exc_info:
        import_sqlite_database(source_path, "broken.db", tmp_path / "imports")

    assert exc_info.value.code == "DATABASE_IMPORT_FAILED"
