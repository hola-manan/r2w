"""Agent registry (P06). build_agents() returns the stage -> agent mapping."""
from __future__ import annotations

from app.agents.architect import Architect
from app.agents.planner import Planner
from app.agents.prd_author import PRDAuthor
from app.agents.requirements_analyst import RequirementsAnalyst
from app.agents.stack_advisor import StackAdvisor
from app.llm import LLMClient


def build_agents(llm: LLMClient) -> dict[int, object]:
    return {
        1: RequirementsAnalyst(llm),
        2: PRDAuthor(llm),
        3: StackAdvisor(llm),
        4: Architect(llm),
        5: Planner(llm),
    }


__all__ = [
    "RequirementsAnalyst",
    "PRDAuthor",
    "StackAdvisor",
    "Architect",
    "Planner",
    "build_agents",
]
