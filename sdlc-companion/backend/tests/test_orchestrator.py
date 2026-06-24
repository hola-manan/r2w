"""P05 verification: gates, reopen propagation, persona validity, blackboard, persistence."""
from __future__ import annotations

import pytest

from app.db.base import Base
from app.db.session import get_engine, init_db, session_scope
from app.engines import ConsistencyChecker, Verdict
from app.graph import GraphRepository, create_project
from app.orchestrator import (
    Conductor,
    PersonaViolation,
    ProposedPatch,
    advance,
    apply_patch,
    load_state,
    new_state,
    reopen,
    save_state,
)
from app.orchestrator.blackboard import BlackboardViolation
from app.orchestrator.types import AgentContext, AgentResult
from app.schemas import DocumentType, GateStatus, Persona, PRDItem, Requirement
from tests.fake_llm import FakeLLM


@pytest.fixture(autouse=True)
def _db():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def _green_checker():
    llm = FakeLLM()
    llm.on("Verdict", lambda msgs, schema: Verdict(level=3, status="valid", justification="ok"))
    return ConsistencyChecker(llm)


class FakeReqAgent:
    name = "requirements_analyst"
    writes = DocumentType.REQUIREMENT

    def handle(self, ctx: AgentContext) -> AgentResult:
        node = ctx.repo.upsert(Requirement(statement=ctx.message), agent=self.name)
        return AgentResult(reply=f"captured {node.id}", written_ids=[node.id])


def test_persona_violation_rejected():
    with session_scope() as s:
        p = create_project(s, "demo")
        repo = GraphRepository(s, p.id)
        state = new_state(p.id)
        cond = Conductor(repo, _green_checker(), {1: FakeReqAgent()})
        with pytest.raises(PersonaViolation):
            cond.handle_message(state, "hi", Persona.TECH_ARCHITECT)


def test_handle_message_writes_and_scores():
    with session_scope() as s:
        p = create_project(s, "demo")
        repo = GraphRepository(s, p.id)
        state = new_state(p.id)
        cond = Conductor(repo, _green_checker(), {1: FakeReqAgent()})
        resp = cond.handle_message(state, "users can export data", Persona.BUSINESS_USER)
        assert resp.written_ids == ["REQ-1"]
        assert resp.scorecard.stage == 1
        assert state.project_brief  # brief updated


def test_gate_blocks_then_advances():
    with session_scope() as s:
        p = create_project(s, "demo")
        repo = GraphRepository(s, p.id)
        state = new_state(p.id)
        # checker that fails stage-1 qualitative dims -> gate blocked
        red = FakeLLM()
        red.on("Verdict", lambda m, sch: Verdict(level=0, justification="vague",
                                                  followup_question="clarify?"))
        cond = Conductor(repo, ConsistencyChecker(red), {1: FakeReqAgent()})
        cond.handle_message(state, "do stuff", Persona.BUSINESS_USER)
        res = cond.confirm_stage(state)
        assert res.advanced is False
        assert state.current_stage == 1

        # now all-green -> advances to stage 2, persona stays business_user
        cond2 = Conductor(repo, _green_checker(), {1: FakeReqAgent()})
        res2 = cond2.confirm_stage(state)
        assert res2.advanced is True
        assert state.current_stage == 2
        assert state.persona == Persona.BUSINESS_USER
        assert state.gate_status[1] == GateStatus.PASSED


def test_reopen_sets_downstream_needs_review():
    state = new_state("P1")
    # pretend a completed project: all stages passed
    for stg in (1, 2, 3, 4, 5):
        state.gate_status[stg] = GateStatus.PASSED
    state.current_stage = 5
    reopen(state, 3)
    assert state.current_stage == 3
    assert state.persona == Persona.TECH_ARCHITECT
    assert state.gate_status[3] == GateStatus.LOCKED
    assert state.gate_status[4] == GateStatus.NEEDS_REVIEW
    assert state.gate_status[5] == GateStatus.NEEDS_REVIEW


def test_blackboard_single_writer():
    with session_scope() as s:
        p = create_project(s, "demo")
        repo = GraphRepository(s, p.id)
        prd = repo.upsert(PRDItem(title="Export"))
        patch = ProposedPatch(
            target_id=prd.id, target_type=DocumentType.PRD_ITEM,
            change={"title": "Export v2"}, origin_agent="architect",
        )
        # architect is NOT the owner of PRD items
        with pytest.raises(BlackboardViolation):
            apply_patch(repo, patch, "architect")
        # prd_author owns PRD items
        updated = apply_patch(repo, patch, "prd_author")
        assert updated.title == "Export v2"


def test_state_persists_round_trip():
    with session_scope() as s:
        p = create_project(s, "demo")
        state = load_state(s, p.id)
        advance(state, True)  # stage 1 -> 2
        save_state(s, state)
    with session_scope() as s:
        reloaded = load_state(s, p.id)
        assert reloaded.current_stage == 2
        assert reloaded.gate_status[1] == GateStatus.PASSED
