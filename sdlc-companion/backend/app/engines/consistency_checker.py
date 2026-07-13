"""Graph Consistency Checker (P04 contract) — the one shared primitive.

Takes a node (rubric dimension scoring, forward) or a pair of linked nodes
(edge consistency, after a change) and returns a structured Verdict with
evidence. The Readiness Engine runs it forward/within a stage; the Impact
Analyzer runs it across edges after a change. Both go through `llm.structured`
at temperature 0 for stable, reproducible output.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.engines.rubrics import Dimension
from app.llm import LLMClient

SCORE_SYSTEM = (
    "You are a pragmatic software readiness reviewer. You score ONE rubric "
    "dimension at a time using a fixed anchored 0-3 scale, and cite the specific "
    "artifact IDs that justify your score. Award level 3 when the level-3 anchor is "
    "substantially met — minor, non-blocking nitpicks do not by themselves keep a "
    "dimension below level 3. Reserve levels 0-1 for genuine, material gaps."
)

EDGE_SYSTEM = (
    "You check whether two linked software artifacts are still consistent after "
    "a change. Return a status (valid | stale | contradicted | unsupported), a "
    "justification citing IDs, and a concrete suggested_patch when not valid."
)


class Verdict(BaseModel):
    status: Optional[Literal["valid", "stale", "contradicted", "unsupported"]] = None
    level: Optional[int] = Field(default=None, ge=0, le=3)
    evidence: list[str] = Field(default_factory=list)
    justification: str = ""
    followup_question: Optional[str] = None
    suggested_patch: Optional[dict] = None


class ConsistencyChecker:
    def __init__(self, llm: LLMClient) -> None:
        self.llm = llm

    def score_dimension(self, dimension: Dimension, context: str) -> Verdict:
        anchors = "\n".join(f"  L{lvl}: {txt}" for lvl, txt in sorted(dimension.anchors.items()))
        prompt = (
            f"Dimension: {dimension.name}\n"
            f"Question: {dimension.question}\n"
            f"Anchored scale:\n{anchors}\n\n"
            f"Artifacts under review:\n{context}\n\n"
            "Return: level (0-3), evidence (artifact IDs), justification, and "
            "(unless level 3) a single gap-closing followup_question."
        )
        return self.llm.structured(
            [{"role": "user", "content": prompt}],
            Verdict,
            system=SCORE_SYSTEM,
            temperature=0.0,
        )

    def check_edge(self, changed_text: str, neighbor_text: str, edge_meaning: str) -> Verdict:
        prompt = (
            f"Edge invariant: {edge_meaning}\n\n"
            f"CHANGED node:\n{changed_text}\n\n"
            f"NEIGHBOR node (may now be inconsistent):\n{neighbor_text}\n\n"
            "Decide the neighbor's status and, if not valid, a suggested_patch "
            "(a dict of fields to change). Cite IDs in justification."
        )
        return self.llm.structured(
            [{"role": "user", "content": prompt}],
            Verdict,
            system=EDGE_SYSTEM,
            temperature=0.0,
        )
