"""Impact Analyzer (P04 contract). Omnidirectional consistency after a change.

BFS over typed edges from the changed node(s), run the consistency checker per
neighbor with edge semantics, emit a consistency_diff, and mark affected nodes
stale. Cascade control: only flagged neighbors propagate; depth-capped; nothing
auto-applies (human ack between passes). Design doc §13.4.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from app.engines.consistency_checker import ConsistencyChecker
from app.engines.edge_semantics import EDGE_MEANING
from app.engines.rendering import render_node
from app.graph import GraphRepository


class ImpactItem(BaseModel):
    node_id: str
    doc_type: str
    status: str  # stale | contradicted | unsupported
    justification: str = ""
    evidence: list[str] = Field(default_factory=list)
    suggested_patch: dict | None = None


class ImpactReport(BaseModel):
    changed: list[str]
    items: list[ImpactItem] = Field(default_factory=list)

    @property
    def has_impact(self) -> bool:
        return bool(self.items)


class ImpactAnalyzer:
    def __init__(self, repo: GraphRepository, checker: ConsistencyChecker) -> None:
        self.repo = repo
        self.checker = checker

    def analyze(self, changed_ids: list[str], *, max_depth: int = 3) -> ImpactReport:
        report = ImpactReport(changed=list(changed_ids))
        visited: set[str] = set(changed_ids)
        frontier: list[str] = list(changed_ids)
        depth = 0

        while frontier and depth < max_depth:
            next_frontier: list[str] = []
            for node_id in frontier:
                changed_node = self.repo.get_optional(node_id)
                if changed_node is None:
                    continue
                changed_text = render_node(changed_node)
                for neighbor_id, edge in self.repo.adjacent(node_id, direction="both"):
                    if neighbor_id in visited:
                        continue
                    neighbor = self.repo.get_optional(neighbor_id)
                    if neighbor is None:
                        continue
                    verdict = self.checker.check_edge(
                        changed_text, render_node(neighbor), EDGE_MEANING[edge]
                    )
                    if verdict.status and verdict.status != "valid":
                        self.repo.set_stale(neighbor_id, True)
                        report.items.append(
                            ImpactItem(
                                node_id=neighbor_id,
                                doc_type=neighbor.doc_type.value,
                                status=verdict.status,
                                justification=verdict.justification,
                                evidence=verdict.evidence,
                                suggested_patch=verdict.suggested_patch,
                            )
                        )
                        # only flagged (content-affected) neighbors propagate
                        visited.add(neighbor_id)
                        next_frontier.append(neighbor_id)
                    else:
                        visited.add(neighbor_id)
            frontier = next_frontier
            depth += 1

        return report
