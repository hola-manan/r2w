# P09 — Frontend Stage Views

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. Design §9.

## Context
The five screens that make the workflow tangible and the AI legible. Each composes P08 primitives and binds to the P07 realtime/REST contract. The headline moment is the live readiness scorecard gating the Advance button.

## Depends on
P08 (shared components, api client, realtime hook).

## Produces
The five stage routes under `/project/:id/stage/:n`.

## Scope / tasks
1. **Stage 1 — Requirements** `src/stages/requirements/` (§9.2): `SplitView` — chat on the left (streams `token` events), **live `Scorecard`** on the right binding `scorecard` events; dimensions animate amber→green; **Advance button disabled until `gate.passed`** (the single most important visual). Follow-up questions surfaced inline.
2. **Stage 2 — PRD review** `src/stages/prd/` (§9.3): list of `ArtifactCard`s (PRD items) each showing `LinkChips` to source requirements; inline edit + confirm (POST upsert → re-render).
3. **Stage 3 — Stack** `src/stages/stack/` (§9.4): ADR cards with rationale + **radar/compliance badges**; "Challenge this" opens a back-and-forth that streams a superseding ADR; handle `escalation` events (conflict prompt: relax / off-radar exception / rescope).
4. **Stage 4 — Spec workspace** `src/stages/spec/` (§9.5): `SplitView` — architect chat + structured spec editor; **Impact panel** binding `impact_diff` events, listing stale/contradicted nodes with Accept / Edit / Dismiss(reason) actions (§13.5) wired to P07 impact endpoints.
5. **Stage 5 — Task board** `src/stages/tasks/` (§9.6): epics → tasks with estimates; dependency links rendered back to spec components (`LinkChips` / simple graph).
6. **Needs-review affordance**: any stage with `needs_review` shows the badge and re-locks Advance until cleared (consume `needs_review` events).

## Key files
`frontend/src/stages/{requirements,prd,stack,spec,tasks}/*`.

## Verification (against running backend)
- Stage 1: scorecard updates live; Advance is disabled until the gate passes, then enabled.
- Stage 2: each PRD item shows working source-requirement chips; edit persists.
- Stage 3: challenge produces a superseding ADR card; an escalation renders the conflict choices.
- Stage 4: an architect edit populates the Impact panel; Accept routes a patch and the node un-stales.
- Stage 5: task board shows dependency links to spec components.
- Reopening an upstream stage flips downstream rails to needs_review in the UI.

## Consistency notes
All data flows through P08's `apiClient`/`useRealtime`; stage views hold layout + interaction only, no bespoke fetch logic. Visuals must match the design narrative (§9) — the gating and traceability cues are the point.
