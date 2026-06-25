# Realtime event contract (P07)

The WebSocket at `GET /projects/{project_id}/ws` is the frozen FE/BE realtime seam
(`app/api/chat.py`). REST resource shapes are covered by the generated OpenAPI schema at
`/openapi.json`; this file documents the WS event union, which OpenAPI does not describe.

## Client → server

```ts
{ message: string; persona: "business_user" | "tech_architect" }
```

## Server → client

The server runs one conductor turn and emits a sequence of typed events, each tagged by `t`,
always ending with `done` (or a single `error`):

```ts
type ServerEvent =
  | { t: "reply";            stage: number | null; text: string }   // assistant reply (whole, not token-streamed)
  | { t: "artifact_upserted"; node: Artifact }                      // one per written node (see types.ts Artifact)
  | { t: "scorecard";        scorecard: Scorecard }                 // live readiness for the active stage
  | { t: "escalation";       payload: object }                      // e.g. Stack Advisor radar conflict
  | { t: "impact_diff";      items: ImpactItem[] }                  // omitted when there is no impact
  | { t: "needs_review";     stages: number[] }                    // stages flipped to needs_review this turn
  | { t: "done" }                                                   // terminal: turn complete
  | { t: "error";            detail: string }                       // bad persona / gate / etc.; turn aborted
```

Ordering within a turn: `reply?` → `artifact_upserted*` → `scorecard` → `escalation?` →
`impact_diff?` → `needs_review?` → `done`.

> **Known limitation:** replies are emitted whole (no `token` stream). Agents produce *structured*
> outputs, so the reply is only available once the turn completes. See the repo README.

## Related REST shapes worth noting

- `POST /projects/{id}/advance` → `ConfirmResult` includes `blocked_by_stale: string[]` — the gate
  can report `gate_passed: true` while `advanced: false` because unreconciled stale nodes hold it
  shut (design §13.5). The UI should surface these.
- `POST /projects/{id}/impact/accept` → `{ node: Artifact; impact: ImpactReport }` — accepting a
  patch opens the next impact pass on the patched node (human-ack-between-passes cascade, §13.4),
  so `impact.items` may flag newly-affected neighbors.
