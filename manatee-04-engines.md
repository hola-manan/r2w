# P04 — Shared Engines (Consistency Checker → Readiness + Impact)

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. This is the product's "legible intelligence" core (design §5, §13).

## Context
Readiness (forward gating) and Impact (omnidirectional consistency) are the **same primitive** viewed two ways: a reasoner over whether the Artifact Graph is consistent/complete. Build that primitive once; both engines call it. Rubrics are encoded as **data** so the gate and the agents optimize the same thing.

## Depends on
P02 (graph repo + traversal), P03 (profile, for feasibility/compliance dimensions), P01 (`structured` LLM helper).

## Produces (contracts owned here)
- `ConsistencyChecker.check(...)` primitive.
- **Rubric registry** (per-stage hard/soft dimensions + anchored descriptors + weights + thresholds).
- `ReadinessEngine.score(stage)` and `ImpactAnalyzer.analyze(changed)`.

## Scope / tasks
1. **Consistency Checker** — `app/engines/consistency_checker.py` (§13):
   ```python
   class Verdict(BaseModel):
       status: Literal["valid","stale","contradicted","unsupported"] | None
       level: int | None             # 0..3 for rubric scoring
       evidence: list[str]           # node ids / turn refs
       justification: str
       followup_question: str | None
       suggested_patch: dict | None
   def check(target, rubric_or_edge_semantics) -> Verdict   # via llm.structured, temperature=0
   ```
2. **Rubric registry** — `app/engines/rubrics.py` (§13.2), data not prompts:
   - Per stage: `hard: list[Dimension]`, `soft: list[(Dimension, weight)]`, `threshold`.
   - Each `Dimension`: name, question, **anchored L0–L3 descriptors** (e.g. testability L0 "no requirement verifiable" … L3 "every requirement has a checkable condition").
   - Stages per master/design §13.2: Requirements, PRD, Stack/ADR, Tech Spec, Task plan.
3. **Readiness Engine** — `app/engines/readiness.py` (§13.1–13.3):
   - `score(project, stage)` → per-dimension `Verdict`s (incremental: only re-score nodes changed since last run), aggregate, gate result `all(hard==L3) AND weighted_soft ≥ threshold`.
   - Collect `followup_question`s for non-green dimensions (drives the stage-1 chat finish line).
4. **Impact Analyzer** — `app/engines/impact.py` (§13.4):
   - `analyze(changed_node_ids)` → BFS via P02 traversal (both directions), run `check` per neighbor with edge semantics, build `consistency_diff` (list of `{node, verdict, suggested_patch}`), `set_stale` on non-valid.
   - **Cascade control:** only nodes whose content actually changed; batch diffs into one review; `max_depth` cap; no auto-apply (human ack between passes).
5. **Edge semantics map** — `app/engines/edge_semantics.py`: per `EdgeType`, the rule the checker enforces (e.g. `realizes`: SpecComponent must still cover its PRD item).

## Key files
`backend/app/engines/{consistency_checker,rubrics,readiness,impact,edge_semantics}.py`.

## Verification
- **Gate (paper/auto):** a deliberately vague requirement holds at the gate; the right follow-up question is emitted (§12).
- **Impact:** a stage-4 datastore swap flags the affected ADR + assuming PRD items + downstream spec, with suggested patches (§13.4 example).
- **Stability:** anchored scoring reproduces the same level across repeated low-temp runs on fixed input.
- **Cascade control:** unchanged neighbors are not re-scored; traversal respects `max_depth`; nothing auto-applies.

## Consistency notes
Rubric/impact reasoning exists **only** here. Agents (P06) reference the same `rubrics.py` registry (via tools) — they must not embed divergent rubric text in their prompts.
