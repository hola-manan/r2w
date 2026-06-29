"""Batch artifact comments route: feedback -> owning agent revises in place."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agents.drafts import ReqAnalystOutput, ReqDraft
from app.api import deps
from app.db.base import Base
from app.db.session import get_engine, init_db
from app.engines import Verdict
from tests.fake_llm import FakeLLM


@pytest.fixture(autouse=True)
def _db():
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


@pytest.fixture
def client():
    llm = FakeLLM()
    llm.on("Verdict", lambda m, s: Verdict(level=3, status="valid", justification="ok"))
    llm.on("ReqAnalystOutput", lambda m, s: ReqAnalystOutput(
        reply="captured", requirements=[ReqDraft(statement="Users export CSV, < 5s")]))
    deps.LLM_FACTORY = lambda: llm
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    deps.LLM_FACTORY = __import__("app.llm", fromlist=["get_llm"]).get_llm


def _project_with_requirement(client) -> str:
    proj = client.post("/projects", json={"name": "Demo", "profile_id": "eu-fintech"}).json()
    pid = proj["id"]
    turn = client.post(f"/projects/{pid}/message",
                       json={"message": "users export data", "persona": "business_user"}).json()
    assert turn["written"][0]["id"] == "REQ-1"
    return pid


def test_comments_revise_artifact(client):
    pid = _project_with_requirement(client)
    # The agent revises REQ-1 in place to address the comment.
    deps.LLM_FACTORY().on("ReqAnalystOutput", lambda m, s: ReqAnalystOutput(
        reply="tightened REQ-1",
        requirements=[ReqDraft(id="REQ-1", statement="Users export CSV in under 5 seconds")]))
    res = client.post(f"/projects/{pid}/comments", json={
        "comments": [{"node_id": "REQ-1", "comment": "make the latency target explicit"}],
        "persona": "business_user",
    })
    assert res.status_code == 200, res.text
    turn = res.json()
    # TurnResponse shape
    assert {"reply", "written", "scorecard", "escalation", "impact", "needs_review"} <= turn.keys()
    assert turn["written"][0]["id"] == "REQ-1"
    assert "5 seconds" in turn["written"][0]["statement"]


def test_comments_empty_rejected(client):
    pid = _project_with_requirement(client)
    res = client.post(f"/projects/{pid}/comments",
                      json={"comments": [], "persona": "business_user"})
    assert res.status_code == 400


def test_comments_wrong_persona_conflicts(client):
    pid = _project_with_requirement(client)
    res = client.post(f"/projects/{pid}/comments", json={
        "comments": [{"node_id": "REQ-1", "comment": "x"}],
        "persona": "tech_architect",
    })
    assert res.status_code == 409
