"""Schemas for the team Tech Capability Catalog + task→tool matching.

Self-contained: this package holds its own contracts so the whole feature is one
copy-pasteable folder (see README.md). The only outward types it constructs are
`app.profile.schema.RadarEntry` (in catalog.py, so a catalog tool validates like an
Adopt radar entry) — the models here are internal to the feature.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class TechCapability(BaseModel):
    """One team tool, parsed from a capability doc in `docs/*.md`."""

    id: str          # filename stem, e.g. "uipath"
    name: str        # display name, e.g. "UiPath"
    category: str    # e.g. rpa | data_prep | low_code
    summary: str = ""  # one-line capability summary (front-matter)
    body: str = ""     # the full markdown body fed to the matcher


class TechMatch(BaseModel):
    """The matcher's fit assessment of one tool against the current task."""

    tool_id: str
    tool_name: str
    score: int = 0  # 0-100 fit
    rationale: str = ""
    recommended: bool = False


class TechMatchOutput(BaseModel):
    """Structured output the matcher LLM call emits (via llm.structured)."""

    matches: list[TechMatch] = Field(default_factory=list)
    summary: str = ""
