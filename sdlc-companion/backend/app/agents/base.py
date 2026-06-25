"""Agent base (P06). Claude + role prompt (incl. rubric awareness) + cite discipline."""
from __future__ import annotations

from typing import Optional, TypeVar

from pydantic import BaseModel

from app.engines.rubrics import describe_rubric
from app.llm import LLMClient

T = TypeVar("T", bound=BaseModel)

CITE_DISCIPLINE = (
    "Always cite the upstream node IDs your output derives from (REQ-, PRD-, "
    "ADR-, SPEC-, COMP-). An artifact that derives from nothing is a defect."
)


class BaseAgent:
    name: str = "agent"
    stage: Optional[int] = None  # set by subclasses; drives rubric-awareness injection

    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def _system(self, role: str, brief: str = "") -> str:
        parts = [role, CITE_DISCIPLINE]
        if self.stage is not None:
            parts.append(describe_rubric(self.stage))
        if brief:
            parts.append("Project brief:\n" + brief)
        return "\n\n".join(parts)

    def _generate(self, schema: type[T], prompt: str, system: str) -> T:
        return self.llm.structured(
            [{"role": "user", "content": prompt}], schema, system=system, temperature=0.0
        )
