from __future__ import annotations

import json
import logging
from collections.abc import Iterator
from typing import Any, Protocol

from openai import OpenAI

from app.configs.llm import LlmConfig
from app.services.errors import Nl2SqlError

logger = logging.getLogger(__name__)


class SqlGenerator(Protocol):
    def generate_sql(self, question: str, dataset_context: str) -> str:
        pass


class StreamingSqlGenerator(SqlGenerator, Protocol):
    def stream_sql_chunks(self, question: str, dataset_context: str) -> Iterator[str]:
        pass


class OpenAiCompatibleClient:
    def __init__(self, config: LlmConfig) -> None:
        self._config = config

    def generate_sql(self, question: str, dataset_context: str) -> str:
        if not self._config.api_key:
            logger.error("llm request rejected: api key missing model=%s", self._config.model, stack_info=True)
            raise Nl2SqlError("llm api key is not configured")

        try:
            logger.info(
                "llm sql generation started model=%s base_url=%s question_length=%s context_length=%s",
                self._config.model,
                self._config.base_url,
                len(question),
                len(dataset_context),
            )
            client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
                timeout=self._config.timeout_seconds,
            )
            completion = client.chat.completions.create(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._user_prompt(question, dataset_context)},
                ],
            )
            content = completion.choices[0].message.content
        except Exception as exc:
            logger.exception("llm request failed model=%s base_url=%s", self._config.model, self._config.base_url)
            raise Nl2SqlError("llm request failed") from exc

        if content is None:
            logger.error("llm returned empty content model=%s", self._config.model, stack_info=True)
            raise Nl2SqlError("llm returned empty content")
        sql = extract_sql(content)
        logger.info("llm sql generation succeeded model=%s sql_length=%s", self._config.model, len(sql))
        return sql

    def stream_sql_chunks(self, question: str, dataset_context: str) -> Iterator[str]:
        if not self._config.api_key:
            logger.error("llm stream rejected: api key missing model=%s", self._config.model, stack_info=True)
            raise Nl2SqlError("llm api key is not configured")

        try:
            logger.info(
                "llm sql streaming started model=%s base_url=%s question_length=%s context_length=%s",
                self._config.model,
                self._config.base_url,
                len(question),
                len(dataset_context),
            )
            client = OpenAI(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
                timeout=self._config.timeout_seconds,
            )
            stream = client.chat.completions.create(
                model=self._config.model,
                messages=[
                    {"role": "system", "content": self._system_prompt()},
                    {"role": "user", "content": self._user_prompt(question, dataset_context)},
                ],
                stream=True,
            )
            is_thinking = False
            for chunk in stream:
                chunk_text, is_thinking = extract_stream_chunk_text(chunk, is_thinking)
                if chunk_text:
                    yield chunk_text

            if is_thinking:
                yield "</think>"
        except Exception as exc:
            logger.exception("llm streaming failed model=%s base_url=%s", self._config.model, self._config.base_url)
            raise Nl2SqlError("llm request failed") from exc

        logger.info("llm sql streaming finished model=%s", self._config.model)

    @staticmethod
    def _system_prompt() -> str:
        from app.services.prompts import SYSTEM_PROMPT

        return SYSTEM_PROMPT

    @staticmethod
    def _user_prompt(question: str, dataset_context: str) -> str:
        from app.services.prompts import build_user_prompt

        return build_user_prompt(question, dataset_context)


def extract_sql(content: str) -> str:
    content_without_think = strip_think_blocks(content)
    json_start = content_without_think.find("{")
    json_end = content_without_think.rfind("}")
    if json_start >= 0 and json_end >= json_start:
        content_without_think = content_without_think[json_start : json_end + 1]

    try:
        parsed = json.loads(content_without_think)
    except json.JSONDecodeError as exc:
        logger.exception("llm returned invalid json content_length=%s", len(content))
        raise Nl2SqlError("llm returned invalid json") from exc

    sql = parsed.get("sql")
    if not isinstance(sql, str) or not sql.strip():
        logger.error("llm response missing sql content_length=%s", len(content), stack_info=True)
        raise Nl2SqlError("llm response missing sql")
    return sql.strip()


def strip_think_blocks(content: str) -> str:
    remaining = content
    while True:
        start = remaining.lower().find("<think>")
        if start < 0:
            return remaining

        end = remaining.lower().find("</think>", start)
        if end < 0:
            return remaining[:start]

        remaining = remaining[:start] + remaining[end + len("</think>") :]


def extract_stream_chunk_text(chunk: Any, is_thinking: bool) -> tuple[str, bool]:
    choices = getattr(chunk, "choices", None) or []
    if not choices:
        logger.debug("llm stream chunk skipped: empty choices")
        return "", is_thinking

    delta = getattr(choices[0], "delta", None)
    if delta is None:
        logger.debug("llm stream chunk skipped: missing delta")
        return "", is_thinking

    reasoning_content = getattr(delta, "reasoning_content", None)
    if reasoning_content:
        prefix = "" if is_thinking else "<think>"
        return f"{prefix}{reasoning_content}", True

    content = getattr(delta, "content", None)
    if content:
        prefix = "</think>" if is_thinking else ""
        return f"{prefix}{content}", False

    return "", is_thinking
