# AI-Powered SDLC Companion — Implementation Plan Set (Master Index)

## Context

The source design doc (`i-want-to-plan-shimmying-manatee.md`) fully specifies an AI-mediated, five-stage SDLC pipeline (Requirements → PRD → Stack/ADR → Tech Spec → Task Plan) driven by a single operator switching personas, with a multi-agent "team" reading/writing a shared **Artifact Graph**, grounded in a seeded **Company Profile**, and made legible by two signature engines (**Readiness** + **Impact Analyzer**) built on one shared **Graph Consistency Checker**.

The design is locked; what's missing is an **implementation breakdown**. This master plan decomposes the build into **10 balanced sub-plans** that are individually shippable, ordered by dependency, and held mutually consistent through a small set of **shared contracts** (defined once, imported everywhere). Stack decisions (locked with the user):

- **Backend:** Python + FastAPI, Pydantic for schemas, SQLAlchemy/SQLModel ORM over **SQLite**.
- **Frontend:** React + Vite + Tailwind (separate app).
- **Agents:** Anthropic Python SDK (Claude), structured outputs, low-temperature for scoring/analysis.
- **Fidelity:** PoC / portfolio — single operator, sequential, no multi-user concurrency hardening.

> **Deliverable note:** This file is the master index. On approval I will create the 10 sub-plan files listed below (`manatee-01-*.md` … `manatee-10-*.md`) in `.claude/plans/`, each expanding the summary here into a full task-level plan.

---

## Repository layout (established by Plan 01, used by all)

```
sdlc-companion/
  backend/
    app/
      main.py            config.py
      llm/               # P01  Anthropic client wrapper, structured-output + low-temp helpers
      schemas/           # P01  Pydantic artifact models, typed edges, API DTOs  ← SHARED CONTRACT
      db/                # P01/P02  engine, session, ORM models
      graph/             # P02  repository, edges, versioning, traversal (BFS)
      profile/           # P03  loader, retriever, radar/compliance validation
      engines/           # P04  consistency_checker, readiness, impact, rubric registry
      orchestrator/      # P05  state machine, conductor, blackboard, project_brief
      agents/            # P06  base + 5 specialists + tool surfaces
      api/               # P07  REST routers, WebSocket/SSE, DTO mapping
    data/                # P03/P10  seed profiles, sqlite db file
    tests/               # per-plan tests
  frontend/
    src/
      api/               # P08  REST client + realtime hooks
      components/        # P08  shared: artifact card, link chips, gate/needs-review badges, stage rail
      design/            # P08  tokens, tailwind config
      routes/            # P08  dashboard
      stages/            # P09  the 5 stage screens
  README.md              # P10
```

---

## Shared contracts (the consistency seams)

These are the reason the sub-plans don't drift apart. Each is **defined once** in the named plan and **only referenced** afterward — no re-definition, no copy-paste.

| Contract | Owner plan | Consumed by |
|---|---|---|
| **Artifact schemas** (Requirement, PRDItem, ADR, SpecComponent, Task) as Pydantic models | P01 | P02, P04, P05, P06, P07 |
| **Node ID conventions** `REQ-/PRD-/ADR-/SPEC-/TASK-/COMP-` + `version, created_by_agent, last_changed, stale` envelope | P01 | all |
| **Typed-edge enum** (`derives_from, satisfies, realizes, constrains, implements`) | P01 | P02, P04 |
| **Graph repository interface** (CRUD per type, edge link, neighbor traversal, version/stale ops) | P02 | P04, P05, P06 |
| **Profile + Retriever interface** (radar/compliance lookup, citation refs, `chosen ∈ radar` validation) | P03 | P04, P06 |
| **Consistency Checker primitive** `check(node|pair, rubric|edge_semantics) → verdict+evidence` | P04 | P04 (both engines), reused not reimplemented |
| **Rubric registry** (per-stage hard/soft dimensions + anchored 4-level descriptors) as **data, not prompt-baked** | P04 | P06 (agents reference same rubric) |
| **Blackboard write-protocol** (single-writer per artifact type; cross-stage edits flow as proposed patches → human ack → owning agent applies) | P05 | P06 |
| **API contract** (REST resource shapes + realtime event types for chat tokens / scorecard / impact diffs) | P07 | P08, P09 |

---

## Sub-plan overview & dependency graph

```
P01 Foundation & contracts
  ├─► P02 Artifact Graph store
  ├─► P03 Company Profile & Retriever
  │
  ├─► P04 Shared engines ......... (needs P02 graph, P03 profile)
  ├─► P05 Orchestrator & blackboard (needs P02, P04)
  ├─► P06 Specialist agents ...... (needs P02, P03, P04, P05)
  ├─► P07 Backend API & realtime . (needs P05, P06, P04)
  │
  ├─► P08 Frontend foundation .... (needs P07 contract)
  └─► P09 Frontend stage views ... (needs P08)
        └─► P10 Seed data, demo & verification (needs all)
```

