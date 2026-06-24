"""Projects + profiles routes (P07)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_session
from app.graph import create_project, get_project, list_projects
from app.orchestrator import load_state, new_state, save_state, stage_name
from app.orchestrator.state import STAGES
from app.profile import list_profile_ids, load_profile

router = APIRouter(tags=["projects"])


class CreateProject(BaseModel):
    name: str
    profile_id: str = ""


def _project_summary(session: Session, project_id: str) -> dict:
    row = get_project(session, project_id)
    state = load_state(session, project_id)
    return {
        "id": row.id,
        "name": row.name,
        "profile_id": row.profile_id,
        "current_stage": state.current_stage,
        "persona": state.persona.value,
        "gate_status": {str(k): v.value for k, v in state.gate_status.items()},
        "stage_names": {str(s): stage_name(s) for s in STAGES},
        "project_brief": state.project_brief,
    }


@router.get("/profiles")
def get_profiles() -> list[dict]:
    out = []
    for pid in list_profile_ids():
        prof = load_profile(pid)
        out.append({"id": pid, "name": prof.name,
                    "radar_count": len(prof.radar),
                    "compliance_count": len(prof.compliance)})
    return out


@router.post("/projects")
def post_project(body: CreateProject, session: Session = Depends(get_session)) -> dict:
    if body.profile_id and body.profile_id not in list_profile_ids():
        raise HTTPException(status_code=400, detail=f"unknown profile '{body.profile_id}'")
    row = create_project(session, body.name, body.profile_id)
    state = new_state(row.id)
    save_state(session, state)
    return _project_summary(session, row.id)


@router.get("/projects")
def get_projects(session: Session = Depends(get_session)) -> list[dict]:
    return [_project_summary(session, p.id) for p in list_projects(session)]


@router.get("/projects/{project_id}")
def get_one(project_id: str, session: Session = Depends(get_session)) -> dict:
    if get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    return _project_summary(session, project_id)
