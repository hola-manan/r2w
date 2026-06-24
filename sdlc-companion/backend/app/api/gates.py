"""Gate routes: readiness snapshot, advance, reopen (P07)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import build_conductor
from app.db.session import get_session
from app.orchestrator import save_state

router = APIRouter(tags=["gates"])


@router.get("/projects/{project_id}/readiness/{stage}")
def readiness(project_id: str, stage: int, session: Session = Depends(get_session)) -> dict:
    a = build_conductor(session, project_id)
    return a.conductor.readiness_of(stage).model_dump()


@router.post("/projects/{project_id}/advance")
def advance(project_id: str, session: Session = Depends(get_session)) -> dict:
    a = build_conductor(session, project_id)
    result = a.conductor.confirm_stage(a.state)
    save_state(session, a.state)
    return result.model_dump()


@router.post("/projects/{project_id}/reopen/{stage}")
def reopen(project_id: str, stage: int, session: Session = Depends(get_session)) -> dict:
    if stage not in (1, 2, 3, 4, 5):
        raise HTTPException(status_code=400, detail="invalid stage")
    a = build_conductor(session, project_id)
    a.conductor.reopen_stage(a.state, stage)
    save_state(session, a.state)
    return {
        "current_stage": a.state.current_stage,
        "persona": a.state.persona.value,
        "gate_status": {str(k): v.value for k, v in a.state.gate_status.items()},
    }
