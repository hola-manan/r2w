"""Structured draft schemas the agents emit via llm.structured (P06).

Keeping the LLM output schema separate from the persisted artifact schema lets
the agent validate/ground the draft before writing it to the graph.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ReqDraft(BaseModel):
    id: Optional[str] = None  # set to update an existing requirement
    statement: str
    req_type: str = "functional"  # functional | nfr
    open_questions: list[str] = Field(default_factory=list)


class ReqAnalystOutput(BaseModel):
    reply: str
    requirements: list[ReqDraft] = Field(default_factory=list)


class PRDDraft(BaseModel):
    id: Optional[str] = None
    title: str
    description: str = ""
    acceptance_criteria: list[str] = Field(default_factory=list)
    priority: str = "should"
    linked_requirements: list[str] = Field(default_factory=list)


class PRDAuthorOutput(BaseModel):
    reply: str
    items: list[PRDDraft] = Field(default_factory=list)


class ADROptionDraft(BaseModel):
    name: str
    ring: Optional[str] = None
    excluded: bool = False
    note: Optional[str] = None


class ADRDraft(BaseModel):
    decision: str
    category: str = ""
    chosen: str
    context: list[str] = Field(default_factory=list)  # PRD / COMP ids driving the decision
    options: list[ADROptionDraft] = Field(default_factory=list)
    rationale: str = ""
    satisfies: list[str] = Field(default_factory=list)  # PRD / COMP ids
    radar_refs: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class StackAdvisorOutput(BaseModel):
    reply: str
    adrs: list[ADRDraft] = Field(default_factory=list)
    escalation: Optional[dict] = None


class SpecDraft(BaseModel):
    id: Optional[str] = None
    name: str
    responsibility: str = ""
    tech_refs: list[str] = Field(default_factory=list)  # ADR ids
    interfaces: list[str] = Field(default_factory=list)
    data: dict = Field(default_factory=dict)
    linked_prd: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class AdrChangeDraft(BaseModel):
    target_id: str
    change: dict = Field(default_factory=dict)
    reason: str = ""


class ArchitectOutput(BaseModel):
    reply: str
    components: list[SpecDraft] = Field(default_factory=list)
    proposed_adr_changes: list[AdrChangeDraft] = Field(default_factory=list)


class TaskDraft(BaseModel):
    id: Optional[str] = None
    title: str
    epic: Optional[str] = None
    estimate: Optional[str] = None
    depends_on: list[str] = Field(default_factory=list)
    linked_spec: list[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    reply: str
    tasks: list[TaskDraft] = Field(default_factory=list)
