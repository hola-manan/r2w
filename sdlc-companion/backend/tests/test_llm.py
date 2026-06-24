"""P01: the LLM client forwards the configured request timeout to the SDK.

Runs offline by injecting a fake `anthropic` module so no key/network is needed.
"""
from __future__ import annotations

import sys
import types

from app.config import Settings
from app.llm.client import LLMClient


def test_request_timeout_default_is_60s():
    assert Settings().request_timeout == 60.0


def test_client_forwards_timeout_to_anthropic(monkeypatch):
    captured: dict = {}

    class FakeAnthropic:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    fake_module = types.ModuleType("anthropic")
    fake_module.Anthropic = FakeAnthropic
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    client = LLMClient(Settings(anthropic_api_key="test-key", request_timeout=12.5))
    client._ensure_client()

    assert captured["timeout"] == 12.5
    assert captured["api_key"] == "test-key"
