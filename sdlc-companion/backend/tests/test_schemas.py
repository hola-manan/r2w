"""P01 verification: schema round-trips, enums, ID conventions, app boot."""
from __future__ import annotations

from app.schemas import (
    ADR,
    ARTIFACT_MODELS,
    DocumentType,
    EdgeType,
    PRDItem,
    Requirement,
    SpecComponent,
    Task,
    format_id,
    prefix_for,
)


def test_id_prefixes():
    assert format_id(DocumentType.REQUIREMENT, 1) == "REQ-1"
    assert format_id(DocumentType.PRD_ITEM, 2) == "PRD-2"
    assert format_id(DocumentType.ADR, 3) == "ADR-3"
    assert format_id(DocumentType.SPEC_COMPONENT, 4) == "SPEC-4"
    assert format_id(DocumentType.TASK, 5) == "TASK-5"


def test_edge_types_match_design():
    names = {e.value for e in EdgeType}
    # The five design edges (§13.4) plus depends_on (SpecComponent -> ADR), which the
    # Impact Analyzer needs so an ADR change ripples to dependent spec components.
    assert names == {
        "derives_from", "satisfies", "realizes", "constrains", "implements", "depends_on",
    }


def test_artifact_registry_complete():
    assert set(ARTIFACT_MODELS) == set(DocumentType)
    for doc_type, _model in ARTIFACT_MODELS.items():
        assert prefix_for(doc_type)


def test_each_artifact_round_trips():
    samples = [
        Requirement(id="REQ-1", project_id="P1", statement="Users can export data"),
        PRDItem(id="PRD-1", project_id="P1", title="Export", linked_requirements=["REQ-1"]),
        ADR(id="ADR-1", project_id="P1", decision="Use Postgres", chosen="Postgres",
            satisfies=["PRD-1"], radar_refs=["postgres"]),
        SpecComponent(id="SPEC-1", project_id="P1", name="ExportService",
                      linked_prd=["PRD-1"], tech_refs=["ADR-1"]),
        Task(id="TASK-1", project_id="P1", title="Build export endpoint",
             linked_spec=["SPEC-1"]),
    ]
    for obj in samples:
        model = type(obj)
        rebuilt = model.model_validate(obj.model_dump())
        assert rebuilt == obj
        assert rebuilt.doc_type == obj.doc_type


def test_envelope_defaults():
    req = Requirement(project_id="P1", statement="x")
    assert req.version == 1
    assert req.stale is False
    assert req.id == ""  # repository assigns on insert


def test_app_boots():
    from app.main import app

    routes = {getattr(r, "path", None) for r in app.routes}
    assert "/health" in routes
