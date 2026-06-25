"""P10 verification: full cold-start walkthrough + profile-swap divergence.

Uses a scripted FakeLLM so the whole pipeline runs without an API key and the
design's acceptance scenarios are checked automatically.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agents import StackAdvisor
from app.agents.drafts import (
    ADRDraft,
    ArchitectOutput,
    PlannerOutput,
    PRDAuthorOutput,
    PRDDraft,
    ReqAnalystOutput,
    ReqDraft,
    SpecDraft,
    StackAdvisorOutput,
    TaskDraft,
)
from app.api import deps
from app.db.base import Base
from app.db.session import get_engine, init_db
from app.engines import Verdict
from app.graph import GraphRepository, create_project
from app.orchestrator.types import AgentContext
from app.profile import ProfileRetriever, load_profile
from app.schemas import Persona, PRDItem
from tests.fake_llm import FakeLLM


@pytest.fixture(autouse=True)
def _db():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def _walkthrough_llm() -> FakeLLM:
    llm = FakeLLM()
    llm.on("Verdict", lambda m, s: Verdict(level=3, justification="ok"))
    llm.on("ReqAnalystOutput", lambda m, s: ReqAnalystOutput(
        reply="captured",
        requirements=[ReqDraft(statement="Customers submit searchable feedback with a status",
                               req_type="functional")]))
    llm.on("PRDAuthorOutput", lambda m, s: PRDAuthorOutput(
        reply="drafted",
        items=[PRDDraft(title="Feedback submission + triage",
                        acceptance_criteria=["status transitions new->in_progress->resolved"],
                        priority="must", linked_requirements=["REQ-1"])]))
    llm.on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="proposing",
        adrs=[ADRDraft(decision="Primary datastore", category="datastore", chosen="PostgreSQL",
                       rationale="Adopt ring; EU-pinned; satisfies residency + audit",
                       satisfies=["PRD-1", "COMP-1", "COMP-2", "COMP-3", "COMP-4"],
                       radar_refs=["PostgreSQL"])]))
    llm.on("ArchitectOutput", lambda m, s: ArchitectOutput(
        reply="spec",
        components=[SpecDraft(name="FeedbackService", responsibility="CRUD + triage",
                             interfaces=["POST /feedback", "GET /feedback"],
                             linked_prd=["PRD-1"], tech_refs=["ADR-1"])]))
    llm.on("PlannerOutput", lambda m, s: PlannerOutput(
        reply="planned",
        tasks=[TaskDraft(title="Build feedback API", epic="Feedback", estimate="3d",
                         linked_spec=["SPEC-1"])]))
    return llm


@pytest.fixture
def client():
    deps.LLM_FACTORY = lambda: _walkthrough_llm()
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    deps.LLM_FACTORY = __import__("app.llm", fromlist=["get_llm"]).get_llm


def test_full_walkthrough_reaches_task_plan_with_traceability(client):
    resp = client.post("/projects", json={"name": "Feedback", "profile_id": "eu-fintech"})
    pid = resp.json()["id"]
    plan = [
        (1, "business_user", "customers send feedback, team triages it"),
        (2, "business_user", "draft the PRD"),
        (3, "tech_architect", "propose the stack"),
        (4, "tech_architect", "write the spec"),
        (5, "tech_architect", "break into tasks"),
    ]
    for stage, persona, msg in plan:
        turn = client.post(f"/projects/{pid}/message",
                           json={"message": msg, "persona": persona}).json()
        assert "scorecard" in turn
        adv = client.post(f"/projects/{pid}/advance").json()
        assert adv["advanced"] is True, (
            f"stage {stage} gate did not pass: {turn['scorecard']['blockers']}"
        )

    proj = client.get(f"/projects/{pid}").json()
    assert proj["gate_status"]["5"] == "passed"

    # Traceability invariant (design §3): every downstream node cites upstream.
    graph = client.get(f"/projects/{pid}/graph").json()
    by_type: dict[str, list[dict]] = {}
    for n in graph["nodes"]:
        by_type.setdefault(n["doc_type"], []).append(n)

    assert all(n["linked_requirements"] for n in by_type["prd_item"])
    assert all(any(s.startswith("PRD-") for s in n["satisfies"]) for n in by_type["adr"])
    assert all(n["linked_prd"] and n["tech_refs"] for n in by_type["spec_component"])
    assert all(n["linked_spec"] for n in by_type["task"])


def _firebase_stack_llm() -> FakeLLM:
    llm = FakeLLM()
    llm.on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="realtime via firebase",
        adrs=[ADRDraft(decision="Realtime notifications", category="realtime",
                       chosen="Firebase Realtime DB", satisfies=["PRD-1"])]))
    return llm


def test_profile_swap_same_request_diverges():
    """Same Firebase request: blocked under eu-fintech, accepted under startup-web."""
    from app.db.session import session_scope

    def run(profile_id: str):
        with session_scope() as s:
            p = create_project(s, "swap", profile_id=profile_id)
            repo = GraphRepository(s, p.id)
            repo.upsert(PRDItem(title="instant notifications"))
            retr = ProfileRetriever(load_profile(profile_id))
            ctx = AgentContext(repo=repo, message="add realtime via Firebase",
                               persona=Persona.TECH_ARCHITECT, retriever=retr)
            return StackAdvisor(_firebase_stack_llm()).handle(ctx)

    eu = run("eu-fintech")
    startup = run("startup-web")

    # eu-fintech: Firebase is Hold -> blocked + escalated, nothing written
    assert eu.written_ids == []
    assert eu.escalation and eu.escalation["type"] == "radar_conflict"

    # startup-web: Firebase is Adopt -> ADR written, no escalation
    assert startup.written_ids != []
    assert startup.escalation is None


def test_gate_relock_blocks_advance_until_reconciled():
    """§13.5 acceptance (end-to-end through the API): a stale node holds a stage's
    gate shut even when the rubric passes, and reconciling it reopens the gate. This
    exercises the reconciliation cascade built across P05/P07/P09."""
    from app.db.session import session_scope
    from app.graph import GraphRepository, create_project
    from app.llm import get_llm
    from app.main import create_app
    from app.orchestrator import new_state, save_state
    from app.schemas import ADR, EdgeType, GateStatus, SpecComponent

    llm = FakeLLM()
    llm.on("Verdict", lambda m, s: Verdict(level=3, status="valid", justification="ok"))
    deps.LLM_FACTORY = lambda: llm
    try:
        with session_scope() as s:
            p = create_project(s, "acc", profile_id="eu-fintech")
            pid = p.id
            repo = GraphRepository(s, p.id)
            prd = repo.upsert(PRDItem(title="store data"))
            adr = repo.upsert(ADR(decision="datastore", chosen="PostgreSQL", satisfies=[prd.id]))
            spec = repo.upsert(
                SpecComponent(name="DataSvc", linked_prd=[prd.id], tech_refs=[adr.id]))
            repo.link(spec.id, prd.id, EdgeType.REALIZES)
            repo.link(spec.id, adr.id, EdgeType.DEPENDS_ON)
            repo.set_stale(spec.id, True)  # an unreconciled impact flag in stage 4
            state = new_state(pid)
            state.current_stage = 4
            for stg in (1, 2, 3):
                state.gate_status[stg] = GateStatus.PASSED
            save_state(s, state)
            spec_id = spec.id

        with TestClient(create_app()) as c:
            blocked = c.post(f"/projects/{pid}/advance").json()
            assert blocked["scorecard"]["gate_passed"] is True  # rubric is satisfied
            assert blocked["advanced"] is False  # but the stale node holds the gate
            assert spec_id in blocked["blocked_by_stale"]

            # reconcile (dismiss with a reason) and the gate reopens
            c.post(f"/projects/{pid}/impact/dismiss",
                   json={"node_id": spec_id, "reason": "accepted risk"})
            advanced = c.post(f"/projects/{pid}/advance").json()
            assert advanced["advanced"] is True and advanced["new_stage"] == 5
    finally:
        deps.LLM_FACTORY = get_llm
