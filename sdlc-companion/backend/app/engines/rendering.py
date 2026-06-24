"""Render graph nodes into compact text for LLM scoring/impact (P04)."""
from __future__ import annotations

from app.graph import GraphRepository
from app.schemas import DocumentType, Envelope


def render_node(node: Envelope) -> str:
    d = node.model_dump(mode="json")
    skip = {"version", "created_by_agent", "last_changed", "project_id", "doc_type", "stale"}
    fields = {k: v for k, v in d.items() if k not in skip and v not in ([], {}, "", None)}
    inner = "; ".join(f"{k}={v}" for k, v in fields.items() if k != "id")
    return f"[{node.id}] {inner}"


def render_type(repo: GraphRepository, doc_type: DocumentType) -> str:
    nodes = repo.list_by_type(doc_type)
    if not nodes:
        return f"({doc_type.value}: none yet)"
    return "\n".join(render_node(n) for n in nodes)


def stage_context(repo: GraphRepository, stage: int, profile_summary: str = "") -> str:
    parts: list[str] = []
    if stage == 1:
        parts.append("REQUIREMENTS:\n" + render_type(repo, DocumentType.REQUIREMENT))
    elif stage == 2:
        parts.append("REQUIREMENTS:\n" + render_type(repo, DocumentType.REQUIREMENT))
        parts.append("PRD ITEMS:\n" + render_type(repo, DocumentType.PRD_ITEM))
    elif stage == 3:
        parts.append("PRD ITEMS:\n" + render_type(repo, DocumentType.PRD_ITEM))
        parts.append("ADRs:\n" + render_type(repo, DocumentType.ADR))
        if profile_summary:
            parts.append("PROFILE:\n" + profile_summary)
    elif stage == 4:
        parts.append("PRD ITEMS:\n" + render_type(repo, DocumentType.PRD_ITEM))
        parts.append("ADRs:\n" + render_type(repo, DocumentType.ADR))
        parts.append("SPEC COMPONENTS:\n" + render_type(repo, DocumentType.SPEC_COMPONENT))
    elif stage == 5:
        parts.append("SPEC COMPONENTS:\n" + render_type(repo, DocumentType.SPEC_COMPONENT))
        parts.append("TASKS:\n" + render_type(repo, DocumentType.TASK))
    return "\n\n".join(parts)