Each plan below is sized to be a focused increment (no single plan owns more than one cohesive area). Heavier areas (engines, agents, stage views) are isolated rather than bundled.

---

### P01 — Foundation & shared contracts
**Goal:** Stand up the monorepo and define the single source of truth every later plan imports.
**Depends on:** —
**Produces (contracts):** artifact Pydantic schemas, node-ID/envelope conventions, typed-edge enum, LLM client wrapper, DB engine/session.
**Scope:**
- Monorepo scaffold: `backend/` (FastAPI app, config, `uv`/`poetry`), `frontend/` (Vite+React+Tailwind), shared dev tooling (ruff, pytest, eslint).
- `app/schemas/`: Pydantic models for the 5 artifact types per design §8 + the common envelope (`id, version, created_by_agent, last_changed, stale`) + `DocumentType`/`EdgeType` enums + ID-prefix helpers.
- `app/llm/`: thin Anthropic client wrapper — one `complete()` and one `structured(schema)` helper (forces JSON / Pydantic-validated output), low-temp default profile for scoring/analysis, retry/timeout, model id config.
- `app/db/`: SQLAlchemy engine + session factory pointed at `data/project.db`; base model; Alembic (or `create_all` for PoC).
- `app/main.py`: FastAPI app, health route, CORS for the Vite dev server.
**Key files:** `backend/app/{main,config}.py`, `backend/app/schemas/*`, `backend/app/llm/client.py`, `backend/app/db/{base,session}.py`.
**Verification:** `pytest` schema round-trip tests; `uvicorn` boots + `/health` 200; structured-output helper validates a sample DimensionScore.

### P02 — Artifact Graph store
**Goal:** Persist the graph (nodes, typed edges, versions, stale flags) behind a clean repository interface.
**Depends on:** P01.
**Produces (contract):** `GraphRepository` interface used by engines, orchestrator, agents.
**Scope:**
- ORM tables: `nodes` (type, json payload validated against P01 schemas, envelope cols), `edges` (from_id, to_id, EdgeType), `node_versions` (audit trail).
- Repository: typed CRUD per artifact type (create/upsert/get/list-by-type/by-project), `link(from,to,edge)`, `neighbors(id, direction, edge_filter)` BFS helper, `bump_version()`, `set_stale()/clear_stale()`.
- Project scoping (multiple projects per DB) and the rule "every node carries its links" so traversal is cheap.
**Key files:** `backend/app/db/models.py`, `backend/app/graph/repository.py`, `backend/app/graph/traversal.py`.
**Verification:** unit tests — create REQ→link→PRD, traverse both directions, version bump increments + snapshots, stale set/clear; round-trip of each artifact type through ORM↔Pydantic.

### P03 — Company Profile & Profile Retriever
**Goal:** Seed and serve the grounding spine (tech radar + compliance) with citation support and radar validation.
**Depends on:** P01.
**Produces (contract):** `ProfileRetriever` (lookup by category/ring, compliance hard-constraint set, `validate_choice(tech) → in_radar/ring`), profile schema + seed format.
**Scope:**
- Profile schema (Pydantic): radar entries `{name, category, ring, notes}`, compliance entries `{id, rule, scope, hard_constraint}`; loaded from seeded JSON/markdown in `data/`.
- Retriever service: category→candidates, ring ranking (Adopt>Trial), hard-constraint enumeration, citation-ref helpers returning radar/COMP ids.
- Validation helpers reused by Stack Advisor + Stack rubric: `chosen ∈ radar`, `no Hold`, `all hard_constraints addressed`.
- Support **swappable profiles** (design §11 "very strong demo move") — load by profile id.
**Key files:** `backend/app/profile/{schema,loader,retriever,validation}.py`, `backend/data/profiles/*.json`.
**Verification:** load seed profile; query datastore category returns ringed candidates; `validate_choice` rejects a Hold/off-radar tech; two different profiles loadable by id.

