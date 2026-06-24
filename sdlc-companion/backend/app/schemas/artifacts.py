"""Artifact schemas (P01 contract) — the five node types + common envelope.

Mirrors design doc §8. Every node carries the envelope (id, version, audit,
stale flag). `id` may be empty on creation; the graph repository (P02) assigns
the sequential, prefixed ID on insert.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional

from pydantic import BaseModel, Field

from .enums import DocumentType, Ring


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Envelope(BaseModel):
    id: str = ""  # assigned by the repository on insert when empty
    project_id: str = ""
    doc_type: DocumentType
    version: int = 1
    created_by_agent: Optional[str] = None
    last_changed: datetime = Field(default_factory=_now)
    stale: bool = False


class Requirement(Envelope):
    doc_type: Literal[DocumentType.REQUIREMENT] = DocumentType.REQUIREMENT
    statement: str
    req_type: Literal["functional", "nfr"] = "functional"
    source_turn: Optional[int] = None
    status: str = "draft"
    readiness: dict[str, int] = Field(default_factory=dict)
    linked_prd: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class PRDItem(Envelope):
    doc_type: Literal[DocumentType.PRD_ITEM] = DocumentType.PRD_ITEM
    title: str
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: Literal["must", "should", "could", "wont"] = "should"
    linked_requirements: list[str] = Field(default_factory=list)
    status: str = "draft"


class ADROption(BaseModel):
    name: str
    ring: Optional[Ring] = None
    excluded: bool = False
    note: Optional[str] = None


class ADR(Envelope):
    doc_type: Literal[DocumentType.ADR] = DocumentType.ADR
    decision: str
    context: list[str] = Field(default_factory=list)  # PRD / COMP ids
    options: list[ADROption] = Field(default_factory=list)
    chosen: str = ""
    rationale: str = ""
    satisfies: list[str] = Field(default_factory=list)  # PRD / COMP ids
    radar_refs: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    status: Literal["accepted", "superseded"] = "accepted"
    superseded_by: Optional[str] = None


class SpecComponent(Envelope):
    doc_type: Literal[DocumentType.SPEC_COMPONENT] = DocumentType.SPEC_COMPONENT
    name: str
    responsibility: str = ""
    tech_refs: list[str] = Field(default_factory=list)  # ADR ids
    interfaces: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)
    linked_prd: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class Task(Envelope):
    doc_type: Literal[DocumentType.TASK] = DocumentType.TASK
    title: str
    epic: Optional[str] = None
    estimate: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)  # TASK ids
    linked_spec: list[str] = Field(default_factory=list)  # SPEC ids


# Registry used for ORM<->Pydantic round-trips (P02) and DTO mapping (P07).
ARTIFACT_MODELS: dict[DocumentType, type[Envelope]] = {
    DocumentType.REQUIREMENT: Requirement,
    DocumentType.PRD_ITEM: PRDItem,
    DocumentType.ADR: ADR,
    DocumentType.SPEC_COMPONENT: SpecComponent,
    DocumentType.TASK: Task,
}
