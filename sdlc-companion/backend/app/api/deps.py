"""API dependencies (P07): assemble a Conductor for a project.

`LLM_FACTORY` is overridable in tests to inject a FakeLLM.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.agents import build_agents
from app.engines import ConsistencyChecker
from app.graph import GraphRepository, get_project
from app.llm import LLMClient, get_llm
from app.orchestrator import Conductor, ProjectState, load_state
from app.profile import ProfileRetriever, load_profile

# Overridable in tests.
LLM_FACTORY: Callable[[], LLMClient] = get_llm


@dataclass
class Assembled:
    conductor: Conductor
    state: ProjectState
    repo: GraphRepository
    retriever: ProfileRetriever | None
    profile_id: str


def build_conductor(session: Session, project_id: str) -> Assembled:
    row = get_project(session, project_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    repo = GraphRepository(session, project_id)
    retriever = ProfileRetriever(load_profile(row.profile_id)) if row.profile_id else None
    llm = LLM_FACTORY()
    checker = ConsistencyChecker(llm)
    agents = build_agents(llm)
    conductor = Conductor(repo, checker, agents, retriever)
    state = load_state(session, project_id)
    return Assembled(conductor, state, repo, retriever, row.profile_id)
