# P06 — Specialist Agents

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. Design §4, §14, §15.4.

## Context
Five Claude-backed specialists, each = system prompt (with rubric awareness) + a **scoped tool surface** + scratchpad. They read their inputs and write only their own artifact type (blackboard rule, P05). The Stack Advisor and Architect share one mechanism: NL objection → scoped regeneration → superseding artifact → consistency sweep.

## Depends on
P02 (repo), P03 (profile), P04 (engines + rubrics), P05 (conductor + blackboard).

## Produces
Five registered agents the Conductor routes to, plus their tool implementations.

## Scope / tasks
1. **Agent base** — `app/agents/base.py`: assembles Claude call = role system prompt + injected `project_brief` + scoped graph view + tool surface; enforces **ID-citation discipline** (outputs must cite upstream ids; un-cited downstream nodes are defects per §3).
2. **Tool surface** — `app/agents/tools.py`: thin wrappers over P02/P03/P04 exposed to agents (`query_profile, read_*, upsert_*, run_readiness, run_impact, ask_followup, decompose_decisions, run_coherence, escalate_conflict, propose_adr_change, check_dependency_cycles`). Each tool respects single-writer scoping.
3. **Requirements Analyst** — `app/agents/requirements_analyst.py`: tools `query_profile, upsert_requirement, run_readiness, ask_followup`. Goal-driven elicitation loop (§13.3): extract/update Requirement nodes → rescore → surface only gap-closing follow-ups for lowest dimensions.
4. **PRD Author** — `app/agents/prd_author.py`: tools `read_requirements, upsert_prd, run_readiness`. Enforce traceability (every PRD item ↔ ≥1 requirement; every requirement covered).
5. **Stack Advisor** — `app/agents/stack_advisor.py` (§14.1–14.4): full pipeline — decision decomposition → candidates from radar (P03) → ring filter (drop Hold, rank Adopt>Trial) → compliance gate (hard constraints) → selection + ADR authoring with mandatory citations → cross-decision coherence pass. Edge cases: Trial requires caveat + named Adopt fallback + risk; Hold/profile-gap → `escalate_conflict` (no silent violation). **Challenge flow**: reopen only the named decision point, emit a superseding ADR (`status: superseded-by`).
6. **Architect (spec co-editor)** — `app/agents/architect.py`: tools `read_prd, read_adr, upsert_spec, propose_adr_change, run_impact`. Co-editing loop (§4, §14.4): NL change → apply to spec → run Impact → may `propose_adr_change` (never edits ADR/PRD directly — emits ProposedPatch via P05).
7. **Planner** — `app/agents/planner.py`: tools `read_spec, upsert_task, check_dependency_cycles`. Decompose spec → epics/tasks/estimates/deps; enforce acyclicity (every component → ≥1 task).

## Key files
`backend/app/agents/{base,tools,requirements_analyst,prd_author,stack_advisor,architect,planner}.py`, plus prompt templates in `app/agents/prompts/`.

## Verification (per-agent, on seed data)
- Requirements Analyst converges a vague requirement to a green rubric via follow-ups.
- PRD Author produces items each citing ≥1 requirement; uncovered requirement is flagged.
- Stack Advisor: never selects a Hold/off-radar tech; emits an `escalate_conflict` when the PRD demands a Hold tech; Trial choice carries caveat + fallback; ADRs cite PRD/COMP/radar ids.
- Architect spec edit triggers Impact and surfaces an ADR `ProposedPatch` (not a direct ADR write).
- Planner output is an acyclic dependency graph covering every spec component.
- **Blackboard:** assert no agent writes outside its artifact type.

## Consistency notes
Agents call P04 rubrics/engines and P03 validation via tools — they do not re-implement scoring, impact, or ring/compliance logic in prompts. Prompts only frame the role and cite-discipline.
