"""Artifacts + graph routes (P07)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dto import graph_dto, node_to_dto
from app.db.session import get_session
from app.graph import GraphRepository, get_project
from app.orchestrator.state import STAGE_OF_TYPE
from app.schemas import DocumentType

router = APIRouter(tags=["artifacts"])

_TYPE_BY_NAME = {t.value: t for t in DocumentType}
_TYPES_BY_STAGE = {stage: dt for dt, stage in STAGE_OF_TYPE.items()}


@router.get("/projects/{project_id}/artifacts")
def list_artifacts(
    project_id: str,
    stage: int | None = None,
    type: str | None = None,
    session: Session = Depends(get_session),
) -> list[dict]:
    if get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    repo = GraphRepository(session, project_id)
    if type:
        doc_type = _TYPE_BY_NAME.get(type)
        if doc_type is None:
            raise HTTPException(status_code=400, detail=f"unknown type '{type}'")
        nodes = repo.list_by_type(doc_type)
    elif stage:
        doc_type = _TYPES_BY_STAGE.get(stage)
        nodes = repo.list_by_type(doc_type) if doc_type else []
    else:
        nodes = repo.list_all()
    return [node_to_dto(repo, n) for n in nodes]


@router.get("/projects/{project_id}/graph")
def get_graph(project_id: str, session: Session = Depends(get_session)) -> dict:
    if get_project(session, project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    return graph_dto(GraphRepository(session, project_id))
