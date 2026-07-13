"""Readiness Engine (P04 contract). Forward gating via the shared checker.

Scores a stage's rubric (deterministic structural dims + LLM qualitative dims),
aggregates, and computes the gate: all hard == Green AND weighted soft >= threshold.
Design doc §13.1-13.3.
"""
from __future__ import annotations

import hashlib
from typing import Optional

from pydantic import BaseModel, Field

from app.engines.consistency_checker import ConsistencyChecker, Verdict
from app.engines.rendering import stage_context
from app.engines.rubrics import STAGES
from app.engines.structural import REGISTRY as STRUCTURAL
from app.graph import GraphRepository
from app.profile import ProfileRetriever

# level (0-3) -> RAG label for the UI
RAG = {0: "red", 1: "amber", 2: "amber", 3: "green"}

# Incremental scoring (manatee-04 §3): qualitative dimensions are scored by the LLM
# at temperature 0, so score_dimension(dim, context) is a pure function of (llm, input)
# and `context` is the complete input. We memoize the Verdict keyed on the exact input,
# so repeated scoring of an unchanged stage (e.g. the readiness poll endpoint) does not
# re-invoke the LLM. Any artifact change alters `context` -> new key -> miss. The key is
# scoped to the LLM instance: production's get_llm() is an lru_cached singleton (stable
# id, so the cache persists across requests), while distinct clients never share verdicts.
# PoC cache is unbounded (single operator); a bounded LRU is the production follow-up.
_VERDICT_CACHE: dict[tuple[int, str, int, str, str], Verdict] = {}


def clear_readiness_cache() -> None:
    _VERDICT_CACHE.clear()


class DimensionResult(BaseModel):
    key: str
    name: str
    kind: str  # hard | soft
    level: int
    rag: str
    evidence: list[str] = Field(default_factory=list)
    justification: str = ""
    followup_question: Optional[str] = None


class Scorecard(BaseModel):
    stage: int
    dimensions: list[DimensionResult]
    weighted_soft: float
    threshold: float
    gate_passed: bool
    blockers: list[str]  # names of hard dims not yet green
    followups: list[str]


class ReadinessEngine:
    def __init__(
        self,
        repo: GraphRepository,
        checker: ConsistencyChecker,
        retriever: ProfileRetriever | None = None,
    ) -> None:
        self.repo = repo
        self.checker = checker
        self.retriever = retriever

    def score(self, stage: int) -> Scorecard:
        rubric = STAGES[stage]
        profile_summary = self.retriever.summary() if self.retriever else ""
        context = stage_context(self.repo, stage, profile_summary)
        context_hash = hashlib.sha256(context.encode("utf-8")).hexdigest()

        results: list[DimensionResult] = []
        for dim, kind in rubric.iter_dims():
            if dim.deterministic:
                level, evidence, justification, followup = STRUCTURAL[dim.deterministic](
                    self.repo, self.retriever
                )
            else:
                verdict = self._score_dimension_cached(dim, context, stage, context_hash)
                level = verdict.level if verdict.level is not None else 0
                evidence = verdict.evidence
                justification = verdict.justification
                followup = verdict.followup_question
            results.append(
                DimensionResult(
                    key=dim.key,
                    name=dim.name,
                    kind=kind,
                    level=level,
                    rag=RAG[level],
                    evidence=evidence,
                    justification=justification,
                    followup_question=followup,
                )
            )

        by_key = {r.key: r for r in results}

        # weighted soft aggregate in [0,1]
        total_w = sum(w for _d, w in rubric.soft) or 1.0
        weighted = sum(w * (by_key[d.key].level / 3) for d, w in rubric.soft)
        weighted_soft = weighted / total_w

        hard_results = [r for r in results if r.kind == "hard"]
        # A hard dimension advances at amber (L2) or better; only red (L0-L1) blocks the gate.
        blockers = [r.name for r in hard_results if r.level < 2]
        gate_passed = (not blockers) and weighted_soft >= rubric.threshold

        followups = [r.followup_question for r in results if r.level < 3 and r.followup_question]

        return Scorecard(
            stage=stage,
            dimensions=results,
            weighted_soft=round(weighted_soft, 3),
            threshold=rubric.threshold,
            gate_passed=gate_passed,
            blockers=blockers,
            followups=followups,
        )

    def _score_dimension_cached(self, dim, context: str, stage: int, context_hash: str) -> Verdict:
        key = (id(self.checker.llm), self.repo.project_id, stage, dim.key, context_hash)
        cached = _VERDICT_CACHE.get(key)
        if cached is not None:
            return cached
        verdict = self.checker.score_dimension(dim, context)
        _VERDICT_CACHE[key] = verdict
        return verdict