### P04 — Shared engines (Consistency Checker → Readiness + Impact)
**Goal:** Build the one reasoning primitive and the two engines on top of it — the product's "legible intelligence."
**Depends on:** P02, P03.
**Produces (contract):** rubric registry (data), `ReadinessEngine.score(stage)`, `ImpactAnalyzer.analyze(changed_nodes)`.
**Scope:**
- **Graph Consistency Checker** (§13): `check(node_or_pair, rubric|edge_semantics) → verdict {level/valid|stale|contradicted|unsupported, evidence[ids], justification, followup?/suggested_patch?}` via P01 structured LLM helper at low temp.
- **Rubric registry** (§13.2): per-stage hard + soft dimensions with **anchored 4-level descriptors** (L0–L3) encoded as data; weighting + gate rule `all(hard==Green) AND weighted_soft ≥ threshold`.
- **Readiness Engine** (§13.1–13.3): score all dimensions for a stage (incremental over changed nodes), emit live scorecard + gap-closing follow-up questions, compute gate pass/fail.
- **Impact Analyzer** (§13.4): on confirmed node change, BFS over typed edges (both directions), run checker per neighbor, emit `consistency_diff` with suggested patches, cascade control (only content-changed nodes, batched, depth cap, human-ack between passes), set `stale`.
**Key files:** `backend/app/engines/{consistency_checker,rubrics,readiness,impact}.py`.
**Verification:** paper-test gate (vague requirement held at gate with right follow-up); impact-test (stage-4 stack change flags correct upstream PRD/ADR); anchored scores reproducible across runs at low temp.

### P05 — Orchestrator & blackboard
**Goal:** The state machine + routing + blackboard protocol that makes five agents behave like one coordinated team.
**Depends on:** P02, P04.
**Produces (contract):** `ProjectState`, `Conductor.handle(message)`, blackboard write-protocol.
**Scope:**
- `ProjectState` (§15.1): `current_stage, persona, gate_status{stage:locked|passed|needs_review}, threads{stage}, project_brief`.
- State machine: forward transitions guarded by P04 gates; **reopen** transitions set downstream `needs_review`; persona/stage validity enforcement (architect actions rejected in stages 1–2).
- **Conductor** (§15.2): route message → active stage's agent by persona; invoke Readiness on demand, Impact after confirmed edit/reopen; manage gate checks + needs-review propagation.
- `project_brief` maintenance (§15.5): rolling compact summary injected into every agent so stage-1 nuance survives transitions.
- **Blackboard protocol** (§15.3): single-writer per artifact type; cross-stage edits enter as **proposed patches** → human ack → owning agent applies. Define the patch object + ack flow here (agents implement in P06).
**Key files:** `backend/app/orchestrator/{state,conductor,blackboard,brief}.py`.
**Verification:** gate blocks advance until P04 passes; reopening stage 3 flips stages 4–5 to needs_review; architect action in stage 1 rejected; proposed-patch can't be written by a non-owning agent.

### P06 — Specialist agents
**Goal:** The five Claude-backed specialists with scoped tool surfaces and rubric-aware prompts.
**Depends on:** P02, P03, P04, P05.
**Produces:** registered agents the Conductor can route to.
**Scope (per §15.4 tool surfaces):**
- `base.py`: agent = Claude + role system prompt (incl. its rubric awareness) + tool surface + scratchpad; ID-citation discipline baked in.
- **Requirements Analyst** — `query_profile, upsert_requirement, run_readiness, ask_followup`; goal-driven elicitation loop (§13.3).
- **PRD Author** — `read_requirements, upsert_prd, run_readiness`; traceability (every item ↔ ≥1 req).
- **Stack Advisor** — full constrained-generation pipeline (§14.1): decision decomposition → candidate gen from radar → ring filter → compliance gate → ADR authoring with mandatory citations → cross-decision coherence; ring/gap edge cases (§14.2: Trial caveat+fallback, Hold/profile-gap escalation); **challenge flow** (§14.4) emitting superseding ADRs.
- **Architect (spec co-editor)** — `read_prd, read_adr, upsert_spec, propose_adr_change, run_impact`; NL objection → scoped regeneration → consistency sweep (shares mechanism with Stack Advisor challenge).
- **Planner** — `read_spec, upsert_task, check_dependency_cycles`; epics/tasks/estimates/deps, acyclicity.
**Key files:** `backend/app/agents/{base,requirements_analyst,prd_author,stack_advisor,architect,planner,tools}.py`.
**Verification:** end-to-end per agent on seed data — Requirements Analyst closes a rubric gap; Stack Advisor rejects a Hold tech and escalates; Architect edit triggers Impact; Planner produces acyclic task graph; no agent writes outside its artifact type.

