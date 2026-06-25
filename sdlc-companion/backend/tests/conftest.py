"""Shared test config: force an in-memory DB and a dummy API key."""
from __future__ import annotations

import os

import pytest

os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


@pytest.fixture(autouse=True)
def _clear_readiness_cache():
    # The readiness verdict cache is process-global; clear it before each test so a
    # FakeLLM verdict from one test can't leak into another with the same input.
    from app.engines.readiness import clear_readiness_cache

    clear_readiness_cache()
    yield
