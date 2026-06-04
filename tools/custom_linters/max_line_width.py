from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_WIDTH = 120
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
    "dist",
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


def _iter_long_lines(path: Path) -> list[tuple[int, int]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8-sig")

    long_lines = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        line_width = len(line)
        if line_width > MAX_WIDTH:
            long_lines.append((line_number, line_width))
    return long_lines


def main() -> int:
    violations: list[tuple[Path, int, int]] = []

    for path in _iter_files():
        for line_number, line_width in _iter_long_lines(path):
            violations.append((path, line_number, line_width))

    for path, line_number, line_width in violations:
        relative_path = path.relative_to(ROOT).as_posix()
        print(f"❌ 行宽超过 {MAX_WIDTH} 字符: {relative_path}:{line_number} 当前 {line_width} 字符")
        print("✅ FIX: 拆分长行，优先使用括号、局部变量或多行结构，例如：")
        print("```python")
        print("result = service.run_query(")
        print("    question=question,")
        print("    limit=limit,")
        print(")")
        print("```")
        print(f"📖 See: {SEE_DOC}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
