# P05 — Orchestrator & Blackboard

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. Design §6, §15.

## Context
Five specialists must behave like one coordinated team. The orchestrator (Conductor) owns the state machine — which stage/persona is active, gate status, needs-review propagation — and enforces the blackboard protocol so agents never trample each other's artifacts.

## Depends on
P02 (graph repo), P04 (engines for gate checks + impact).

## Produces (contracts owned here)
- `ProjectState` model.
- `Conductor.handle(project_id, message)` routing entrypoint.
- **Blackboard write-protocol** (single-writer per artifact type; cross-stage edits as proposed patches → ack → owning agent applies). Consumed by P06, exposed by P07.

## Scope / tasks
1. **ProjectState** — `app/orchestrator/state.py` (§15.1):
   ```python
   class ProjectState(BaseModel):
       project_id; current_stage: int; persona: Persona
       gate_status: dict[int, GateStatus]
       threads: dict[int, list[Message]]      # per-stage conversation
       project_brief: str                     # rolling summary injected into every agent
   ```
2. **State machine** — `app/orchestrator/state_machine.py`:
   - Forward transition `advance(stage)` guarded by P04 `ReadinessEngine` gate (`passed` required).
   - `reopen(stage)` (hybrid model): allowed; sets all downstream stages → `needs_review`.
   - Persona/stage validity: reject architect-only actions in stages 1–2 and vice-versa.
3. **Conductor** — `app/orchestrator/conductor.py` (§15.2):
   - Route a user message to the active stage's agent (P06) given persona.
   - Invoke Readiness on demand during a stage; invoke Impact after any **confirmed** edit or reopen.
   - Manage gate checks + needs-review propagation; emit events for P07 to stream.
4. **project_brief** — `app/orchestrator/brief.py` (§15.5): maintain a compact rolling summary (decisions + key constraints + stage-1 nuance) updated on each confirm; injected into every agent prompt.
5. **Blackboard protocol** — `app/orchestrator/blackboard.py` (§15.3):
   - `ProposedPatch {target_id, target_type, change, origin_agent}`.
   - Single-writer rule: only the owning agent for `target_type` may apply. Cross-stage agent edits must be emitted as `ProposedPatch` → enter Impact review → on human ack, routed to the owning agent to apply.

## Key files
`backend/app/orchestrator/{state,state_machine,conductor,brief,blackboard}.py`.

## Verification (pytest)
- Gate blocks `advance` until P04 reports `passed`; then transitions.
- `reopen(3)` flips stages 4 & 5 to `needs_review`.
- An architect action submitted in stage 1 is rejected.
- A `ProposedPatch` targeting PRD cannot be applied by the Architect agent — only routed to the PRD Author.
- `project_brief` updates on confirm and is present in the next agent invocation payload.

## Consistency notes
The orchestrator does not contain rubric or impact logic — it **invokes** P04. It does not write artifacts itself — agents (P06) do, under this protocol.
