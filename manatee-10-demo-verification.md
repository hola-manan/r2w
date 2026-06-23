# P10 — Seed Data, Demo & Verification

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`. Design §11, §12.

## Context
Final plan: make the end-to-end demo runnable from a cold start and validate the design's acceptance scenarios — including the strongest demo move: the **same request → two profiles → two different, internally-consistent stacks**.

## Depends on
All prior plans (P01–P09).

## Scope / tasks
1. **Seed Company Profiles** — `backend/data/profiles/`: at least two contrasting profiles (e.g. EU-regulated fintech vs. fast-moving startup) with meaningfully different radars/compliance so the swap demo diverges. (Schema from P03.)
2. **Demo script** — `backend/data/demo/`: one vague business request + a suggested operator walkthrough (the messages to send per stage) so the demo is reproducible.
3. **Profile-swap demo** — a runnable scenario that takes the same request through both profiles and surfaces the divergent ADRs side by side (§12 acceptance).
4. **Verification suite** — `backend/tests/e2e_*.py`, implementing design §12 as automated/semi-automated checks:
   - **Walkthrough:** cold start → confirmed task plan; assert every node links to an upstream id (the §3 invariant).
   - **Gate test:** vague requirement is held at the gate with the correct follow-up.
   - **Impact test:** a stage-4 stack change flags the correct upstream PRD/ADR nodes.
   - **Constraint test:** a request that wants a Hold tech is redirected to an Adopt alternative with a compliant ADR (or escalated).
   - **Profile-swap:** same request → two profiles → visibly different, internally-consistent ADRs.
5. **README** — root `README.md`: prerequisites (Python, Node, Anthropic key), how to run backend (`uvicorn`) + frontend (`npm run dev`), seed/select a profile, and the demo walkthrough steps.

## Key files
`backend/data/profiles/*.json`, `backend/data/demo/*`, `backend/tests/e2e_*.py`, root `README.md`.

## Verification
- A single scripted run reaches a confirmed task plan from a cold database.
- Profile swap produces divergent ADR sets for the same request.
- All four acceptance checks (gate / impact / constraint / profile-swap) pass.
- A new developer can follow the README to run the full demo unaided.

## Consistency notes
This plan adds **no new product logic** — it exercises P01–P09 and packages the demo. Any gap found here is fixed in the owning plan, not patched locally, so the contracts stay authoritative.
