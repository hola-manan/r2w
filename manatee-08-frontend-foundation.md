# P08 — Frontend Foundation & Shared Components

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. Design §9.

## Context
The portfolio value lives in the UI being legible. This plan builds the shell, design system, API/realtime client, and the reusable primitives (cards, link chips, badges, scorecard widget, split view) that all five stage screens (P09) compose.

## Depends on
P07 (REST + WS event contract).

## Produces
`apiClient`, `useRealtime` hook, and the shared component library + design tokens. Consumed by P09.

## Scope / tasks
1. **Shell & design system** — `src/design/`: Tailwind config + tokens (color, spacing, type scale), base layout, dark/light. App router (`react-router`) with routes for dashboard + `/project/:id/stage/:n`.
2. **API client** — `src/api/client.ts`: typed wrappers over P07 REST (projects, artifacts, gates, impact). Generated/handwritten types matching `dto`/OpenAPI.
3. **Realtime hook** — `src/api/useRealtime.ts`: open the project WebSocket, parse the P07 `Event` union, expose reducers for `tokens`, `scorecard`, `impact_diff`, `needs_review`, `escalation`.
4. **Dashboard** — `src/routes/Dashboard.tsx` (§9.1): list/create projects, pick or seed a Company Profile, show the **five-stage progress rail** reflecting `gate_status` (locked/passed/needs_review).
5. **Shared components** — `src/components/`:
   - `StageRail` — the five-stage progress indicator with gate badges.
   - `ArtifactCard` — generic node card (title, body, status).
   - `LinkChips` — renders upstream/downstream node-id references (traceability, §3) as clickable chips.
   - `GateBadge` / `NeedsReviewBadge` — gate status pills.
   - `Scorecard` — dimension rows with R/A/G state + justification + follow-up (shell; stage-1 binds live data in P09).
   - `SplitView` — chat-left / panel-right layout used by stages 1 and 4.

## Key files
`frontend/src/design/*`, `frontend/src/api/{client,useRealtime}.ts`, `frontend/src/routes/Dashboard.tsx`, `frontend/src/components/*`.

## Verification
- Dashboard lists projects from the backend and creates one with a chosen profile.
- `useRealtime` receives a backend test event and updates state.
- `StageRail` renders the correct gate states from `GET /projects/{id}`.
- A sandbox/Storybook route renders every shared component with mock props.

## Consistency notes
Components consume only the P07 contract types — no direct knowledge of backend internals. Stage-specific layouts belong to P09; keep this layer generic and reusable.
