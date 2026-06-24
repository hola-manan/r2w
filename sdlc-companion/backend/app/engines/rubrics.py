"""Rubric registry (P04 contract) — data, not prompts.

Per-stage hard + soft dimensions with anchored 0-3 descriptors. Dimensions
with a `deterministic` key are scored by a structural checker (no LLM); the
rest are scored by the ConsistencyChecker. Agents (P06) reference the SAME
registry so the gate and the agents optimize the same thing.

Design doc §13.2.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Dimension:
    key: str
    name: str
    question: str
    anchors: dict[int, str]
    deterministic: Optional[str] = None  # name of a structural checker, or None -> LLM


@dataclass(frozen=True)
class Rubric:
    stage: int
    hard: list[Dimension]
    soft: list[tuple[Dimension, float]]
    threshold: float = 0.6

    def iter_dims(self):
        for d in self.hard:
            yield d, "hard"
        for d, _w in self.soft:
            yield d, "soft"

    def weight_of(self, key: str) -> float:
        for d, w in self.soft:
            if d.key == key:
                return w
        return 0.0


def _anchors(l0: str, l1: str, l2: str, l3: str) -> dict[int, str]:
    return {0: l0, 1: l1, 2: l2, 3: l3}


# ---- Stage 1: Requirements ------------------------------------------------
_clarity = Dimension(
    "clarity", "Clarity",
    "Is the language unambiguous, with defined entities?",
    _anchors("nothing is defined", "some terms defined",
             "most defined, a few vague", "all entities/terms unambiguous"),
)
_testability = Dimension(
    "testability", "Testability",
    "Is each requirement independently verifiable?",
    _anchors("no requirement is verifiable", "some are",
             "most are, a few vague", "every requirement has a checkable condition"),
)
_scope = Dimension(
    "scope_boundedness", "Scope boundedness",
    "Is in-scope vs out-of-scope explicit?",
    _anchors("no scope stated", "vague scope",
             "scope mostly clear", "in/out of scope explicit"),
)
_completeness = Dimension(
    "completeness", "Completeness",
    "Are personas, primary flows, and edge cases present?",
    _anchors("none", "few", "most", "personas + flows + edge cases present"),
)
_feasibility = Dimension(
    "feasibility", "Feasibility",
    "Is it implementable within the Company Profile?",
    _anchors("clearly infeasible", "doubtful", "mostly feasible", "feasible within profile"),
)
_nfr = Dimension(
    "nfr_coverage", "NFR coverage",
    "Are performance / security / compliance needs stated?",
    _anchors("none", "few", "most", "perf/security/compliance all stated"),
)
_metrics = Dimension(
    "success_metrics", "Success-metric measurability",
    "Are success metrics stated and measurable?",
    _anchors("none", "vague", "some measurable", "clear measurable success metrics"),
)

# ---- Stage 2: PRD ---------------------------------------------------------
_traceability = Dimension(
    "traceability", "Traceability",
    "Does every PRD item link to >=1 requirement, and is every requirement covered?",
    _anchors("no links", "few links", "most linked", "full two-way traceability"),
    deterministic="traceability",
)
_accept_quality = Dimension(
    "acceptance_quality", "Acceptance-criteria quality",
    "Are acceptance criteria concrete and testable?",
    _anchors("none", "weak", "mostly good", "all concrete & testable"),
)
_prioritization = Dimension(
    "prioritization", "Prioritization sanity",
    "Are priorities present and sensible?",
    _anchors("none", "arbitrary", "mostly sensible", "clear sensible priorities"),
)
_noncontradiction = Dimension(
    "non_contradiction", "Internal non-contradiction",
    "Are the PRD items free of internal contradictions?",
    _anchors("many conflicts", "some", "minor", "no contradictions"),
)

# ---- Stage 3: Stack / ADR -------------------------------------------------
_radar_compliance = Dimension(
    "radar_compliance", "Radar-compliance",
    "Are all chosen technologies on the radar (no Hold)?",
    _anchors("none on radar", "some off-radar/Hold", "one off-radar/Hold", "all on radar, no Hold"),
    deterministic="radar_compliance",
)
_compliance_satisfaction = Dimension(
    "compliance_satisfaction", "Compliance-satisfaction",
    "Are all hard compliance constraints satisfied by ADRs?",
    _anchors("none satisfied", "few", "most", "all hard constraints satisfied"),
    deterministic="compliance_satisfaction",
)
_decision_coverage = Dimension(
    "decision_coverage", "Decision coverage",
    "Does every significant capability have a supporting decision?",
    _anchors("none", "few", "most", "every capability has a decision"),
)
_rationale = Dimension(
    "rationale_grounding", "Rationale grounding",
    "Do ADR rationales cite specific PRD/COMP/radar IDs?",
    _anchors("ungrounded", "weakly cited", "mostly cited", "all rationales cite IDs"),
)
_risk = Dimension(
    "risk_ack", "Risk acknowledgement",
    "Are risks (esp. for Trial tech) acknowledged?",
    _anchors("none", "few", "most", "risks acknowledged where relevant"),
)

# ---- Stage 4: Tech Spec ---------------------------------------------------
_component_coverage = Dimension(
    "component_coverage", "Component coverage",
    "Does every PRD item map to >=1 spec component?",
    _anchors("none", "few", "most", "every PRD item realized by a component"),
    deterministic="component_coverage",
)
_adr_alignment = Dimension(
    "adr_alignment", "ADR alignment",
    "Do components reference accepted ADRs (no dangling/superseded refs)?",
    _anchors("none aligned", "few", "most", "all tech_refs point to accepted ADRs"),
    deterministic="adr_alignment",
)
_interfaces = Dimension(
    "interface_completeness", "Interface completeness",
    "Are component interfaces specified?",
    _anchors("none", "few", "most", "all interfaces specified"),
)
_data_model = Dimension(
    "data_model_coverage", "Data-model coverage",
    "Is the data model covered for components that need it?",
    _anchors("none", "few", "most", "data model covered"),
)
_failure = Dimension(
    "failure_handling", "Failure/edge handling",
    "Are failure modes and edge cases handled?",
    _anchors("none", "few", "most", "failure/edge handling present"),
)
_nfr_realization = Dimension(
    "nfr_realization", "NFR realization",
    "Are NFRs from the PRD realized in the spec?",
    _anchors("none", "few", "most", "NFRs realized"),
)

# ---- Stage 5: Task plan ---------------------------------------------------
_decomposition = Dimension(
    "decomposition", "Decomposition completeness",
    "Does every spec component map to >=1 task?",
    _anchors("none", "few", "most", "every component has a task"),
    deterministic="decomposition",
)
_acyclicity = Dimension(
    "acyclicity", "Dependency acyclicity",
    "Is the task dependency graph acyclic?",
    _anchors("cyclic", "cyclic", "cyclic", "acyclic"),
    deterministic="acyclicity",
)
_estimates = Dimension(
    "estimate_presence", "Estimate presence",
    "Does every task carry an estimate?",
    _anchors("none", "few", "most", "every task estimated"),
    deterministic="estimate_presence",
)
_sizing = Dimension(
    "sizing_sanity", "Sizing sanity",
    "Are task sizes reasonable (not too large)?",
    _anchors("all huge", "many huge", "mostly fine", "all reasonably sized"),
)
_critical_path = Dimension(
    "critical_path", "Critical-path identified",
    "Is the critical path/dependencies legible?",
    _anchors("unknown", "vague", "mostly clear", "critical path clear"),
)


STAGES: dict[int, Rubric] = {
    1: Rubric(
        stage=1,
        hard=[_clarity, _testability, _scope],
        soft=[(_completeness, 1.0), (_feasibility, 1.0), (_nfr, 1.0), (_metrics, 1.0)],
        threshold=0.6,
    ),
    2: Rubric(
        stage=2,
        hard=[_traceability],
        soft=[(_accept_quality, 1.0), (_prioritization, 0.5), (_noncontradiction, 1.0)],
        threshold=0.6,
    ),
    3: Rubric(
        stage=3,
        hard=[_radar_compliance, _compliance_satisfaction],
        soft=[(_decision_coverage, 1.0), (_rationale, 1.0), (_risk, 0.5)],
        threshold=0.6,
    ),
    4: Rubric(
        stage=4,
        hard=[_component_coverage, _adr_alignment],
        soft=[(_interfaces, 1.0), (_data_model, 1.0), (_failure, 0.75), (_nfr_realization, 0.75)],
        threshold=0.6,
    ),
    5: Rubric(
        stage=5,
        hard=[_decomposition, _acyclicity],
        soft=[(_estimates, 1.0), (_sizing, 0.5), (_critical_path, 0.5)],
        threshold=0.6,
    ),
}
