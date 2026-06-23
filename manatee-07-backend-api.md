# P07 — Backend API & Realtime

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`.

## Context
The frontend (P08/P09) is a separate React app. This plan defines the **only** seam between front and back: REST resources + a realtime channel for streaming chat tokens, live scorecard updates, and impact diffs. The event/resource schema published here is what the frontend codes against.

## Depends on
P05 (conductor/state), P06 (agents), P04 (engines).

## Produces (contract owned here)
REST resource shapes + realtime event type union. Consumed by P08, P09.

## Scope / tasks
1. **REST routers** — `app/api/`:
   - `projects.py`: `POST /projects` (create, choose/seed profile id), `GET /projects`, `GET /projects/{id}` (returns `ProjectState` + gate_status).
   - `artifacts.py`: `GET /projects/{id}/artifacts?stage=&type=` (nodes + their link chips), `GET /projects/{id}/graph` (nodes+edges for traceability views).
   - `gates.py`: `POST /projects/{id}/advance`, `POST /projects/{id}/reopen/{stage}`, `GET /projects/{id}/readiness/{stage}` (live scorecard snapshot).
   - `impact.py`: `GET /projects/{id}/impact` (current consistency_diff), `POST .../impact/{item}/accept|dismiss` (dismiss requires reason → audit note, §13.5).
2. **Realtime** — `app/api/chat_ws.py`: WebSocket (fallback SSE) per project. Client sends a user message; server streams a typed event union:
   ```ts
   type Event =
     | {t:"token", stage, text}
     | {t:"artifact_upserted", node}
     | {t:"scorecard", stage, dimensions, gate}
     | {t:"impact_diff", items}
     | {t:"needs_review", stages}
     | {t:"escalation", payload}        // Stack Advisor conflict
     | {t:"done", stage}
   ```
   Conductor (P05) emits; the WS handler forwards.
3. **DTO mapping** — `app/api/dto.py`: map P01 schemas ↔ wire shapes (keep envelope fields, expose links as chips). Single mapping module so FE shapes never diverge.
4. **Wiring** — register routers + WS in `app/main.py`; dependency-inject repo/conductor/engines.
5. **Contract doc** — emit OpenAPI; document the WS event union in `frontend/`-readable form (e.g. a generated `events.d.ts` or a markdown spec).

## Key files
`backend/app/api/{projects,artifacts,gates,impact,chat_ws,dto}.py`, `backend/app/main.py`.

## Verification
- `httpx` tests cover each REST route (create project → advance blocked until gate → reopen flips needs_review).
- A scripted WS session drives a stage-1 turn and receives `token` → `artifact_upserted` → `scorecard` events ending in `done`.
- Dismiss-impact without a reason is rejected (400).
- OpenAPI + event spec generated and checked in.

## Consistency notes
No business logic here — routers/WS only translate between HTTP/WS and P05/P06/P04. The event union is the frozen FE/BE contract; changing it is a coordinated P07+P08 change.
