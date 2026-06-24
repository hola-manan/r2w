"""Deterministic structural rubric checkers (P04).

These score the graph-structural dimensions (traceability, radar-compliance,
acyclicity, ...) without an LLM, so gates are robust and reproducible. Each
returns (level 0-3, evidence ids, justification, followup|None).
"""
from __future__ import annotations

from typing import Optional

from app.graph import GraphRepository
from app.profile import ProfileRetriever, check_constraints, validate_choice
from app.schemas import DocumentType

CheckResult = tuple[int, list[str], str, Optional[str]]


def _ratio_level(good: int, total: int) -> int:
    if total == 0:
        return 0
    r = good / total
    if r >= 1.0:
        return 3
    if r >= 0.75:
        return 2
    if r > 0:
        return 1
    return 0


def _accepted_adrs(repo: GraphRepository):
    return [a for a in repo.list_by_type(DocumentType.ADR) if a.status == "accepted"]


def traceability(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    prds = repo.list_by_type(DocumentType.PRD_ITEM)
    reqs = repo.list_by_type(DocumentType.REQUIREMENT)
    if not prds:
        return 0, [], "No PRD items drafted yet.", "Draft PRD items linked to requirements."
    covered = {rid for p in prds for rid in p.linked_requirements}
    orphan_prds = [p.id for p in prds if not p.linked_requirements]
    uncovered = [r.id for r in reqs if r.id not in covered]
    problems = orphan_prds + uncovered
    good = (len(prds) - len(orphan_prds)) + (len(reqs) - len(uncovered))
    total = len(prds) + len(reqs)
    level = _ratio_level(good, total)
    if not problems:
        return 3, [], "Every PRD item links a requirement and every requirement is covered.", None
    fu = None
    if orphan_prds:
        fu = f"PRD items without a source requirement: {', '.join(orphan_prds)}."
    elif uncovered:
        fu = f"Requirements not yet covered by any PRD item: {', '.join(uncovered)}."
    return level, problems, "Traceability gaps found.", fu


def radar_compliance(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    adrs = _accepted_adrs(repo)
    if not adrs:
        return 0, [], "No accepted ADRs yet.", "Author ADRs choosing technologies from the radar."
    if retriever is None:
        return 0, [], "No profile loaded to validate against.", None
    violations = []
    for a in adrs:
        if not validate_choice(retriever, a.chosen).allowed:
            violations.append(a.id)
    level = _ratio_level(len(adrs) - len(violations), len(adrs))
    if not violations:
        return 3, [], "All chosen technologies are on the radar (no Hold).", None
    return level, violations, (
        f"ADRs choosing off-radar/Hold technologies: {', '.join(violations)}."
    ), "Re-select an Adopt/Trial technology from the radar for the flagged ADRs."


def compliance_satisfaction(
    repo: GraphRepository, retriever: ProfileRetriever | None
) -> CheckResult:
    adrs = _accepted_adrs(repo)
    if retriever is None:
        return 0, [], "No profile loaded.", None
    hard = retriever.hard_constraints()
    if not hard:
        return 3, [], "No hard compliance constraints to satisfy.", None
    if not adrs:
        return (0, [], "No accepted ADRs to satisfy constraints.",
                "Author ADRs that satisfy compliance constraints.")
    satisfied = {s for a in adrs for s in a.satisfies}
    uncovered = check_constraints(retriever, list(satisfied))
    level = _ratio_level(len(hard) - len(uncovered), len(hard))
    if not uncovered:
        return 3, [], "All hard compliance constraints are satisfied by ADRs.", None
    return level, uncovered, (
        f"Hard compliance constraints not satisfied by any ADR: {', '.join(uncovered)}."
    ), "Add or amend an ADR that satisfies the uncovered constraints."


def component_coverage(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    prds = repo.list_by_type(DocumentType.PRD_ITEM)
    specs = repo.list_by_type(DocumentType.SPEC_COMPONENT)
    if not specs:
        return 0, [], "No spec components yet.", "Add spec components that realize PRD items."
    realized = {pid for sc in specs for pid in sc.linked_prd}
    uncovered = [p.id for p in prds if p.id not in realized]
    level = _ratio_level(len(prds) - len(uncovered), len(prds)) if prds else 3
    if not uncovered:
        return 3, [], "Every PRD item is realized by at least one component.", None
    return level, uncovered, (
        f"PRD items not realized by any component: {', '.join(uncovered)}."
    ), "Add spec components realizing the uncovered PRD items."


def adr_alignment(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    specs = repo.list_by_type(DocumentType.SPEC_COMPONENT)
    if not specs:
        return 0, [], "No spec components yet.", None
    accepted = {a.id for a in _accepted_adrs(repo)}
    bad = []
    for sc in specs:
        if not sc.tech_refs or any(ref not in accepted for ref in sc.tech_refs):
            bad.append(sc.id)
    level = _ratio_level(len(specs) - len(bad), len(specs))
    if not bad:
        return 3, [], "All components reference accepted ADRs.", None
    return level, bad, (
        f"Components with missing/dangling ADR references: {', '.join(bad)}."
    ), "Point each component's tech_refs at an accepted ADR."


def decomposition(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    specs = repo.list_by_type(DocumentType.SPEC_COMPONENT)
    tasks = repo.list_by_type(DocumentType.TASK)
    if not tasks:
        return 0, [], "No tasks yet.", "Decompose components into tasks."
    implemented = {sid for t in tasks for sid in t.linked_spec}
    uncovered = [s.id for s in specs if s.id not in implemented]
    level = _ratio_level(len(specs) - len(uncovered), len(specs)) if specs else 3
    if not uncovered:
        return 3, [], "Every component is implemented by at least one task.", None
    return level, uncovered, (
        f"Components with no implementing task: {', '.join(uncovered)}."
    ), "Add tasks implementing the uncovered components."


def acyclicity(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    tasks = repo.list_by_type(DocumentType.TASK)
    graph = {t.id: list(t.depends_on) for t in tasks}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {tid: WHITE for tid in graph}
    cycle_node: list[str] = []

    def visit(n: str) -> bool:
        color[n] = GRAY
        for m in graph.get(n, []):
            if m not in color:
                continue
            if color[m] == GRAY:
                cycle_node.append(m)
                return True
            if color[m] == WHITE and visit(m):
                return True
        color[n] = BLACK
        return False

    for tid in graph:
        if color[tid] == WHITE and visit(tid):
            return 0, cycle_node, "Task dependency cycle detected.", "Break the dependency cycle."
    return 3, [], "Task dependency graph is acyclic.", None


def estimate_presence(repo: GraphRepository, retriever: ProfileRetriever | None) -> CheckResult:
    tasks = repo.list_by_type(DocumentType.TASK)
    if not tasks:
        return 0, [], "No tasks yet.", None
    missing = [t.id for t in tasks if not t.estimate]
    level = _ratio_level(len(tasks) - len(missing), len(tasks))
    if not missing:
        return 3, [], "Every task carries an estimate.", None
    return (level, missing, f"Tasks missing estimates: {', '.join(missing)}.",
            "Add estimates to the flagged tasks.")


REGISTRY = {
    "traceability": traceability,
    "radar_compliance": radar_compliance,
    "compliance_satisfaction": compliance_satisfaction,
    "component_coverage": component_coverage,
    "adr_alignment": adr_alignment,
    "decomposition": decomposition,
    "acyclicity": acyclicity,
    "estimate_presence": estimate_presence,
}
