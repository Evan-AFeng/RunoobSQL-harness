from __future__ import annotations

import sqlite3
from contextlib import closing
from io import BytesIO
from pathlib import Path
from typing import Any


def _sqlite_bytes(path: Path) -> bytes:
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT)")
        connection.execute("INSERT INTO products (name) VALUES (?)", ("Keyboard",))
        connection.commit()
    return path.read_bytes()


def test_import_database_endpoint_accepts_sqlite_file(client: Any, tmp_path: Path) -> None:
    database_bytes = _sqlite_bytes(tmp_path / "products.db")

    response = client.post(
        "/api/databases/import",
        data={"file": (BytesIO(database_bytes), "products.db")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["filename"] == "products.db"
    assert body["database_id"].startswith("products-")
    assert body["tables"][0]["name"] == "products"
    assert body["tables"][0]["row_count"] == 1


def test_import_database_endpoint_requires_file(client: Any) -> None:
    response = client.post("/api/databases/import", data={}, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json() == {
        "code": "INVALID_REQUEST",
        "message": "file is required",
        "detail": {},
    }


def test_health_endpoint(client: Any) -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


class RouteSqlGenerator:
    def generate_sql(self, question: str, schema: str) -> str:
        return "SELECT name FROM products LIMIT 1"


class StreamingRouteSqlGenerator(RouteSqlGenerator):
    def stream_sql_chunks(self, question: str, schema: str) -> list[str]:
        return [
            "<think>use products table</think>",
            '{"sql": ',
            '"SELECT name FROM products LIMIT 1"',
            "}",
        ]


def test_query_endpoint_returns_sql_and_rows(client: Any, app: Any, tmp_path: Path) -> None:
    app.config["SQL_GENERATOR"] = RouteSqlGenerator()
    database_bytes = _sqlite_bytes(tmp_path / "products.db")
    import_response = client.post(
        "/api/databases/import",
        data={"file": (BytesIO(database_bytes), "products.db")},
        content_type="multipart/form-data",
    )
    database_id = import_response.get_json()["database_id"]

    response = client.post(
        "/api/query",
        json={"question": "first product", "database_id": database_id},
    )

    assert response.status_code == 200
    assert response.get_json() == {
        "sql": "SELECT name FROM products LIMIT 1",
        "columns": ["name"],
        "rows": [{"name": "Keyboard"}],
    }


def test_query_stream_endpoint_returns_sse_events(client: Any, app: Any, tmp_path: Path) -> None:
    app.config["SQL_GENERATOR"] = StreamingRouteSqlGenerator()
    database_bytes = _sqlite_bytes(tmp_path / "products.db")
    import_response = client.post(
        "/api/databases/import",
        data={"file": (BytesIO(database_bytes), "products.db")},
        content_type="multipart/form-data",
    )
    database_id = import_response.get_json()["database_id"]

    response = client.get(
        "/api/query/stream",
        query_string={"question": "first product", "database_id": database_id},
    )

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert response.mimetype == "text/event-stream"
    assert "event: model_delta" in body
    assert "event: sql" in body
    assert "event: result" in body
    assert "event: done" in body
    assert "use products table" in body
    assert "SELECT name FROM products LIMIT 1" in body
