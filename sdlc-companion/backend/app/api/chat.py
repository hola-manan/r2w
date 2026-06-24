"""Chat routes: REST message, ADR challenge, and a streaming WebSocket (P07).

The WS emits the typed event union the frontend codes against:
  reply | artifact_upserted | scorecard | impact_diff | escalation | needs_review | done
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import build_conductor
from app.api.dto import node_to_dto
from app.db.session import get_session, session_scope
from app.orchestrator import save_state
from app.orchestrator.state_machine import PersonaViolation
from app.schemas import GateStatus, Persona

router = APIRouter(tags=["chat"])


class MessageIn(BaseModel):
    message: str
    persona: str


class ChallengeIn(BaseModel):
    adr_id: str
    objection: str


def _persona(value: str) -> Persona:
    try:
        return Persona(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"unknown persona '{value}'")


def _run_turn(session: Session, project_id: str, message: str, persona: Persona) -> dict:
    a = build_conductor(session, project_id)
    try:
        resp = a.conductor.handle_message(a.state, message, persona)
    except PersonaViolation as exc:
        raise HTTPException(status_code=409, detail=str(exc))

    impact = None
    # Run impact after edits once there is downstream structure (stage >= 3).
    if resp.written_ids and a.state.current_stage >= 3:
        report = a.conductor.run_impact(a.state, resp.written_ids)
        impact = report.model_dump()

    save_state(session, a.state)
    nodes = [node_to_dto(a.repo, a.repo.get(nid)) for nid in resp.written_ids]
    return {
        "reply": resp.reply,
        "written": nodes,
        "scorecard": resp.scorecard.model_dump(),
        "escalation": resp.escalation,
        "impact": impact,
        "needs_review": [s for s, st in a.state.gate_status.items()
                         if st == GateStatus.NEEDS_REVIEW],
    }


@router.post("/projects/{project_id}/message")
def post_message(project_id: str, body: MessageIn, session: Session = Depends(get_session)) -> dict:
    return _run_turn(session, project_id, body.message, _persona(body.persona))


@router.post("/projects/{project_id}/challenge")
def post_challenge(project_id: str, body: ChallengeIn, session: Session = Depends(get_session)) -> dict:
    a = build_conductor(session, project_id)
    agent = a.conductor.agents.get(3)
    from app.orchestrator.types import AgentContext

    ctx = AgentContext(repo=a.repo, message=body.objection, persona=Persona.TECH_ARCHITECT,
                       project_brief=a.state.project_brief, retriever=a.retriever)
    result = agent.challenge(ctx, body.adr_id, body.objection)
    report = a.conductor.run_impact(a.state, result.written_ids) if result.written_ids else None
    save_state(session, a.state)
    nodes = [node_to_dto(a.repo, a.repo.get(nid)) for nid in result.written_ids]
    return {
        "reply": result.reply,
        "written": nodes,
        "escalation": result.escalation,
        "impact": report.model_dump() if report else None,
    }


@router.websocket("/projects/{project_id}/ws")
async def ws(websocket: WebSocket, project_id: str) -> None:
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            persona_str = data.get("persona", "")
            try:
                persona = Persona(persona_str)
            except ValueError:
                await websocket.send_json({"t": "error", "detail": f"bad persona '{persona_str}'"})
                continue
            try:
                with session_scope() as session:
                    turn = _run_turn(session, project_id, message, persona)
            except HTTPException as exc:
                await websocket.send_json({"t": "error", "detail": exc.detail})
                continue

            if turn["reply"]:
                await websocket.send_json({"t": "reply", "stage": None, "text": turn["reply"]})
            for node in turn["written"]:
                await websocket.send_json({"t": "artifact_upserted", "node": node})
            await websocket.send_json({"t": "scorecard", "scorecard": turn["scorecard"]})
            if turn["escalation"]:
                await websocket.send_json({"t": "escalation", "payload": turn["escalation"]})
            if turn["impact"] and turn["impact"]["items"]:
                await websocket.send_json({"t": "impact_diff", "items": turn["impact"]["items"]})
            if turn["needs_review"]:
                await websocket.send_json({"t": "needs_review", "stages": turn["needs_review"]})
            await websocket.send_json({"t": "done"})
    except WebSocketDisconnect:
        return
