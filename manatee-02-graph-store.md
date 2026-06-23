# P02 — Artifact Graph Store

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`.

## Context
The five documents are projections of one graph (design §3). This plan persists nodes, typed edges, versions, and `stale` flags, and exposes a single repository interface that engines, the orchestrator, and agents all use — so there is exactly one way to read/write the graph.

## Depends on
P01 (schemas, enums, DB session).

## Produces (contract owned here)
`GraphRepository` — typed CRUD per artifact type, edge linking, neighbor traversal, version + stale operations. Consumed by P04, P05, P06.

## Scope / tasks
1. **ORM models** — `app/db/models.py`:
   - `NodeRow`: `id (pk), project_id, type (DocumentType), payload (JSON), version, created_by_agent, last_changed, stale`. Payload validated against the matching P01 schema on write.
   - `EdgeRow`: `id, project_id, from_id, to_id, edge_type (EdgeType)`. Indexed on `(from_id)` and `(to_id)`.
   - `NodeVersionRow`: append-only audit (`node_id, version, payload, changed_at, agent`).
2. **Repository** — `app/graph/repository.py`:
   ```python
   class GraphRepository:
       def upsert(self, node: Envelope) -> Envelope          # validate, bump version, snapshot
       def get(self, id: str) -> Envelope
       def list_by_type(self, project_id, type) -> list[Envelope]
       def link(self, from_id, to_id, edge: EdgeType) -> None
       def unlink(self, from_id, to_id, edge) -> None
       def neighbors(self, id, *, direction="both", edges=None) -> list[Envelope]
       def set_stale(self, id, value: bool) -> None
       def versions(self, id) -> list[NodeVersionRow]
   ```
   - `upsert` re-serializes to the correct Pydantic type, increments `version`, writes a `NodeVersionRow`, sets `last_changed`.
3. **Traversal** — `app/graph/traversal.py`: `bfs(repo, start_ids, *, direction, edge_filter, max_depth)` returning frontier nodes + the path edges (used by P04 Impact Analyzer).
4. **Project scoping** — every query filters by `project_id`; helper to create/list projects.
5. **ORM↔Pydantic mapping** — single `to_model` / `from_model` pair so payload typing is centralized.

## Key files
`backend/app/db/models.py`, `backend/app/graph/{repository,traversal}.py`, `backend/app/graph/mapping.py`.

## Verification (pytest)
- Create REQ, PRD; `link(PRD, REQ, derives_from)`; `neighbors(REQ, direction="in")` returns the PRD.
- `upsert` twice → `version` 1→2 and two `NodeVersionRow`s recorded.
- `set_stale` / clear toggles the flag and persists.
- `bfs` from a SPEC node reaches its PRD and ADR within depth 2; respects `edge_filter`.
- Round-trip each artifact type through `to_model`/`from_model`.

## Consistency notes
No LLM calls here — pure persistence + graph mechanics. Edge **meanings** (which checks run across them) belong to P04, not here; this plan only stores the typed edges.
