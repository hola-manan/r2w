"""Persist ProjectState in the project row's JSON column (P05)."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.graph import get_project
from app.orchestrator.state import ProjectState
from app.orchestrator.state_machine import new_state


def load_state(session: Session, project_id: str) -> ProjectState:
    row = get_project(session, project_id)
    if row is None:
        raise KeyError(f"project {project_id} not found")
    if row.state:
        return ProjectState.model_validate(row.state)
    state = new_state(project_id)
    row.state = state.model_dump(mode="json")
    session.flush()
    return state


def save_state(session: Session, state: ProjectState) -> None:
    row = get_project(session, state.project_id)
    if row is None:
        raise KeyError(f"project {state.project_id} not found")
    row.state = state.model_dump(mode="json")
    session.flush()
