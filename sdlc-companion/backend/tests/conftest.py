"""Shared test config: force an in-memory DB and a dummy API key."""
from __future__ import annotations

import os

os.environ.setdefault("DB_PATH", ":memory:")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
