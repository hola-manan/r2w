"""P02 verification: CRUD, edges, traversal, versioning, stale, round-trip."""
from __future__ import annotations

import pytest

from app.db.base import Base
from app.db.session import get_engine, init_db, session_scope
from app.graph import GraphRepository, bfs, create_project
from app.schemas import (
    ADR,
    DocumentType,
    EdgeType,
    PRDItem,
    Requirement,
    SpecComponent,
    Task,
)


@pytest.fixture(autouse=True)
def _db():
    # Fresh schema per test (in-memory SQLite persists across the session).
    init_db()
    Base.metadata.drop_all(bind=get_engine())
    Base.metadata.create_all(bind=get_engine())


def _repo(s):
    p = create_project(s, "demo", profile_id="startup")
    return GraphRepository(s, p.id), p.id


def test_create_link_and_neighbors():
    with session_scope() as s:
        repo, _ = _repo(s)
        req = repo.upsert(Requirement(statement="export data"))
        prd = repo.upsert(PRDItem(title="Export"))
        assert req.id == "REQ-1"
        assert prd.id == "PRD-1"
        repo.link(prd.id, req.id, EdgeType.DERIVES_FROM)
        inbound = repo.neighbors(req.id, direction="in")
        assert [n.id for n in inbound] == ["PRD-1"]


def test_version_bump_and_snapshots():
    with session_scope() as s:
        repo, _ = _repo(s)
        req = repo.upsert(Requirement(statement="v1"))
        assert req.version == 1
        req.statement = "v2 clearer"
        req2 = repo.upsert(req)
        assert req2.version == 2
        snaps = repo.versions(req.id)
        assert [v.version for v in snaps] == [1, 2]


def test_set_stale_persists_in_column_and_payload():
    with session_scope() as s:
        repo, _ = _repo(s)
        adr = repo.upsert(ADR(decision="Use Postgres", chosen="Postgres"))
        repo.set_stale(adr.id, True)
        assert repo.get(adr.id).stale is True


def test_bfs_reaches_prd_and_adr_from_spec():
    with session_scope() as s:
        repo, _ = _repo(s)
        req = repo.upsert(Requirement(statement="r"))
        prd = repo.upsert(PRDItem(title="t"))
        adr = repo.upsert(ADR(decision="d", chosen="Postgres"))
        spec = repo.upsert(SpecComponent(name="svc"))
        repo.link(prd.id, req.id, EdgeType.DERIVES_FROM)
        repo.link(adr.id, prd.id, EdgeType.SATISFIES)
        repo.link(spec.id, prd.id, EdgeType.REALIZES)
        repo.link(spec.id, adr.id, EdgeType.REALIZES)

        result = bfs(repo, [spec.id], direction="out", max_depth=2)
        reached = set(result.nodes)
        assert prd.id in reached
        assert adr.id in reached


def test_round_trip_all_types():
    with session_scope() as s:
        repo, _ = _repo(s)
        nodes = [
            Requirement(statement="r"),
            PRDItem(title="t"),
            ADR(decision="d", chosen="Postgres"),
            SpecComponent(name="svc"),
            Task(title="task"),
        ]
        for n in nodes:
            saved = repo.upsert(n)
            reread = repo.get(saved.id)
            assert reread.doc_type == saved.doc_type
            assert reread.id == saved.id


def test_list_by_type_and_sequential_ids():
    with session_scope() as s:
        repo, _ = _repo(s)
        repo.upsert(Requirement(statement="a"))
        repo.upsert(Requirement(statement="b"))
        reqs = repo.list_by_type(DocumentType.REQUIREMENT)
        assert [r.id for r in reqs] == ["REQ-1", "REQ-2"]


def test_ids_are_unique_per_project_not_global():
    with session_scope() as s:
        p1 = create_project(s, "one")
        p2 = create_project(s, "two")
        r1 = GraphRepository(s, p1.id).upsert(Requirement(statement="a"))
        r2 = GraphRepository(s, p2.id).upsert(Requirement(statement="b"))
        # Same legible ID in two projects, no collision.
        assert r1.id == r2.id == "REQ-1"
