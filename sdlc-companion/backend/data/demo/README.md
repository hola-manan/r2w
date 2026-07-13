# Demo — Customer Complaint & Dispute Resolution Portal (eu-fintech)

A scripted walkthrough that shows the **readiness gate visibly BLOCK, then PASS** at every
one of the five stages. The project is an EU-regulated fintech complaint/dispute portal — a
normal web app, so it exercises the gate and the profile's compliance rules (not the team
automation tools).

The exact messages live in [`walkthrough.json`](./walkthrough.json). Each stage has two
`steps`: the first is worded to leave a gap the gate catches (`expect_advanced: false`), the
second closes it (`expect_advanced: true`).

## What each stage demonstrates

| Stage | Type msg 1 → **blocked** because… | Type msg 2 → **passes** |
|-------|-----------------------------------|--------------------------|
| **1 Requirements** | a vague ask → **Clarity / Testability / Scope** score red | actors + flow + explicit in/out-of-scope + measurable success + compliance NFR |
| **2 PRD** | "PRD for submission + triage **only**" → the audit/EU/encryption requirements are uncovered → **Traceability** red | "add PRD items for audit trail, EU residency, encryption + search; link every requirement" |
| **3 Stack** | "use **Firebase** for real-time" → Firebase is **Hold** under eu-fintech → the advisor **escalates the conflict** and writes nothing → gate red | "use the approved managed **WebSocket**, complete the stack, and satisfy COMP-1…4" |
| **4 Spec** | "spec the submission service **only**" → other PRD items unrealized → **Component coverage** red | "add components for the remaining PRD items, referencing the ADRs" |
| **5 Tasks** | "break down the intake epic **only**" → other components untasked → **Decomposition** red | "add tasks for all remaining components, with estimates + dependencies" |

The **stage-3 escalation** ("Firebase is on Hold — data must stay in the EU") is the
signature moment: the advisor refuses to silently violate the radar and asks the operator to
choose. Optional encore (`profile_swap` in `walkthrough.json`): the same Firebase request is
**accepted** under `startup-web` — one profile swap, a different internally-consistent stack.

## Setup

```bash
cd backend
python -m venv .venv && . .venv/bin/activate      # or use your interpreter
pip install -r requirements.txt
echo "GOOGLE_API_KEY=<your Vertex AI Express key>" > .env
```

The demo runs with the **team Tech Catalog disabled** so the automation tools never appear —
start the server (and the scripted runner's server) with `TECH_CATALOG_ENABLED=false`.

## Option A — scripted (fastest, self-checking)

```bash
# terminal 1: server
cd backend && TECH_CATALOG_ENABLED=false python -m uvicorn app.main:app --port 8000
# terminal 2: run the staged walkthrough
cd backend && python -m scripts.run_demo --profile eu-fintech --verbose
```

For each step it prints the agent reply, the readiness scorecard (each dimension's
level/justification — the live LLM scoring), any escalation, and the `POST /advance` result,
asserting it matches `expect_advanced`. A clean run ends with
`All stages blocked-then-passed as expected.`

## Option B — live in the UI (most compelling)

Start the backend as above (with `TECH_CATALOG_ENABLED=false`) and the frontend
(`cd frontend && npm run dev`). Open the dashboard, create a project on **eu-fintech**, and
type the two messages per stage from `walkthrough.json`. After msg 1 the scorecard shows the
red dimension and **Advance** is disabled; after msg 2 it goes green and Advance unlocks.
Switch persona to **Tech Architect** at stage 3.

## Demo-tuning notes (so the numbers make sense)

To make the gate reliably achievable with a real, strict LLM while keeping the blocks sharp:
- A hard dimension advances at **amber (L2)** or better; only red (L0–L1) blocks
  (`app/engines/readiness.py`). The weighted soft score must reach **0.8**
  (`app/engines/rubrics.py`), so the "fixing" message at each stage is written to drive the
  soft dimensions (completeness, prioritization, failure-handling, …) green.
- The readiness scorer (`app/engines/consistency_checker.py`) awards level 3 when the anchor
  is *substantially* met — not only when flawless — so a genuinely good artifact can reach
  green at the 0.8 bar. Deliberately vague or incomplete inputs still score L0–L1, so the
  block steps hold (and the structural hard gates — traceability, coverage, decomposition —
  are independent of the scorer and block regardless).
- Requirements are stored as finalized statements — follow-up questions stay in the chat and
  the scorecard, not on the node (`app/agents/requirements_analyst.py`) — so a well-specified
  answer can actually reach "testable."
- The blocking messages deliberately scope narrowly ("only…") to leave a clear gap.
