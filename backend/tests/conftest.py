from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from app import create_app
from flask import Flask
from flask.testing import FlaskClient


@pytest.fixture
def app(tmp_path: Path) -> Flask:
    return create_app({"TESTING": True, "DATABASE_IMPORT_DIR": str(tmp_path / "imports")})


@pytest.fixture
def client(app: Flask) -> Iterator[FlaskClient]:
    with app.test_client() as test_client:
        yield test_client
