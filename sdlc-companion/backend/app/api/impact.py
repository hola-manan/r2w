"""Impact routes: run analysis, accept patch, dismiss with reason (P07)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import build_conductor
from app.api.dto import node_to_dto
from app.db.session import get_session
from app.orchestrator import ProposedPatch, save_state
from app.schemas import DocumentType

router = APIRouter(tags=["impact"])


class RunImpact(BaseModel):
    changed_ids: list[str]


class AcceptPatch(BaseModel):
    target_id: str
    target_type: str
    change: dict


class DismissItem(BaseModel):
    node_id: str
    reason: str


@router.post("/projects/{project_id}/impact")
def run_impact(project_id: str, body: RunImpact, session: Session = Depends(get_session)) -> dict:
    a = build_conductor(session, project_id)
    report = a.conductor.run_impact(a.state, body.changed_ids)
    save_state(session, a.state)
    return report.model_dump()


@router.post("/projects/{project_id}/impact/accept")
def accept_patch(
    project_id: str, body: AcceptPatch, session: Session = Depends(get_session)
) -> dict:
    a = build_conductor(session, project_id)
    patch = ProposedPatch(
        target_id=body.target_id,
        target_type=DocumentType(body.target_type),
        change=body.change,
        origin_agent="impact_analyzer",
    )
    updated = a.conductor.apply_impact_patch(patch)
    # Accepting a patch changes the node's content, which opens the next impact pass on
    # it (the human-ack-between-passes cascade, design §13.4): re-analyze from the patched
    # node so any newly-affected neighbors are flagged rather than silently left stale.
    report = a.conductor.run_impact(a.state, [updated.id])
    save_state(session, a.state)
    return {"node": node_to_dto(a.repo, updated), "impact": report.model_dump()}


@router.post("/projects/{project_id}/impact/dismiss")
def dismiss(project_id: str, body: DismissItem, session: Session = Depends(get_session)) -> dict:
    if not body.reason.strip():
        raise HTTPException(status_code=400, detail="dismiss requires a reason")
    a = build_conductor(session, project_id)
    a.repo.set_stale(body.node_id, False)
    # An honest audit trail: the accepted-inconsistency note (design §13.5).
    return {"node_id": body.node_id, "dismissed": True, "reason": body.reason}
