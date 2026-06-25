"""Project state model (P05 contract). Design doc §15.1."""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas import DocumentType, GateStatus, Persona

STAGES = [1, 2, 3, 4, 5]

STAGE_NAMES = {
    1: "Requirements",
    2: "PRD",
    3: "Stack / ADR",
    4: "Tech Spec",
    5: "Task Plan",
}

# Which persona drives each stage (design §4).
_STAGE_PERSONA = {
    1: Persona.BUSINESS_USER,
    2: Persona.BUSINESS_USER,
    3: Persona.TECH_ARCHITECT,
    4: Persona.TECH_ARCHITECT,
    5: Persona.TECH_ARCHITECT,
}

# Which stage owns each artifact type (for needs-review propagation).
STAGE_OF_TYPE = {
    DocumentType.REQUIREMENT: 1,
    DocumentType.PRD_ITEM: 2,
    DocumentType.ADR: 3,
    DocumentType.SPEC_COMPONENT: 4,
    DocumentType.TASK: 5,
}

# Inverse: the artifact type each stage owns (for gate-relock stale checks).
TYPE_OF_STAGE = {stage: doc_type for doc_type, stage in STAGE_OF_TYPE.items()}


def persona_for_stage(stage: int) -> Persona:
    return _STAGE_PERSONA[stage]


def stage_name(stage: int) -> str:
    return STAGE_NAMES[stage]


class Message(BaseModel):
    role: str  # "user" | "agent"
    content: str


class ProjectState(BaseModel):
    project_id: str
    current_stage: int = 1
    persona: Persona = Persona.BUSINESS_USER
    gate_status: dict[int, GateStatus] = Field(default_factory=dict)
    threads: dict[int, list[Message]] = Field(default_factory=dict)
    project_brief: str = ""

    def thread(self, stage: int) -> list[Message]:
        return self.threads.setdefault(stage, [])
