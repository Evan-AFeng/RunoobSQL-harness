from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_LINES = 500
SEE_DOC = "docs/conventions/linters.md"

INCLUDED_SUFFIXES = {
    ".bat",
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".ts",
    ".vue",
    ".yaml",
    ".yml",
}
EXCLUDED_DIRS = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts)


def _iter_files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.suffix in INCLUDED_SUFFIXES and not _is_excluded(path)
    )


def _count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as file:
            return sum(1 for _ in file)
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8-sig") as file:
            return sum(1 for _ in file)


def main() -> int:
    violations: list[tuple[Path, int]] = []

    for path in _iter_files():
        line_count = _count_lines(path)
        if line_count > MAX_LINES:
            violations.append((path, line_count))

    for path, line_count in violations:
        relative_path = path.relative_to(ROOT).as_posix()
        print(f"❌ 单文件超过 {MAX_LINES} 行: {relative_path} 当前 {line_count} 行")
        print("✅ FIX: 拆分文件，把路由、业务逻辑、组件或配置移到更小的模块，例如：")
        print("```python")
        print("from app.services.query_service import run_query")
        print("")
        print("")
        print("@query_bp.post('/api/query')")
        print("def query():")
        print("    return run_query(request.get_json())")
        print("```")
        print(f"📖 See: {SEE_DOC}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
