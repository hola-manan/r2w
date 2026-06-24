"""Agent protocol (P05). Agents (P06) implement this; the Conductor routes to it."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field

from app.graph import GraphRepository
from app.profile import ProfileRetriever
from app.schemas import DocumentType, Persona


class AgentResult(BaseModel):
    reply: str = ""
    written_ids: list[str] = Field(default_factory=list)
    escalation: Optional[dict] = None  # Stack Advisor conflict, etc.


@dataclass
class AgentContext:
    repo: GraphRepository
    message: str
    persona: Persona
    project_brief: str = ""
    retriever: Optional[ProfileRetriever] = None
    history: list = field(default_factory=list)


@runtime_checkable
class Agent(Protocol):
    name: str
    writes: DocumentType

    def handle(self, ctx: AgentContext) -> AgentResult: ...
