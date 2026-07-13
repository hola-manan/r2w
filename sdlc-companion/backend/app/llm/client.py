"""Gemini client wrapper (P01 contract), via Vertex AI Express mode.

One thin surface used by every engine and agent:
  - `complete()`  -> free text
  - `structured()` -> a validated Pydantic object (forced JSON output)

Backed by the unified `google-genai` SDK pointed at Vertex AI in *Express mode*,
which authenticates with a single API key instead of full GCP credentials
(client = genai.Client(vertexai=True, api_key=...)). The default model is
`gemini-2.5-flash`.

Scoring and analysis default to temperature 0 for stable, reproducible output.
The `google.genai` import is lazy so unit tests that don't hit the API (and don't
need a key) can import the rest of the app freely.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Any, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import Settings, get_settings

T = TypeVar("T", bound=BaseModel)

Message = dict[str, Any]


class LLMError(RuntimeError):
    pass


def _to_contents(messages: Sequence[Message]) -> list[dict[str, Any]]:
    """Translate our internal `{role, content}` messages into google-genai `contents`.

    Callers pass `{"role": "user"|"assistant", "content": <str>}`. Gemini uses
    the role name "model" for assistant turns and wraps text in `parts`.
    """
    contents: list[dict[str, Any]] = []
    for m in messages:
        role = "model" if m.get("role") == "assistant" else "user"
        content = m.get("content", "")
        text = content if isinstance(content, str) else str(content)
        contents.append({"role": role, "parts": [{"text": text}]})
    return contents


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._client = None  # lazily constructed
        self.model = self._settings.google_model

    def _ensure_client(self):
        if self._client is None:
            try:
                from google import genai
                from google.genai import types
            except ImportError as exc:  # pragma: no cover
                raise LLMError(
                    "google-genai package not installed; run pip install -r requirements.txt"
                ) from exc
            if not self._settings.google_api_key:
                raise LLMError("GOOGLE_API_KEY is not set")
            self._client = genai.Client(
                vertexai=True,
                api_key=self._settings.google_api_key,
                http_options=types.HttpOptions(
                    # google-genai expresses the request timeout in milliseconds.
                    timeout=int(self._settings.request_timeout * 1000),
                ),
            )
        return self._client

    def _config(self, *, system, temperature, max_tokens, **extra):
        from google.genai import types

        return types.GenerateContentConfig(
            system_instruction=system or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
            # gemini-2.5-* enable "thinking" by default, which spends the output-token budget
            # on reasoning and truncates our structured JSON mid-object. These agents/engines
            # emit structured output at temperature 0 and don't need it, so disable it.
            thinking_config=types.ThinkingConfig(thinking_budget=0),
            **extra,
        )

    def complete(
        self,
        messages: Sequence[Message],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 2048,
    ) -> str:
        client = self._ensure_client()
        resp = client.models.generate_content(
            model=self.model,
            contents=_to_contents(messages),
            config=self._config(
                system=system, temperature=temperature, max_tokens=max_tokens
            ),
        )
        return resp.text or ""

    def structured(
        self,
        messages: Sequence[Message],
        schema: type[T],
        *,
        system: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 8192,
        max_retries: int = 2,
    ) -> T:
        """Force the model to emit JSON matching `schema`.

        Uses Gemini's native structured output (response_mime_type=application/json
        + response_schema). Retries on validation failure, feeding the error back
        to the model so it can correct itself.
        """
        client = self._ensure_client()
        config = self._config(
            system=system,
            temperature=temperature,
            max_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=schema,
        )
        contents = _to_contents(messages)
        last_error: Exception | None = None

        for _ in range(max_retries + 1):
            resp = client.models.generate_content(
                model=self.model, contents=contents, config=config
            )
            raw = resp.text or ""
            try:
                return schema.model_validate_json(raw)
            except ValidationError as exc:
                last_error = exc
                contents.append({"role": "model", "parts": [{"text": raw}]})
                contents.append(
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"Validation failed: {exc}. Fix and re-emit valid JSON."}
                        ],
                    }
                )

        raise LLMError(f"structured() failed after retries: {last_error}")


@lru_cache
def get_llm() -> LLMClient:
    return LLMClient()
