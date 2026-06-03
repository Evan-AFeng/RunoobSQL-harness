from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "pyproject.toml"


def _load_lint_config() -> dict[str, Any]:
    with CONFIG_PATH.open("rb") as config_file:
        config = tomllib.load(config_file)

    return config.get("tool", {}).get("runoobsql", {}).get("lint", {})


def _expand_command(command: list[str]) -> list[str]:
    return [part.replace("{python}", sys.executable) for part in command]


def _should_skip(command: list[str], missing_paths: set[str]) -> bool:
    return any(part in missing_paths for part in command)


def main() -> int:
    lint_config = _load_lint_config()
    commands = lint_config.get("default_commands", []) + lint_config.get("custom_commands", [])
    missing_paths = {path for path in lint_config.get("skip_if_missing", []) if not (ROOT / path).exists()}

    if not commands:
        print("No linter commands configured.")
        return 0

    failed = 0
    for raw_command in commands:
        command = _expand_command(raw_command)
        display = " ".join(command)

        if _should_skip(raw_command, missing_paths):
            print(f"SKIP {display}")
            continue

        print(f"RUN  {display}")
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode != 0:
            failed = result.returncode

    return failed


if __name__ == "__main__":
    raise SystemExit(main())
