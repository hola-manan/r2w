"""project_brief maintenance (P05). Design doc §15.5.

A compact rolling summary (key artifacts + constraints) injected into every
agent so stage-1 nuance survives stage transitions without dumping transcripts.
"""
from __future__ import annotations

from app.graph import GraphRepository
from app.orchestrator.state import ProjectState, stage_name
from app.schemas import DocumentType

_COUNT_TYPES = [
    (DocumentType.REQUIREMENT, "requirements"),
    (DocumentType.PRD_ITEM, "PRD items"),
    (DocumentType.ADR, "ADRs"),
    (DocumentType.SPEC_COMPONENT, "spec components"),
    (DocumentType.TASK, "tasks"),
]


def update_brief(state: ProjectState, repo: GraphRepository, profile_summary: str = "") -> str:
    lines: list[str] = []
    lines.append(f"Project at stage {state.current_stage} ({stage_name(state.current_stage)}).")
    counts = []
    for doc_type, label in _COUNT_TYPES:
        n = len(repo.list_by_type(doc_type))
        if n:
            counts.append(f"{n} {label}")
    if counts:
        lines.append("Artifacts so far: " + ", ".join(counts) + ".")

    # Carry forward the headline decisions (ADR titles) and key requirements.
    reqs = repo.list_by_type(DocumentType.REQUIREMENT)
    if reqs:
        lines.append("Requirements: " + "; ".join(f"{r.id}: {r.statement}" for r in reqs[:6]))
    adrs = [a for a in repo.list_by_type(DocumentType.ADR) if a.status == "accepted"]
    if adrs:
        lines.append("Decisions: " + "; ".join(f"{a.id}: {a.decision}" for a in adrs[:6]))
    if profile_summary:
        lines.append("Grounded in company profile (radar + compliance).")

    state.project_brief = "\n".join(lines)
    return state.project_brief
