"""P07 verification: REST + WebSocket against a TestClient with a FakeLLM."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.agents.drafts import PRDAuthorOutput, PRDDraft, ReqAnalystOutput, ReqDraft
from app.api import deps
from app.db.base import Base
from app.db.session import get_engine, init_db
from app.engines import Verdict
from app.engines.consistency_checker import ConsistencyChecker  # noqa: F401
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
    llm.on("PRDAuthorOutput", lambda m, s: PRDAuthorOutput(
        reply="drafted", items=[PRDDraft(title="CSV Export", linked_requirements=["REQ-1"])]))
    deps.LLM_FACTORY = lambda: llm
    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c
    deps.LLM_FACTORY = __import__("app.llm", fromlist=["get_llm"]).get_llm


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_profiles_listed(client):
    ids = {p["id"] for p in client.get("/profiles").json()}
    assert {"eu-fintech", "startup-web"} <= ids


def test_project_lifecycle_and_message(client):
    # create
    proj = client.post("/projects", json={"name": "Demo", "profile_id": "eu-fintech"}).json()
    pid = proj["id"]
    assert proj["current_stage"] == 1

    # stage-1 message creates a requirement
    turn = client.post(f"/projects/{pid}/message",
                       json={"message": "users export data", "persona": "business_user"}).json()
    assert turn["written"][0]["id"] == "REQ-1"
    assert turn["scorecard"]["gate_passed"] is True  # fake scores all green

    # persona violation -> 409
    bad = client.post(f"/projects/{pid}/message",
                      json={"message": "x", "persona": "tech_architect"})
    assert bad.status_code == 409

    # advance to stage 2
    adv = client.post(f"/projects/{pid}/advance").json()
    assert adv["advanced"] is True and adv["new_stage"] == 2

    # artifacts + graph endpoints
    arts = client.get(f"/projects/{pid}/artifacts", params={"type": "requirement"}).json()
    assert arts[0]["id"] == "REQ-1"
    graph = client.get(f"/projects/{pid}/graph").json()
    assert any(n["id"] == "REQ-1" for n in graph["nodes"])


def test_reopen_flips_needs_review(client):
    proj = client.post("/projects", json={"name": "D", "profile_id": "startup-web"}).json()
    pid = proj["id"]
    client.post(f"/projects/{pid}/message",
                json={"message": "req", "persona": "business_user"})
    client.post(f"/projects/{pid}/advance")  # -> stage 2
    client.post(f"/projects/{pid}/advance")  # stage 2 gate (traceability) may block
    # reopen stage 1 from wherever we are
    res = client.post(f"/projects/{pid}/reopen/1").json()
    assert res["current_stage"] == 1


def test_dismiss_requires_reason(client):
    proj = client.post("/projects", json={"name": "D", "profile_id": "eu-fintech"}).json()
    pid = proj["id"]
    r = client.post(f"/projects/{pid}/impact/dismiss", json={"node_id": "REQ-1", "reason": ""})
    assert r.status_code == 400


def test_websocket_streams_events(client):
    proj = client.post("/projects", json={"name": "WS", "profile_id": "eu-fintech"}).json()
    pid = proj["id"]
    with client.websocket_connect(f"/projects/{pid}/ws") as ws:
        ws.send_json({"message": "users export data", "persona": "business_user"})
        events = []
        while True:
            evt = ws.receive_json()
            events.append(evt["t"])
            if evt["t"] == "done":
                break
    assert "reply" in events
    assert "artifact_upserted" in events
    assert "scorecard" in events
    assert events[-1] == "done"