### P07 — Backend API & realtime
**Goal:** Expose orchestrator/engines/agents over a stable HTTP + streaming contract for the frontend.
**Depends on:** P05, P06, P04.
**Produces (contract):** REST resource shapes + realtime event types.
**Scope:**
- REST routers: projects (create/seed-profile/list), graph/artifacts (read by stage/type, with links), gate status, confirm-stage / reopen-stage, accept/dismiss consistency_diff item.
- Realtime (WebSocket or SSE): stream chat tokens, live scorecard updates, impact diffs, needs-review flags.
- DTO mapping between P01 schemas and wire shapes; document the event schema (this is what P08/P09 code against).
**Key files:** `backend/app/api/{projects,artifacts,gates,chat_ws,dto}.py`, `backend/app/main.py` wiring.
**Verification:** httpx tests for each route; a scripted WS session drives a stage-1 turn and receives scorecard events; OpenAPI/event-schema doc generated.

### P08 — Frontend foundation & shared components
**Goal:** App shell, design system, API/realtime client, and the reusable primitives every stage screen needs.
**Depends on:** P07.
**Produces:** `apiClient` + realtime hooks; shared components.
**Scope:**
- Vite/React/Tailwind shell, routing, design tokens; **project dashboard** (pick/seed profile, start project) and the **five-stage progress rail** (§9.1).
- `api/`: typed REST client + `useRealtime` hook (chat tokens, scorecard, impact, needs-review) against the P07 contract.
- Shared components: artifact card, **traceability link chips** (node-id references), **gate / needs-review badges**, scorecard widget shell, split-view layout.
**Key files:** `frontend/src/{design,api,components,routes/dashboard}/*`.
**Verification:** dashboard lists projects from backend; realtime hook receives a test event; stage rail reflects gate_status; Storybook (optional) or a sandbox route renders each shared component.

### P09 — Frontend stage views
**Goal:** The five stage screens that make the workflow tangible and the AI legible.
**Depends on:** P08.
**Scope (per §9):**
- **Stage 1 Requirements:** split view — chat left, **live readiness scorecard** right (dimensions amber→green), Advance disabled until gate passes (the headline moment).
- **Stage 2 PRD review:** AI-drafted items with source-requirement link chips; inline edit + confirm.
- **Stage 3 Stack:** ADR cards with rationale + **radar/compliance badges**; "challenge this" reopen flow.
- **Stage 4 Spec workspace:** architect chat + structured spec editor; **impact panel** listing stale/contradicted nodes with accept/reject reconciliations.
- **Stage 5 Task board:** epics→tasks with estimates + dependency links back to spec components.
**Key files:** `frontend/src/stages/{requirements,prd,stack,spec,tasks}/*`.
**Verification:** click-through each stage against the running backend; Advance gating visibly enforced; challenge produces a superseding ADR card; impact panel reflects a real diff; task board shows dependency links.

### P10 — Seed data, demo & verification
**Goal:** Make the end-to-end demo runnable and validate the design's acceptance scenarios.
**Depends on:** all.
**Scope:**
- One+ sample **Company Profile(s)** + one **vague business request** script (design §12 walkthrough).
- The **profile-swap demo**: same request → two profiles → visibly different, internally-consistent ADRs (§11/§12 acceptance).
- Verification suite implementing the four paper tests as automated/semi-automated checks: gate test, impact test, constraint test, profile-swap.
- `README.md`: run backend + frontend, seed, walkthrough steps.
**Key files:** `backend/data/profiles/*`, `backend/tests/e2e_*`, `README.md`.
**Verification:** scripted run reaches a confirmed task plan from a cold start; profile swap yields divergent ADRs; all four acceptance checks pass.

---

## How consistency is guaranteed across plans
1. **One contract, one owner** (table above) — later plans import, never redefine.
2. **Schemas-first**: P01 fixes every artifact + edge shape before any logic is written.
3. **One reasoning primitive**: rubric/impact logic lives only in P04's Consistency Checker; agents and engines call it, never re-prompt it.
4. **Rubrics as data**: the same rubric registry gates progression (Readiness) and informs agent prompts — no divergence between "what the gate checks" and "what the agent optimizes."
5. **Single-writer blackboard**: P05 protocol prevents agents in P06 from trampling each other's artifacts.
6. **API contract as the FE/BE seam**: P07 event/resource schema is the only thing P08/P09 depend on.

## Global verification (design §12, end-to-end)
- Cold-start walkthrough: seed profile → vague request → Stage 1 chat closes rubric gaps → gate opens → PRD → constrained ADRs → spec + impact sweep → acyclic task plan.
- Gate / impact / constraint / profile-swap acceptance tests from P10 pass.
- Traceability holds: every downstream node cites an upstream id; uncited nodes are flagged (the §3 invariant).

## On approval
I will create the ten files `manatee-01-foundation.md` … `manatee-10-demo-verification.md` in `.claude/plans/`, each expanding its section above into a task-level plan (concrete file lists, function signatures for the shared contracts, and per-plan test checklists).
