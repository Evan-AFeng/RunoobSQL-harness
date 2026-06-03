from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TARGET_DIR = ROOT / "backend"
SEE_DOC = "docs/conventions/logging.md"


def _iter_python_files() -> list[Path]:
    if not TARGET_DIR.exists():
        return []

    return sorted(path for path in TARGET_DIR.rglob("*.py") if "__pycache__" not in path.relative_to(ROOT).parts)


def _is_print_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"


def _find_print_calls(path: Path) -> list[int]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))

    return [node.lineno for node in ast.walk(tree) if _is_print_call(node)]


def main() -> int:
    violations: list[tuple[Path, int]] = []

    for path in _iter_python_files():
        for line_number in _find_print_calls(path):
            violations.append((path, line_number))

    for path, line_number in violations:
        relative_path = path.relative_to(ROOT).as_posix()
        print(f"❌ 后端代码禁止直接使用 print: {relative_path}:{line_number}")
        print("✅ FIX: 使用 logging 输出日志，例如：")
        print("```python")
        print("import logging")
        print("")
        print("logger = logging.getLogger(__name__)")
        print('logger.info("message")')
        print("```")
        print(f"📖 See: {SEE_DOC}")

    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
