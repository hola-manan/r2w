"""Anthropic client wrapper (P01 contract).

One thin surface used by every engine and agent:
  - `complete()`  -> free text
  - `structured()` -> a validated Pydantic object (forced tool/JSON output)

Scoring and analysis default to temperature 0 for stable, reproducible output.
The `anthropic` import is lazy so unit tests that don't hit the API (and don't
need a key) can import the rest of the app freely.
"""
from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

Message = dict[str, Any]


class LLMError(RuntimeError):
    pass


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None  # lazily constructed
        self.model = self._settings.anthropic_model

    def _ensure_client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError as exc:  # pragma: no cover
                raise LLMError(
                    "anthropic package not installed; run pip install -r requirements.txt"
                ) from exc
            if not self._settings.anthropic_api_key:
                raise LLMError("ANTHROPIC_API_KEY is not set")
            self._client = Anthropic(api_key=self._settings.anthropic_api_key)
        return self._client

    def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        client = self._ensure_client()
        resp = client.messages.create(
            model=self.model,
            system=system or "",
            messages=list(messages),
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return "".join(
            block.text for block in resp.content if getattr(block, "type", None) == "text"
        )

    def structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
        max_retries: int = 2,
    ) -> T:
        """Force the model to emit JSON matching `schema` via a single tool.

        Retries on validation failure, feeding the error back to the model.
        """
        client = self._ensure_client()
        tool = {
            "name": "emit",
            "description": f"Return a {schema.__name__} object.",
            "input_schema": schema.model_json_schema(),
        }
        convo: list[Message] = list(messages)
        last_error: Exception | None = None

        for _ in range(max_retries + 1):
            resp = client.messages.create(
                model=self.model,
                system=system or "",
                messages=convo,
                tools=[tool],
                tool_choice={"type": "tool", "name": "emit"},
                temperature=temperature,
                max_tokens=max_tokens,
            )
            tool_use = next(
                (b for b in resp.content if getattr(b, "type", None) == "tool_use"),
                None,
            )
            if tool_use is None:
                last_error = LLMError("model did not call the emit tool")
                continue
            try:
                return schema.model_validate(tool_use.input)
            except ValidationError as exc:
                last_error = exc
                convo.append({"role": "assistant", "content": resp.content})
                convo.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": tool_use.id,
                                "content": f"Validation failed: {exc}. Fix and re-emit.",
                                "is_error": True,
                            }
                        ],
                    }
                )

        raise LLMError(f"structured() failed after retries: {last_error}")


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()
