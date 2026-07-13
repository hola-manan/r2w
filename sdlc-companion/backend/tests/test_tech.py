"""Tests for the self-contained team Tech Capability Catalog + task->tool matching.

Covers: catalog loading/parsing, the two integration seams (retriever fallback + the
stage-3 radar_compliance gate), matcher sorting/recommendation, and — importantly — the
best-effort degradation path that keeps the feature from touching existing flows.
"""
from __future__ import annotations

import pytest

from app.profile import ProfileRetriever, load_profile, validate_choice
from app.schemas import Ring
from app.tech import TechMatcher, catalog_entry, load_catalog, rank_tools
from app.tech.schema import TechMatch, TechMatchOutput
from tests.fake_llm import FakeLLM


# ---- catalog loading --------------------------------------------------------

def test_catalog_loads_three_tools_with_frontmatter():
    cat = load_catalog()
    assert set(cat.names()) == {"Alteryx", "UiPath", "Power Apps"}
    for cap in cat.all():
        assert cap.id and cap.name and cap.category and cap.summary and cap.body
    assert {c.category for c in cat.all()} == {"data_prep", "rpa", "low_code"}


def test_catalog_get_is_case_insensitive_on_id_and_name():
    cat = load_catalog()
    assert cat.get("uipath") is cat.get("UiPath")
    assert cat.get("Power Apps").id == "powerapps"
    assert cat.get("nonsuch") is None
    assert cat.get(None) is None


def test_catalog_entry_is_adopt_radar_entry_or_none():
    e = catalog_entry("UiPath")
    assert e is not None and e.ring == Ring.ADOPT and e.category == "rpa"
    assert e.notes  # the capability summary is carried as the radar note
    assert catalog_entry("PostgreSQL") is None  # not a catalog tool


# ---- Seam 1: retriever fallback + the stage-3 gate --------------------------

def test_retriever_lookup_falls_back_to_catalog():
    r = ProfileRetriever(load_profile("eu-fintech"))
    # profile radar entries still resolve as before
    assert r.lookup("PostgreSQL").ring == Ring.ADOPT
    # a catalog tool (absent from this profile's radar) now resolves as Adopt...
    uip = r.lookup("UiPath")
    assert uip is not None and uip.ring == Ring.ADOPT
    # ...and is therefore an allowed choice
    assert validate_choice(r, "UiPath").allowed is True
    # a genuinely unknown technology is still off-radar / blocked
    assert r.lookup("CobolScreenScraper 3000") is None
    assert validate_choice(r, "CobolScreenScraper 3000").allowed is False


@pytest.fixture
def _db():
    from app.db.base import Base
    from app.db.session import get_engine, init_db

    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())
    yield


def test_radar_compliance_gate_passes_for_catalog_tool(_db):
    """An ADR choosing a team catalog tool clears the deterministic stage-3 gate."""
    from app.db.session import session_scope
    from app.engines.structural import radar_compliance
    from app.graph import GraphRepository, create_project
    from app.schemas import ADR, PRDItem

    with session_scope() as s:
        p = create_project(s, "auto", profile_id="eu-fintech")
        repo = GraphRepository(s, p.id)
        prd = repo.upsert(PRDItem(title="automate invoice data entry into the legacy ERP"))
        repo.upsert(ADR(decision="Process automation", chosen="UiPath", satisfies=[prd.id]))

        r = ProfileRetriever(load_profile("eu-fintech"))
        level, violations, _just, _fu = radar_compliance(repo, r)
        assert level == 3 and violations == []


# ---- matcher + best-effort degradation --------------------------------------

def _match_handler(messages, schema):
    # Canned, deliberately unsorted, to exercise the engine's own sorting/recommendation.
    return TechMatchOutput(
        matches=[
            TechMatch(tool_id="alteryx", tool_name="Alteryx", score=40, rationale="light prep only"),
            TechMatch(tool_id="uipath", tool_name="UiPath", score=90,
                      rationale="drives the legacy UI with no API", recommended=True),
            TechMatch(tool_id="powerapps", tool_name="Power Apps", score=30,
                      rationale="no new app surface needed"),
        ]
    )


def test_matcher_sorts_desc_and_keeps_recommended():
    fake = FakeLLM().on("TechMatchOutput", _match_handler)
    out = TechMatcher(fake).match("automate data entry", load_catalog())
    assert [m.tool_name for m in out.matches] == ["UiPath", "Alteryx", "Power Apps"]
    assert out.matches[0].recommended is True


def test_rank_tools_renders_visible_and_prompt_blocks():
    fake = FakeLLM().on("TechMatchOutput", _match_handler)
    ranking = rank_tools(fake, "automate data entry")
    assert not ranking.is_empty()
    assert "UiPath" in ranking.reply_block and "90/100" in ranking.reply_block
    assert "recommended" in ranking.reply_block.lower()
    assert "UiPath [90]" in ranking.prompt_block


def test_rank_tools_degrades_to_empty_on_error():
    # No handler registered -> FakeLLM.structured raises -> best-effort empty ranking,
    # which renders/injects nothing so the advisor behaves exactly as before.
    ranking = rank_tools(FakeLLM(), "anything")
    assert ranking.is_empty()
    assert ranking.reply_block == "" and ranking.prompt_block == ""


def _no_fit_handler(messages, schema):
    # Non-automation task: low scores, nothing recommended.
    return TechMatchOutput(
        matches=[
            TechMatch(tool_id="alteryx", tool_name="Alteryx", score=15, rationale="not a data task"),
            TechMatch(tool_id="uipath", tool_name="UiPath", score=10, rationale="no UI automation"),
            TechMatch(tool_id="powerapps", tool_name="Power Apps", score=20, rationale="no app surface"),
        ]
    )


def test_rank_tools_suppresses_when_no_tool_fits():
    # When no team tool is a genuine fit, the ranking is suppressed entirely so unrelated
    # (non-automation) stack turns show nothing about the team tools.
    fake = FakeLLM().on("TechMatchOutput", _no_fit_handler)
    ranking = rank_tools(fake, "build a public marketing website")
    assert ranking.is_empty()
    assert ranking.reply_block == "" and ranking.prompt_block == ""
