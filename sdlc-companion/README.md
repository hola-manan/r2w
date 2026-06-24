# AI-Powered SDLC Companion

An AI-mediated, five-stage software workflow — **Requirements → PRD → Stack/ADR →
Tech Spec → Task Plan** — driven by one operator switching personas (Business User /
Tech Architect). A team of specialist AI agents read and write a shared **Artifact
Graph**, grounded in a seeded **Company Profile** (tech radar + compliance), and made
legible by two engines built on one primitive:

- **Readiness Engine** — a visible, anchored rubric scorecard that *gates* progression.
- **Impact Analyzer** — after any change, walks the graph and flags stale/contradicted
  nodes with suggested fixes.

Both are built on a single **Graph Consistency Checker**. Stack decisions are emitted as
**ADRs** constrained to the company's radar (Adopt preferred, Trial with caveats, Hold
blocked) and must satisfy every hard compliance constraint — or the advisor escalates
the conflict instead of silently violating it.

> Proof-of-concept / portfolio piece. Single operator, sequential, SQLite.

## Architecture

```
backend/   FastAPI + SQLAlchemy (SQLite) + Anthropic
  app/schemas      shared artifact + edge contracts (P01)
  app/graph        Artifact Graph store + traversal (P02)
  app/profile      Company Profile + retriever + validation (P03)
  app/engines      consistency checker, rubrics, readiness, impact (P04)
  app/orchestrator state machine, conductor, blackboard, brief (P05)
  app/agents       5 specialists (P06)
  app/api          REST + WebSocket (P07)
frontend/  React + Vite + Tailwind
  src/api          typed client + realtime hook (P08)
  src/components   stage rail, cards, link chips, badges, scorecard (P08)
  src/stages       the 5 stage screens (P09)
```

The implementation plans live in `manatee-01..10-*.md` and the master index in
`i-have-a-big-sparkling-manatee.md`.

## Prerequisites
- Python 3.11+ (developed on 3.14), Node 18+ / npm
- An Anthropic API key (only needed to run the agents/engines *live*; the test suite
  runs fully offline with a fake LLM).

## Run the backend
```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt   # macOS/Linux

cp .env.example .env        # set ANTHROPIC_API_KEY (+ optional ANTHROPIC_MODEL)
.venv/Scripts/python -m uvicorn app.main:app --reload   # http://localhost:8000
```
Health check: `GET http://localhost:8000/health` → `{"status":"ok"}`.
Interactive API docs: `http://localhost:8000/docs`.

## Run the frontend
```bash
cd frontend
npm install
cp .env.example .env        # VITE_API_BASE defaults to http://localhost:8000
npm run dev                 # http://localhost:5173
```

## Demo walkthrough
1. Open the dashboard, pick a **Company Profile** (`eu-fintech` or `startup-web`), start a
   project.
2. **Stage 1 — Requirements:** chat on the left, the **live readiness scorecard** on the
   right. *Advance* is disabled until the hard dimensions go green.
3. **Stage 2 — PRD:** each item shows its source-requirement link chips.
4. **Stage 3 — Stack:** ADR cards with radar/compliance badges; "Challenge this" reopens a
   single decision and emits a superseding ADR.
5. **Stage 4 — Spec:** architect chat + spec components; edits trigger the **impact panel**.
6. **Stage 5 — Tasks:** epics → tasks with estimates and dependencies back to the spec.

Scripted run against a live server (needs a key):
```bash
cd backend && .venv/Scripts/python -m scripts.run_demo --profile eu-fintech
```

### The strong demo move: swap the profile
Run the same request under `eu-fintech` vs `startup-web`. A real-time/notification need is
served by Firebase/Pusher (**Adopt**) under `startup-web`, but Firebase is **Hold** under
`eu-fintech` (data must stay in EU) — so you get a *different, internally-consistent* stack
and a conflict escalation. This is verified automatically in
`tests/test_e2e.py::test_profile_swap_same_request_diverges`.

## Verify (offline, no API key)
```bash
cd backend && .venv/Scripts/python -m pytest -q
```
Covers the design's acceptance checks: the **gate test** (a vague requirement is held with
the right follow-up), the **constraint test** (a Hold technology is blocked), the **impact
test** (a change flags the correct downstream nodes), the **traceability invariant**, and
the **profile-swap** divergence.
