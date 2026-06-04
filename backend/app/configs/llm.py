from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class LlmConfig:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: int


def _get_env_string(name: str, default: str = "") -> str:
    value = os.getenv(name)
    return value if value is not None else default


def load_llm_config() -> LlmConfig:
    return LlmConfig(
        base_url=_get_env_string(
            "RUNOOBSQL_LLM_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        api_key=_get_env_string("RUNOOBSQL_LLM_API_KEY"),
        model=_get_env_string("RUNOOBSQL_LLM_MODEL", "qwen-plus"),
        timeout_seconds=int(_get_env_string("RUNOOBSQL_LLM_TIMEOUT_SECONDS", "30")),
    )
