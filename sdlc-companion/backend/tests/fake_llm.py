"""A scriptable fake LLM for engine/agent tests (no API key needed).

`structured()` returns objects produced by a handler keyed on the schema name,
or queued canned responses. `complete()` returns queued strings.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence


class FakeLLM:
    def __init__(self) -> None:
        self.model = "fake"
        self.handlers: dict[str, Callable[[list, type], Any]] = {}
        self.calls: list[tuple[str, list]] = []

    def on(self, schema_name: str, handler: Callable[[list, type], Any]) -> "FakeLLM":
        self.handlers[schema_name] = handler
        return self

    def structured(self, messages, schema, *, system=None, temperature=0.0, **kw):
        self.calls.append((schema.__name__, list(messages)))
        handler = self.handlers.get(schema.__name__)
        if handler is None:
            raise AssertionError(f"FakeLLM has no handler for {schema.__name__}")
        return handler(list(messages), schema)

    def complete(self, messages: Sequence[dict], *, system=None, temperature=0.0, **kw) -> str:
        self.calls.append(("complete", list(messages)))
        handler = self.handlers.get("complete")
        if handler is None:
            return ""
        return handler(list(messages), str)
