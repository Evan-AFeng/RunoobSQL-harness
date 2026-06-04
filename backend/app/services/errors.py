from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppError(Exception):
    code: str
    message: str
    status_code: int
    detail: dict[str, Any] = field(default_factory=dict)

    def to_response(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


class InvalidRequestError(AppError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="INVALID_REQUEST",
            message=message,
            status_code=400,
            detail=detail or {},
        )


class DatabaseImportError(AppError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="DATABASE_IMPORT_FAILED",
            message=message,
            status_code=422,
            detail=detail or {},
        )


class Nl2SqlError(AppError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="NL2SQL_FAILED",
            message=message,
            status_code=422,
            detail=detail or {},
        )


class SqlValidateError(AppError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="SQL_VALIDATE_FAILED",
            message=message,
            status_code=422,
            detail=detail or {},
        )


class SqlExecuteError(AppError):
    def __init__(self, message: str, detail: dict[str, Any] | None = None) -> None:
        super().__init__(
            code="SQL_EXECUTE_FAILED",
            message=message,
            status_code=500,
            detail=detail or {},
        )
