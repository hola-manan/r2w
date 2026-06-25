"""P06 verification: each agent writes its own type, citations, constraints, challenge."""
from __future__ import annotations

import pytest

from app.agents import Architect, Planner, PRDAuthor, RequirementsAnalyst, StackAdvisor
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
from app.db.base import Base
from app.db.session import get_engine, init_db, session_scope
from app.graph import GraphRepository, create_project
from app.orchestrator.types import AgentContext
from app.profile import ProfileRetriever, load_profile
from app.schemas import ADR, DocumentType, Persona, PRDItem, Requirement, SpecComponent
from tests.fake_llm import FakeLLM


@pytest.fixture(autouse=True)
def _db():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def _ctx(repo, message, retriever=None):
    return AgentContext(repo=repo, message=message, persona=Persona.BUSINESS_USER,
                        retriever=retriever)


def test_agents_inject_their_stage_rubric():
    """The single rubrics.py source feeds the agent prompt (no divergent rubric prose)."""
    from app.engines.rubrics import describe_rubric

    system = RequirementsAnalyst(FakeLLM())._system("role", brief="")
    assert "Clarity" in system and "Testability" in system
    assert describe_rubric(1) in system
    # The Planner (stage 5) gets the task-plan rubric instead.
    assert "Dependency acyclicity" in Planner(FakeLLM())._system("role")


def test_requirements_analyst_sets_source_turn():
    from app.orchestrator.state import Message

    llm = FakeLLM().on("ReqAnalystOutput", lambda m, s: ReqAnalystOutput(
        reply="ok", requirements=[ReqDraft(statement="Users export CSV")]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        ctx = AgentContext(
            repo=repo, message="export", persona=Persona.BUSINESS_USER,
            history=[Message(role="user", content="hi"), Message(role="agent", content="?"),
                     Message(role="user", content="export")],
        )
        res = RequirementsAnalyst(llm).handle(ctx)
        assert repo.get(res.written_ids[0]).source_turn == 2  # two user turns


def test_stack_advisor_grounds_radar_refs():
    retr = ProfileRetriever(load_profile("eu-fintech"))
    llm = FakeLLM().on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="ok", adrs=[ADRDraft(decision="datastore", chosen="PostgreSQL",
                                   satisfies=["PRD-1"],
                                   radar_refs=["Postgres", "MadeUpDB"])]))
    with session_scope() as s:
        p = create_project(s, "d", profile_id="eu-fintech")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="store data"))
        res = StackAdvisor(llm).handle(_ctx(repo, "pick a db", retr))
        adr = repo.get(res.written_ids[0])
        # bogus "MadeUpDB" dropped; canonical "PostgreSQL" present (chosen always cited).
        assert "MadeUpDB" not in adr.radar_refs
        assert "PostgreSQL" in adr.radar_refs


def test_requirements_analyst_writes_requirement():
    llm = FakeLLM().on("ReqAnalystOutput", lambda m, s: ReqAnalystOutput(
        reply="got it", requirements=[ReqDraft(statement="Users can export data as CSV")]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        res = RequirementsAnalyst(llm).handle(_ctx(repo, "export please"))
        assert res.written_ids == ["REQ-1"]
        assert repo.get("REQ-1").doc_type == DocumentType.REQUIREMENT


def test_prd_author_links_requirements():
    llm = FakeLLM().on("PRDAuthorOutput", lambda m, s: PRDAuthorOutput(
        reply="drafted", items=[PRDDraft(title="CSV export", linked_requirements=["REQ-1"])]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        repo.upsert(Requirement(statement="export"))
        res = PRDAuthor(llm).handle(_ctx(repo, "make a prd"))
        prd = repo.get(res.written_ids[0])
        assert prd.linked_requirements == ["REQ-1"]
        # derives_from edge created
        assert any(n.id == "PRD-1" for n in repo.neighbors("REQ-1", direction="in"))


def test_stack_advisor_blocks_hold_and_escalates():
    retr = ProfileRetriever(load_profile("eu-fintech"))
    llm = FakeLLM().on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="proposing", adrs=[ADRDraft(decision="datastore", chosen="MongoDB",
                                          satisfies=["PRD-1"])]))
    with session_scope() as s:
        p = create_project(s, "d", profile_id="eu-fintech")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="store data"))
        res = StackAdvisor(llm).handle(_ctx(repo, "pick a db", retr))
        assert res.written_ids == []  # Hold tech not written
        assert res.escalation and res.escalation["type"] == "radar_conflict"


