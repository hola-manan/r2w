"""P04 verification: gate logic, deterministic structural dims, impact analysis."""
from __future__ import annotations

import pytest

from app.db.base import Base
from app.db.session import get_engine, init_db, session_scope
from app.engines import ConsistencyChecker, ImpactAnalyzer, ReadinessEngine, Verdict
from app.graph import GraphRepository, create_project
from app.profile import ProfileRetriever, load_profile
from app.schemas import ADR, EdgeType, PRDItem, Requirement, SpecComponent, Task
from tests.fake_llm import FakeLLM


@pytest.fixture(autouse=True)
def _db():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def _repo(s):
    p = create_project(s, "demo", profile_id="eu-fintech")
    return GraphRepository(s, p.id)


def _all_green_llm():
    llm = FakeLLM()
    llm.on("Verdict", lambda msgs, schema: Verdict(level=3, justification="ok"))
    return llm


def test_stage1_gate_blocks_when_qualitative_low():
    """A vague requirement is held at the gate with a follow-up question."""
    llm = FakeLLM()

    def score(msgs, schema):
        text = msgs[0]["content"]
        # 'testability' dimension scores low and emits a follow-up
        if "Testability" in text:
            return Verdict(level=1, justification="REQ-1 has no measurable condition",
                           followup_question="How will we know export is 'fast enough'?")
        return Verdict(level=3, justification="ok")

    llm.on("Verdict", score)
    with session_scope() as s:
        repo = _repo(s)
        repo.upsert(Requirement(statement="make export fast"))
        engine = ReadinessEngine(repo, ConsistencyChecker(llm))
        card = engine.score(1)
        assert card.gate_passed is False
        assert "Testability" in card.blockers
        assert any("fast enough" in f for f in card.followups)


def test_stage1_gate_passes_when_all_green():
    with session_scope() as s:
        repo = _repo(s)
        repo.upsert(Requirement(statement="clear, testable, scoped requirement"))
        engine = ReadinessEngine(repo, ConsistencyChecker(_all_green_llm()))
        card = engine.score(1)
        assert card.gate_passed is True
        assert card.blockers == []


def test_stage2_traceability_is_deterministic_and_blocks():
    """Orphan PRD item (no requirement link) fails the hard traceability gate."""
    with session_scope() as s:
        repo = _repo(s)
        repo.upsert(Requirement(statement="r"))
        repo.upsert(PRDItem(title="orphan feature"))  # no linked_requirements
        engine = ReadinessEngine(repo, ConsistencyChecker(_all_green_llm()))
        card = engine.score(2)
        assert card.gate_passed is False
        trace = next(d for d in card.dimensions if d.key == "traceability")
        assert trace.level < 3
        assert "PRD-1" in trace.evidence


def test_stage3_constraint_test_blocks_hold_tech():
    """Constraint test: an ADR choosing a Hold tech fails radar-compliance."""
    retr = ProfileRetriever(load_profile("eu-fintech"))
    with session_scope() as s:
        repo = _repo(s)
        # MongoDB is Hold in eu-fintech
        repo.upsert(ADR(decision="Use MongoDB", chosen="MongoDB", satisfies=["COMP-1"]))
        engine = ReadinessEngine(repo, ConsistencyChecker(_all_green_llm()), retr)
        card = engine.score(3)
        radar = next(d for d in card.dimensions if d.key == "radar_compliance")
        assert radar.level < 3
        assert "ADR-1" in radar.evidence
        assert card.gate_passed is False


def test_stage5_acyclicity_detects_cycle():
    with session_scope() as s:
        repo = _repo(s)
        spec = repo.upsert(SpecComponent(name="svc"))
        t1 = repo.upsert(Task(title="a", estimate="1d", linked_spec=[spec.id]))
        t2 = repo.upsert(Task(title="b", estimate="1d", linked_spec=[spec.id], depends_on=[t1.id]))
        # introduce a cycle t1 -> t2 -> t1
        t1.depends_on = [t2.id]
        repo.upsert(t1)
        engine = ReadinessEngine(repo, ConsistencyChecker(_all_green_llm()))
        card = engine.score(5)
        acyc = next(d for d in card.dimensions if d.key == "acyclicity")
        assert acyc.level == 0


def test_impact_flags_downstream_after_change():
    """Impact test: changing an ADR flags the spec component that realizes via it."""
    llm = FakeLLM()

    def edge(msgs, schema):
        return Verdict(status="contradicted",
                       justification="SPEC-1 assumed the previous datastore",
                       evidence=["SPEC-1"],
                       suggested_patch={"responsibility": "update for new datastore"})

    llm.on("Verdict", edge)
    with session_scope() as s:
        repo = _repo(s)
        prd = repo.upsert(PRDItem(title="store data", linked_requirements=[]))
        adr = repo.upsert(ADR(decision="Use Postgres", chosen="PostgreSQL", satisfies=[prd.id]))
        spec = repo.upsert(SpecComponent(name="DataSvc", linked_prd=[prd.id], tech_refs=[adr.id]))
        repo.link(adr.id, prd.id, EdgeType.SATISFIES)
        repo.link(spec.id, adr.id, EdgeType.DEPENDS_ON)

        analyzer = ImpactAnalyzer(repo, ConsistencyChecker(llm))
        report = analyzer.analyze([adr.id])
        flagged = {i.node_id for i in report.items}
        assert spec.id in flagged
        assert repo.get(spec.id).stale is True


def test_impact_uses_depends_on_edge_meaning():
    """The component->ADR DEPENDS_ON edge has a registered invariant (no KeyError)."""
    from app.engines.edge_semantics import EDGE_MEANING

    assert EdgeType.DEPENDS_ON in EDGE_MEANING

    captured: dict[str, str] = {}

    def edge(msgs, schema):
        captured["prompt"] = msgs[0]["content"]
        return Verdict(status="stale", justification="ADR-1 changed", evidence=["SPEC-1"])

    llm = FakeLLM().on("Verdict", edge)
    with session_scope() as s:
        repo = _repo(s)
        adr = repo.upsert(ADR(decision="Use Postgres", chosen="PostgreSQL"))
        spec = repo.upsert(SpecComponent(name="DataSvc", tech_refs=[adr.id]))
        repo.link(spec.id, adr.id, EdgeType.DEPENDS_ON)

        report = ImpactAnalyzer(repo, ConsistencyChecker(llm)).analyze([adr.id])
        assert {i.node_id for i in report.items} == {spec.id}
        # the checker was handed the depends-on invariant, not the realizes one
        assert "depends on an ADR decision" in captured["prompt"]


def test_impact_no_false_positive_when_valid():
    llm = FakeLLM()
    llm.on("Verdict", lambda msgs, schema: Verdict(status="valid", justification="fine"))
    with session_scope() as s:
        repo = _repo(s)
        prd = repo.upsert(PRDItem(title="x"))
        adr = repo.upsert(ADR(decision="d", chosen="PostgreSQL", satisfies=[prd.id]))
        repo.link(adr.id, prd.id, EdgeType.SATISFIES)
        report = ImpactAnalyzer(repo, ConsistencyChecker(llm)).analyze([adr.id])
        assert report.has_impact is False
