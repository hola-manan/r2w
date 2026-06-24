"""GraphRepository (P02 contract).

The single way to read/write the Artifact Graph. Consumed by engines (P04),
the orchestrator (P05), and agents (P06). No LLM calls here.

A repository instance is scoped to one project (node IDs like REQ-1 are unique
only within a project). Project lifecycle uses the module-level helpers.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    CounterRow,
    EdgeRow,
    NodeRow,
    NodeVersionRow,
    ProjectRow,
)
from app.graph.mapping import payload_of, to_model
from app.schemas import DocumentType, EdgeType, Envelope, format_id


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ----- project lifecycle (not project-scoped) -----------------------------
def create_project(session: Session, name: str, profile_id: str = "") -> ProjectRow:
    row = ProjectRow(id=uuid.uuid4().hex[:12], name=name, profile_id=profile_id)
    session.add(row)
    session.flush()
    return row


def get_project(session: Session, project_id: str) -> ProjectRow | None:
    return session.get(ProjectRow, project_id)


def list_projects(session: Session) -> list[ProjectRow]:
    return list(session.scalars(select(ProjectRow)))


class GraphRepository:
    def __init__(self, session: Session, project_id: str) -> None:
        self.s = session
        self.project_id = project_id

    # ----- id allocation --------------------------------------------------
    def _next_seq(self, doc_type: DocumentType) -> int:
        counter = self.s.get(
            CounterRow, {"project_id": self.project_id, "doc_type": doc_type.value}
        )
        if counter is None:
            counter = CounterRow(
                project_id=self.project_id, doc_type=doc_type.value, value=0
            )
            self.s.add(counter)
        counter.value += 1
        self.s.flush()
        return counter.value

    def _row(self, node_id: str) -> NodeRow | None:
        return self.s.get(NodeRow, {"project_id": self.project_id, "id": node_id})

    # ----- nodes ----------------------------------------------------------
    def upsert(self, node: Envelope, *, agent: str | None = None) -> Envelope:
        """Insert (when id is empty) or update an existing node.

        Updates bump the version and append a NodeVersionRow snapshot.
        """
        node.project_id = self.project_id
        if not node.id:
            seq = self._next_seq(node.doc_type)
            node.id = format_id(node.doc_type, seq)
            node.version = 1
            if agent and not node.created_by_agent:
                node.created_by_agent = agent
            node.last_changed = _now()
            row = NodeRow(
                project_id=self.project_id,
                id=node.id,
                type=node.doc_type.value,
                payload=payload_of(node),
                version=node.version,
                created_by_agent=node.created_by_agent,
                last_changed=node.last_changed,
                stale=node.stale,
            )
            self.s.add(row)
        else:
            row = self._row(node.id)
            if row is None:
                raise KeyError(f"node {node.id} not found")
            node.version = row.version + 1
            node.last_changed = _now()
            row.version = node.version
            row.last_changed = node.last_changed
            row.stale = node.stale
            if agent:
                row.created_by_agent = row.created_by_agent or agent
            node.created_by_agent = row.created_by_agent
            row.payload = payload_of(node)

        self.s.add(
            NodeVersionRow(
                project_id=self.project_id,
                node_id=node.id,
                version=node.version,
                payload=payload_of(node),
                changed_at=node.last_changed,
                agent=agent,
            )
        )
        self.s.flush()
        return node

    def get(self, node_id: str) -> Envelope:
        row = self._row(node_id)
        if row is None:
            raise KeyError(f"node {node_id} not found")
        return to_model(row)

    def get_optional(self, node_id: str) -> Envelope | None:
        row = self._row(node_id)
        return to_model(row) if row else None

    def list_by_type(self, doc_type: DocumentType) -> list[Envelope]:
        rows = self.s.scalars(
            select(NodeRow)
            .where(NodeRow.project_id == self.project_id, NodeRow.type == doc_type.value)
            .order_by(NodeRow.id)
        )
        return [to_model(r) for r in rows]

    def list_all(self) -> list[Envelope]:
        rows = self.s.scalars(
            select(NodeRow)
            .where(NodeRow.project_id == self.project_id)
            .order_by(NodeRow.id)
        )
        return [to_model(r) for r in rows]

    def set_stale(self, node_id: str, value: bool) -> None:
        row = self._row(node_id)
        if row is None:
            raise KeyError(f"node {node_id} not found")
        row.stale = value
        payload = dict(row.payload)
        payload["stale"] = value
        row.payload = payload
        self.s.flush()

    def versions(self, node_id: str) -> list[NodeVersionRow]:
        return list(
            self.s.scalars(
                select(NodeVersionRow)
                .where(
                    NodeVersionRow.project_id == self.project_id,
                    NodeVersionRow.node_id == node_id,
                )
                .order_by(NodeVersionRow.version)
            )
        )

    # ----- edges ----------------------------------------------------------
    def link(self, from_id: str, to_id: str, edge: EdgeType) -> None:
        existing = self.s.scalar(
            select(EdgeRow).where(
                EdgeRow.project_id == self.project_id,
                EdgeRow.from_id == from_id,
                EdgeRow.to_id == to_id,
                EdgeRow.edge_type == edge.value,
            )
        )
        if existing:
            return
        self.s.add(
            EdgeRow(
                project_id=self.project_id,
                from_id=from_id,
                to_id=to_id,
                edge_type=edge.value,
            )
        )
        self.s.flush()

    def unlink(self, from_id: str, to_id: str, edge: EdgeType) -> None:
        row = self.s.scalar(
            select(EdgeRow).where(
                EdgeRow.project_id == self.project_id,
                EdgeRow.from_id == from_id,
                EdgeRow.to_id == to_id,
                EdgeRow.edge_type == edge.value,
            )
        )
        if row:
            self.s.delete(row)
            self.s.flush()

    def edges(self) -> list[EdgeRow]:
        return list(
            self.s.scalars(
                select(EdgeRow).where(EdgeRow.project_id == self.project_id)
            )
        )

    def adjacent(
        self,
        node_id: str,
        *,
        direction: str = "both",
        edges: list[EdgeType] | None = None,
    ) -> list[tuple[str, EdgeType]]:
        """Return (neighbor_id, edge_type) pairs. direction in {out, in, both}."""
        edge_vals = [e.value for e in edges] if edges else None
        result: list[tuple[str, EdgeType]] = []
        if direction in ("out", "both"):
            q = select(EdgeRow).where(
                EdgeRow.project_id == self.project_id, EdgeRow.from_id == node_id
            )
            if edge_vals:
                q = q.where(EdgeRow.edge_type.in_(edge_vals))
            for e in self.s.scalars(q):
                result.append((e.to_id, EdgeType(e.edge_type)))
        if direction in ("in", "both"):
            q = select(EdgeRow).where(
                EdgeRow.project_id == self.project_id, EdgeRow.to_id == node_id
            )
            if edge_vals:
                q = q.where(EdgeRow.edge_type.in_(edge_vals))
            for e in self.s.scalars(q):
                result.append((e.from_id, EdgeType(e.edge_type)))
        return result

    def neighbors(
        self,
        node_id: str,
        *,
        direction: str = "both",
        edges: list[EdgeType] | None = None,
    ) -> list[Envelope]:
        seen: dict[str, Envelope] = {}
        for neighbor_id, _edge in self.adjacent(
            node_id, direction=direction, edges=edges
        ):
            if neighbor_id not in seen:
                node = self.get_optional(neighbor_id)
                if node is not None:
                    seen[neighbor_id] = node
        return list(seen.values())