def test_stack_advisor_writes_adopt_with_links():
    retr = ProfileRetriever(load_profile("eu-fintech"))
    llm = FakeLLM().on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="ok", adrs=[ADRDraft(decision="datastore", chosen="PostgreSQL",
                                   satisfies=["PRD-1", "COMP-1"], radar_refs=["PostgreSQL"])]))
    with session_scope() as s:
        p = create_project(s, "d", profile_id="eu-fintech")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="store data"))
        res = StackAdvisor(llm).handle(_ctx(repo, "pick a db", retr))
        adr = repo.get(res.written_ids[0])
        assert adr.chosen == "PostgreSQL"
        assert "PRD-1" in adr.satisfies
        # context falls back to satisfies when the model omits it (design §14.3 grounding)
        assert adr.context == ["PRD-1", "COMP-1"]


def test_stack_advisor_challenge_supersedes():
    retr = ProfileRetriever(load_profile("eu-fintech"))
    llm = FakeLLM().on("StackAdvisorOutput", lambda m, s: StackAdvisorOutput(
        reply="revised", adrs=[ADRDraft(decision="datastore", chosen="MySQL",
                                        satisfies=["PRD-1"])]))
    with session_scope() as s:
        p = create_project(s, "d", profile_id="eu-fintech")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="store data"))
        old = repo.upsert(ADR(decision="datastore", chosen="PostgreSQL", satisfies=["PRD-1"]))
        res = StackAdvisor(llm).challenge(_ctx(repo, "", retr), old.id, "prefer MySQL")
        assert old.id in res.written_ids
        assert repo.get(old.id).status == "superseded"
        assert repo.get(old.id).superseded_by is not None


def test_architect_proposes_adr_change_not_direct_write():
    from app.agents.drafts import AdrChangeDraft
    llm = FakeLLM().on("ArchitectOutput", lambda m, s: ArchitectOutput(
        reply="spec", components=[SpecDraft(name="Svc", linked_prd=["PRD-1"], tech_refs=["ADR-1"])],
        proposed_adr_changes=[AdrChangeDraft(target_id="ADR-1", change={"chosen": "Redis"},
                                             reason="cache")]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="x"))
        repo.upsert(ADR(decision="d", chosen="PostgreSQL"))
        res = Architect(llm).handle(_ctx(repo, "spec it"))
        assert repo.get(res.written_ids[0]).doc_type == DocumentType.SPEC_COMPONENT
        # ADR not directly modified; change is proposed
        assert repo.get("ADR-1").chosen == "PostgreSQL"
        assert res.escalation and res.escalation["proposed_adr_changes"]


def test_architect_links_specs_with_correct_edges():
    """tech_refs (component -> ADR) use DEPENDS_ON; linked_prd use REALIZES."""
    from app.schemas import EdgeType

    llm = FakeLLM().on("ArchitectOutput", lambda m, s: ArchitectOutput(
        reply="spec",
        components=[SpecDraft(name="Svc", linked_prd=["PRD-1"], tech_refs=["ADR-1"])]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        repo.upsert(PRDItem(title="x"))
        repo.upsert(ADR(decision="d", chosen="PostgreSQL"))
        res = Architect(llm).handle(_ctx(repo, "spec it"))
        spec_id = res.written_ids[0]
        edges = {(e.to_id, e.edge_type) for e in repo.edges() if e.from_id == spec_id}
        assert (spec_id and ("ADR-1", EdgeType.DEPENDS_ON.value) in edges)
        assert ("PRD-1", EdgeType.REALIZES.value) in edges


def test_planner_writes_tasks_with_links():
    llm = FakeLLM().on("PlannerOutput", lambda m, s: PlannerOutput(
        reply="planned",
        tasks=[TaskDraft(title="build svc", estimate="2d", linked_spec=["SPEC-1"])]))
    with session_scope() as s:
        p = create_project(s, "d")
        repo = GraphRepository(s, p.id)
        repo.upsert(SpecComponent(name="Svc"))
        res = Planner(llm).handle(_ctx(repo, "plan it"))
        task = repo.get(res.written_ids[0])
        assert task.linked_spec == ["SPEC-1"]
        assert task.estimate == "2d"
