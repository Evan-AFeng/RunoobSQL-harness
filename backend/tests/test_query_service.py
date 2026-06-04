from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest
from app.services.database_import_service import import_sqlite_database
from app.services.errors import SqlValidateError
from app.services.llm_client import extract_sql, extract_stream_chunk_text
from app.services.query_service import run_query


class FakeSqlGenerator:
    def __init__(self, sql: str) -> None:
        self.sql = sql
        self.seen_schema = ""

    def generate_sql(self, question: str, schema: str) -> str:
        self.seen_schema = schema
        return self.sql


def _create_sales_database(path: Path) -> None:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE sales (id INTEGER PRIMARY KEY, product TEXT, amount INTEGER)")
        connection.execute("INSERT INTO sales (product, amount) VALUES (?, ?)", ("Keyboard", 120))
        connection.execute("INSERT INTO sales (product, amount) VALUES (?, ?)", ("Mouse", 80))
        connection.commit()


def test_run_query_generates_and_executes_readonly_sql(tmp_path: Path) -> None:
    source_path = tmp_path / "sales.db"
    import_dir = tmp_path / "imports"
    _create_sales_database(source_path)
    imported = import_sqlite_database(source_path, "sales.db", import_dir)
    sql_generator = FakeSqlGenerator("SELECT product, amount FROM sales ORDER BY amount DESC LIMIT 1")

    result = run_query(
        question="top product",
        database_id=str(imported["database_id"]),
        import_dir=import_dir,
        sql_generator=sql_generator,
    )

    assert "Table: sales" in sql_generator.seen_schema
    assert "Columns: id INTEGER, product TEXT, amount INTEGER" in sql_generator.seen_schema
    assert "Sample rows:" in sql_generator.seen_schema
    assert result == {
        "sql": "SELECT product, amount FROM sales ORDER BY amount DESC LIMIT 1",
        "columns": ["product", "amount"],
        "rows": [{"product": "Keyboard", "amount": 120}],
    }


def test_run_query_rejects_write_sql(tmp_path: Path) -> None:
    source_path = tmp_path / "sales.db"
    import_dir = tmp_path / "imports"
    _create_sales_database(source_path)
    imported = import_sqlite_database(source_path, "sales.db", import_dir)

    with pytest.raises(SqlValidateError) as exc_info:
        run_query(
            question="remove rows",
            database_id=str(imported["database_id"]),
            import_dir=import_dir,
            sql_generator=FakeSqlGenerator("DELETE FROM sales"),
        )

    assert exc_info.value.code == "SQL_VALIDATE_FAILED"


def test_extract_sql_ignores_visible_think_block() -> None:
    content = '<think>look at budget_amount</think>{"sql": "SELECT * FROM sales LIMIT 1"}'

    assert extract_sql(content) == "SELECT * FROM sales LIMIT 1"


class Chunk:
    def __init__(self, choices: list[object]) -> None:
        self.choices = choices


class Choice:
    def __init__(self, delta: object) -> None:
        self.delta = delta


class Delta:
    def __init__(self, content: str | None = None, reasoning_content: str | None = None) -> None:
        self.content = content
        self.reasoning_content = reasoning_content


def test_extract_stream_chunk_text_skips_empty_choices() -> None:
    assert extract_stream_chunk_text(Chunk([]), False) == ("", False)


def test_extract_stream_chunk_text_wraps_reasoning_content_as_think() -> None:
    text, is_thinking = extract_stream_chunk_text(Chunk([Choice(Delta(reasoning_content="scan schema"))]), False)
    assert text == "<think>scan schema"
    assert is_thinking is True

    text, is_thinking = extract_stream_chunk_text(Chunk([Choice(Delta(content='{"sql": "SELECT 1"}'))]), True)
    assert text == '</think>{"sql": "SELECT 1"}'
    assert is_thinking is False
