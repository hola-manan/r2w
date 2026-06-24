"""Blackboard write-protocol (P05 contract). Design doc §15.3.

Single-writer rule: each artifact type has exactly one owning agent. Agents
never edit another stage's nodes directly; cross-stage changes flow as
ProposedPatch objects through impact review, then the OWNING agent applies them.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.graph import GraphRepository
from app.schemas import DocumentType, Envelope

# The single writer for each artifact type.
OWNER: dict[DocumentType, str] = {
    DocumentType.REQUIREMENT: "requirements_analyst",
    DocumentType.PRD_ITEM: "prd_author",
    DocumentType.ADR: "stack_advisor",
    DocumentType.SPEC_COMPONENT: "architect",
    DocumentType.TASK: "planner",
}


class ProposedPatch(BaseModel):
    target_id: str
    target_type: DocumentType
    change: dict = Field(default_factory=dict)  # fields to overwrite on the target node
    origin_agent: str
    reason: str = ""


class BlackboardViolation(Exception):
    pass


def can_apply(agent_name: str, target_type: DocumentType) -> bool:
    return OWNER.get(target_type) == agent_name


def apply_patch(repo: GraphRepository, patch: ProposedPatch, applying_agent: str) -> Envelope:
    """Apply a proposed patch — only the owning agent may do so."""
    if not can_apply(applying_agent, patch.target_type):
        raise BlackboardViolation(
            f"agent '{applying_agent}' may not write {patch.target_type.value}; "
            f"owner is '{OWNER[patch.target_type]}'"
        )
    node = repo.get(patch.target_id)
    # Applying a fix clears the stale flag.
    updated = node.model_copy(update={**patch.change, "stale": False})
    return repo.upsert(updated, agent=applying_agent)
