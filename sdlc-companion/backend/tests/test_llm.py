"""P01: the LLM client forwards the configured request timeout + key to the SDK.

Runs offline by injecting a fake `google.genai` module so no key/network is needed.
"""
from __future__ import annotations

import sys
import types

from app.config import Settings
from app.llm.client import LLMClient


def test_request_timeout_default_is_60s():
    assert Settings().request_timeout == 60.0


def test_client_forwards_key_and_timeout_to_genai(monkeypatch):
    captured: dict = {}

    class FakeClient:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    class FakeHttpOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    # Fake the `google.genai` and `google.genai.types` modules.
    genai_module = types.ModuleType("google.genai")
    genai_module.Client = FakeClient
    types_module = types.ModuleType("google.genai.types")
    types_module.HttpOptions = FakeHttpOptions
    genai_module.types = types_module
    google_pkg = types.ModuleType("google")
    google_pkg.genai = genai_module

    monkeypatch.setitem(sys.modules, "google", google_pkg)
    monkeypatch.setitem(sys.modules, "google.genai", genai_module)
    monkeypatch.setitem(sys.modules, "google.genai.types", types_module)

    client = LLMClient(Settings(google_api_key="test-key", request_timeout=12.5))
    client._ensure_client()

    assert captured["api_key"] == "test-key"
    assert captured["vertexai"] is True
    # 12.5s -> 12500ms, in milliseconds as google-genai expects.
    assert captured["http_options"].kwargs["timeout"] == 12500
