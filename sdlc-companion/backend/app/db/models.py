"""ORM models (P02).

The Artifact Graph: nodes (the five document types), typed edges between them,
an append-only version log, plus project scoping and per-type ID counters.
Payload is the authoritative JSON of the Pydantic artifact; the scalar columns
(version, stale, last_changed, ...) are denormalized copies kept in sync on
write so they can be queried/indexed cheaply.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ProjectRow(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    profile_id: Mapped[str] = mapped_column(String, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    # Orchestrator state (P05) stored as JSON; null until set.
    state: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class CounterRow(Base):
    """Per-project, per-doc-type sequence for human-legible IDs (REQ-1, REQ-2...)."""

    __tablename__ = "counters"

    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_type: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[int] = mapped_column(Integer, default=0)


class NodeRow(Base):
    __tablename__ = "nodes"

    # Composite PK: node IDs (REQ-1, ...) are unique only within a project.
    project_id: Mapped[str] = mapped_column(String, primary_key=True)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[str] = mapped_column(String, index=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by_agent: Mapped[str | None] = mapped_column(String, nullable=True)
    last_changed: Mapped[datetime] = mapped_column(DateTime, default=_now)
    stale: Mapped[bool] = mapped_column(default=False)


class EdgeRow(Base):
    __tablename__ = "edges"
    __table_args__ = (
        # Node IDs (REQ-1, ...) are unique only within a project, so the same
        # (from, to, edge) triple legitimately recurs across projects.
        UniqueConstraint("project_id", "from_id", "to_id", "edge_type", name="uq_edge"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    from_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    to_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    edge_type: Mapped[str] = mapped_column(String, nullable=False)


class NodeVersionRow(Base):
    __tablename__ = "node_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    node_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    agent: Mapped[str | None] = mapped_column(String, nullable=True)
