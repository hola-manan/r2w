# AI-Powered SDLC Companion — Design Document (v1)

> **Nature of this document:** This is a *design/strategy* artifact. The product described here is a proof-of-concept / portfolio piece and (per the user's instruction) will **not be implemented**. The deliverable is the design itself: the reasoning, the architecture, the data model, and the UX narrative. "Verification" below therefore means *how we'd validate the design*, not how we'd test code.

---

## 1. Context

Real companies move a software idea through a chain of human roles — a business stakeholder voices a need, a product person turns it into a PRD, an architect picks a stack and writes a tech spec, a lead breaks it into tasks. Each handoff is lossy, slow, and inconsistent, and the reasoning behind decisions (especially *why this stack*) is rarely captured.

This product **mimics that procedure** as an AI-mediated workflow. A single operator drives the whole chain by switching between two personas (Business User, Tech Architect); a team of specialized AI agents produces and continuously reconciles a set of linked artifacts, grounded in a specific company's standards.

**Intended outcome:** a compelling end-to-end demonstration that an AI "team" can take a vague business request and walk it — with visible, legible reasoning and human gates — all the way to a buildable, stack-justified, task-broken-down plan that respects a real company's constraints.

### Decisions locked with the user
- **Goal:** Proof-of-concept / portfolio (optimize for a legible, impressive end-to-end demo; minimal production hardening).
- **Scope end-state:** continues past the tech spec to **task / project breakdown** (5 stages total).
- **Stack selection:** **constrained by company standards** (grounded in a seeded Company Profile).
- **Workflow model:** **hybrid** — confirm each stage with gates, but reopening upstream is allowed and the AI surfaces impacts.
- **AI architecture:** **multi-agent specialists** sharing a central artifact store.
- **Role model:** **one operator switching personas.**
- **Readiness engine:** **explicit, visible rubric/scorecard** that gates progression.
- **Company Profile dimensions:** **approved tech radar** + **compliance & security** (team-skills and budget/scale intentionally out of scope for v1).

---

## 2. Product summary

A five-stage, human-in-the-loop pipeline. Every stage reads from a shared **Company Profile** (the spine) and reads/writes a shared **Artifact Graph** (the state).

```
                 ┌─────────────────────────────────────────────┐
                 │  COMPANY PROFILE  (seeded, read by all)      │
                 │  • Tech Radar: Adopt / Trial / Hold          │
                 │  • Compliance & Security constraints         │
                 └─────────────────────────────────────────────┘
                                     │ grounds every decision
   Business User hat │                                   │ Tech Architect hat
        ▼            ▼                                   ▼            ▼
  ┌───────────┐  ┌───────┐   ┌───────────────┐   ┌────────────┐  ┌────────────┐
  │ [1] Reqs  │->│[2] PRD│-> │[3] Stack (ADR)│-> │[4] TechSpec│->│[5] TaskPlan│
  └───────────┘  └───────┘   └───────────────┘   └────────────┘  └────────────┘
        ▲             ▲              ▲                  │  │
        └─────────────┴──────────── IMPACT ANALYZER ◄──┘  │
                     (spec/stack edits ripple upstream)    │
```

---

## 3. The core mental model: one Artifact Graph

The five "documents" are not independent — they are **projections of a single evolving graph**. Each node carries a stable ID and links to its neighbors, which is what makes traceability and impact analysis possible.

```
Requirement (REQ-1) ─┐
                     ├─► PRD Item (PRD-1) ─┐
Requirement (REQ-2) ─┘                     ├─► Stack Decision / ADR-1 ─┐
                                           │                           ├─► Spec Component (SPEC-1) ─► Task (TASK-1)
                                           └─► PRD Item (PRD-2) ───────┘
```

**Design principle:** every downstream artifact must cite the upstream node(s) it derives from. A spec component with no PRD link, or an ADR that satisfies no requirement, is a *consistency defect* the system flags. This single rule powers both the readiness gate (forward) and the impact analyzer (any direction).

---

## 4. The five stages in detail

| # | Stage | Driving persona | Specialist agent | Human interaction | Exit gate | Output artifact |
|---|-------|-----------------|------------------|-------------------|-----------|-----------------|
| 1 | Requirements capture | Business User | **Requirements Analyst** | Conversational elicitation; AI asks targeted questions to remove ambiguity | Readiness scorecard ≥ threshold | Structured Requirements set |
| 2 | PRD generation | Business User | **PRD Author** | AI drafts PRD; user reviews/edits/confirms | User confirmation | PRD (linked to requirements) |
| 3 | Stack decision | (system) → Architect | **Stack Advisor** | AI proposes stack with reasoning; architect can challenge | Architect confirmation | ADR set (linked to PRD, radar, compliance) |
| 4 | Tech spec | Tech Architect | **Architect (spec co-editor)** | Back-and-forth Q&A; AI edits spec *and* may revise the stack | Architect confirmation | Tech Spec (linked to PRD + ADRs) |
| 5 | Task / project plan | Tech Architect | **Planner** | AI decomposes into epics/tasks/estimates/deps; user adjusts | User confirmation | Task plan (linked to spec) |

Notes on the trickier stages:
- **Stage 1** is where the *Readiness Engine* (§5.1) lives. The chat is goal-driven, not free-form: the agent works the conversation toward closing every red/amber rubric dimension.
- **Stage 3** is *constrained generation*: the Stack Advisor may only choose technologies present in the tech radar (Adopt preferred, Trial allowed-with-caveat, Hold blocked) and must satisfy every applicable compliance rule. Output is one or more **ADRs** (§7), not prose.
- **Stage 4** is a *co-editing loop*: the architect pushes changes in natural language; the agent applies them to structured spec state, then runs the *Impact Analyzer* (§5.2) — which can bubble a change back into the ADRs (and flag affected PRD items).

---

## 5. The two signature engines

> **Key insight:** these are the *same primitive* viewed in two directions — a reasoner over whether the Artifact Graph is internally consistent and complete enough. Designing this one capability well is what makes the product feel intelligent rather than like four disconnected chatbots.

### 5.1 Readiness Engine (forward / gating)
A **visible scorecard** scored per stage. Proposed dimensions for the Requirements stage:

| Dimension | Question it answers |
|-----------|---------------------|
| Clarity | Is the language unambiguous, with defined entities? |
| Completeness | Are personas, primary flows, and edge cases present? |
| Testability | Is each requirement independently verifiable? |
| Feasibility | Is it implementable within the Company Profile? |
| NFR coverage | Are performance / security / compliance needs stated? |
| Scope boundedness | Is in-scope vs out-of-scope explicit? |

Each dimension gets a Red/Amber/Green (or 0–100) score with a one-line justification and, when not Green, a generated follow-up question. Progression to the next stage is **gated** on the aggregate crossing a threshold. The scorecard is shown live in the UI — this is the headline "the AI's thinking is legible" portfolio moment. (Each later stage gets its own rubric, e.g. the spec stage scores interface completeness, data-model coverage, failure handling.)

### 5.2 Impact Analyzer (omnidirectional / consistency)
Triggered when any confirmed artifact changes. Algorithm:
1. Identify the changed node(s).
2. Traverse links to neighbors (both directions).
3. Re-run the relevant rubric checks on each neighbor.
4. Emit a **consistency diff**: which neighboring nodes are now *stale / contradicted / unsupported*, each with a suggested reconciliation.
5. Mark affected downstream stages "needs review" and require human acknowledgement (hybrid model — nothing auto-rewrites silently).

Example: architect swaps a managed SQL datastore for an event-sourced design → analyzer flags the affected ADR, any PRD item that assumed strong consistency, and downstream spec components, proposing edits to each.

---

## 6. Multi-agent architecture

A **blackboard pattern**: specialist agents never talk directly; they read/write the shared Artifact Graph and are routed by an orchestrator.

```
                         ┌──────────────────────────┐
                         │   ORCHESTRATOR / CONDUCTOR │
                         │  • routes by active stage  │
                         │  • enforces gates          │
                         │  • invokes engines         │
                         └─────────────┬─────────────┘
        ┌───────────┬──────────┬───────┴───────┬──────────┬───────────┐
        ▼           ▼          ▼               ▼          ▼           ▼
  Requirements   PRD        Stack          Architect   Planner   (shared services)
   Analyst       Author     Advisor        (spec)                Readiness Engine
                                                                 Impact Analyzer
                                                                 Profile Retriever
        └───────────┴──────────┴───────┬───────┴──────────┴───────────┘
                                        ▼
                        ┌──────────────────────────────┐
                        │   ARTIFACT GRAPH (state store) │  ◄── Company Profile (read-only)
                        └──────────────────────────────┘
```

- **Agents** = LLM (Claude) + a stage-specific system prompt + a small tool surface (read/write its artifact type, query the Profile Retriever, call the Readiness/Impact engines).
- **Orchestrator** owns the state machine (which stage is active, gate status, persona context) and decides which agent runs.
- **Shared services** are deterministic-ish wrappers around LLM calls used by multiple agents (so the rubric logic and impact logic live once, not copy-pasted into five prompts).
- **Profile Retriever** does grounded retrieval over the Company Profile so recommendations cite specific radar/compliance entries.

*(Alternative considered: single stateful orchestrator with stage prompts. Rejected for the portfolio narrative — the "team of named experts" framing is more legible and demos better, at the cost of more moving parts.)*

---

## 7. Company Profile & ADRs (grounding + auditable reasoning)

**Company Profile** (seeded JSON/markdown for the PoC, no admin UI needed):
- **Tech Radar:** entries `{ name, category (lang/framework/datastore/cloud/...), ring: Adopt|Trial|Hold, notes }`.
- **Compliance & Security:** entries `{ id, rule, scope, hard_constraint: bool }` (e.g., "PII must stay in EU region", "no third-party LLM may receive customer data").

**Stack decisions are emitted as ADRs** so the "reasoning" is structured and auditable:
```
ADR-1
  decision:   "Use Postgres (managed) as the primary datastore"
  context:    PRD-2, PRD-5 require relational integrity + audit history
  options:    [Postgres(Adopt), DynamoDB(Trial), MySQL(Hold→excluded)]
  chosen:     Postgres
  rationale:  satisfies COMP-3 (EU residency via region pinning); Adopt ring; team-standard
  satisfies:  [PRD-2, PRD-5, COMP-3]
  status:     accepted | superseded-by ADR-x
```

**Constrained-selection rule:** the Stack Advisor must (a) only choose from radar entries, preferring Adopt, justifying any Trial, never Hold; and (b) satisfy every `hard_constraint` compliance rule or explicitly surface the conflict. A chosen technology not in the radar is a validation error, not a suggestion.

---

## 8. Data model (artifact schemas, sketch)

```
Requirement   { id, statement, type: functional|nfr, source_turn, status,
                readiness: {dimension: score}, linked_prd: [PRD-id], open_questions: [] }
PRDItem       { id, title, description, acceptance_criteria: [], priority,
                linked_requirements: [REQ-id], status }
ADR           { id, decision, context, options, chosen, rationale,
                satisfies: [PRD-id|COMP-id], radar_refs: [], status }
SpecComponent { id, name, responsibility, tech_refs: [ADR-id], interfaces: [],
                data: {}, linked_prd: [PRD-id], risks: [] }
Task          { id, title, epic, estimate, depends_on: [TASK-id],
                linked_spec: [SPEC-id] }
```
Every node also carries `version`, `created_by_agent`, `last_changed`, and a `stale` flag set by the Impact Analyzer. Versioning gives the audit trail and powers "needs review" after reopening.

---

## 9. UX narrative (the demo walkthrough)

1. **Project dashboard** — pick/seed a Company Profile, start a new project, see the five-stage progress rail.
2. **Stage 1 — Requirements chat.** Split view: conversation on the left, **live readiness scorecard** on the right (dimensions turning amber→green as gaps close). The "Advance" button is disabled until the gate passes — the single most important visual.
3. **Stage 2 — PRD review.** AI-drafted PRD with each item showing its source requirement links; inline edit + confirm.
4. **Stage 3 — Stack decision.** ADR cards, each with rationale and **radar/compliance badges**; architect can hit "challenge this" to reopen a back-and-forth.
5. **Stage 4 — Spec workspace.** Architect chat + structured spec editor; when an edit ripples, an **impact panel** lists stale/contradicted nodes with suggested reconciliations to accept/reject.
6. **Stage 5 — Task board.** Epics → tasks with estimates and dependency links back to spec components.

---

## 10. Risks, failure modes, mitigations

| Risk | Mitigation in the design |
|------|--------------------------|
| LLM recommends tech outside the radar / hallucinated libs | Constrained generation + validation that `chosen ∈ radar`; reject + regenerate |
| Consistency drift after many edits | Impact Analyzer + `stale` flags + "needs review" gates; nothing auto-rewrites silently |
| Endless requirements chat | Readiness rubric gives a concrete finish line; agent asks only gap-closing questions |
| Ungrounded "reasoning" that sounds plausible but is generic | ADRs must cite specific PRD/COMP/radar IDs; un-cited decisions flagged |
| Demo feels like four chatbots | Single Artifact Graph + visible traceability links across stages |
| Scope creep toward real implementation | Explicitly bounded at task plan; no codegen in v1 |

---

## 11. Open questions / candidate next deep-dives
- Exact rubric dimensions + scoring math per stage (esp. stages 3–5).
- Impact-analyzer reconciliation UX: auto-suggest vs. require manual edit.
- ADR granularity (one big ADR vs. one per decision) and how the architect "challenges" them.
- Task-plan depth in stage 5 (epics only? estimates? dependency graph? Gantt?).
- Whether the Company Profile is fixed per-demo or swappable to show the same request yielding different stacks (a *very* strong demo move).
- How conversation history is summarized/grounded so later stages "remember" stage-1 nuance.

---

## 12. Verification (how we validate the *design*, since nothing is built)
- **Walkthrough script:** write one sample Company Profile + one vague business request, then trace by hand the artifacts each stage should produce and confirm every node links correctly end-to-end.
- **Gate test (paper):** craft a deliberately vague requirement and confirm the readiness rubric would hold it at the gate with the right follow-up questions.
- **Impact test (paper):** make a stage-4 stack change and confirm the analyzer's traversal flags the correct upstream PRD/ADR nodes.
- **Constraint test (paper):** confirm a request that would naturally want a Hold-ring technology gets redirected to an Adopt alternative with a compliant ADR.
- **Demo acceptance:** the "swap the Company Profile, same request → different justified stack" scenario produces visibly different, internally-consistent ADRs.

---

# Deep dives

## 13. Deep dive — Readiness & Impact engines

Both are built on **one shared primitive: a Graph Consistency Checker** that takes (a node or pair of linked nodes) + (a rubric/edge-semantics) and returns a structured verdict with evidence. The Readiness Engine runs it *forward and within a stage*; the Impact Analyzer runs it *across edges after a change*.

### 13.1 How a single dimension is scored (stable, legible)
Free-form "rate this 0–100" is unstable. Instead each dimension uses an **anchored 4-level scale** with explicit descriptors, and the LLM must return structured output:

```
DimensionScore {
  dimension: "testability",
  level: 0|1|2|3,            // Red | Amber | Amber+ | Green, with fixed anchor text per level
  evidence: [REQ-2, REQ-7],  // node IDs / turn refs supporting the score
  justification: "REQ-2 has no measurable acceptance condition",
  followup_question?: "How will we know the export feature is 'fast enough'?"  // present unless level 3
}
```
Anchors example (testability): L0 = "no requirement is verifiable"; L1 = "some are"; L2 = "most are, a few vague"; L3 = "every requirement has a checkable condition". Anchors make scores reproducible and explainable. Scoring agents run at low temperature.

### 13.2 Per-stage rubrics (gate criteria)
Each stage has **hard** dimensions (must be Green to advance) and **soft** dimensions (contribute to a weighted aggregate ≥ threshold).

| Stage | Hard dimensions | Soft dimensions |
|-------|-----------------|-----------------|
| 1 Requirements | Clarity, Testability, Scope boundedness | Completeness, Feasibility, NFR coverage, Success-metric measurability |
| 2 PRD | Traceability (every PRD item ↔ ≥1 req; every req covered) | Acceptance-criteria quality, Prioritization sanity, Internal non-contradiction |
| 3 Stack/ADR | Radar-compliance (all chosen ∈ radar, no Hold), Compliance-satisfaction (all hard constraints met) | Decision coverage (every significant capability has a supporting decision), Rationale grounding, Risk acknowledgement |
| 4 Tech Spec | Component coverage (every PRD item → ≥1 component), ADR alignment | Interface completeness, Data-model coverage, Failure/edge handling, NFR realization |
| 5 Task plan | Decomposition completeness (every component → ≥1 task), Dependency acyclicity | Estimate presence, Sizing sanity, Critical-path identified |

Gate rule: `advance == all(hard == Green) AND weighted_soft ≥ threshold`. The UI shows hard dimensions as the literal blockers.

### 13.3 The requirements conversation loop (stage 1)
```
loop:
  user message → Requirements Analyst extracts/updates Requirement nodes
  → Readiness Engine re-scores all dimensions (incremental: only changed nodes)
  → for each non-Green dimension, surface its followup_question
  → render live scorecard; enable "Advance" only when gate passes
```
The agent asks **only gap-closing questions** (driven by the lowest-scoring dimensions), which is what gives the chat a finish line instead of meandering.

### 13.4 Impact Analyzer — edges, traversal, verdicts
Typed edges in the graph:

| Edge | From → To | Meaning |
|------|-----------|---------|
| derives_from | PRD → Requirement | PRD item came from this requirement |
| satisfies | ADR → PRD / COMP | this decision satisfies a need/constraint |
| realizes | SpecComponent → PRD | component implements this PRD item |
| constrains | Profile entry → ADR | radar/compliance entry bounding the decision |
| implements | Task → SpecComponent | task builds this component |

Trigger: a **confirmed** node changes, or a stage is reopened. Algorithm:
```
changed = {nodes touched}
frontier = neighbors(changed)            # BFS over typed edges, both directions
for node in frontier:
    verdict = ConsistencyChecker(changed_node, node, edge_semantics)
    # verdict ∈ {valid, stale, contradicted, now_unsupported} + rationale + suggested_patch
    if verdict != valid:
        mark node.stale = true; record in consistency_diff
        if patch accepted later → that becomes a new 'changed' node (next pass)
```
**Cascade control:** re-analyze only nodes whose *content actually changed*; batch all diffs into one review session; cap traversal depth and require human acknowledgement between passes (hybrid model → nothing silently auto-rewrites).

### 13.5 Reconciliation UX
Each `consistency_diff` item offers three actions:
- **Accept suggested patch** → the *owning agent* applies it (the analyzer proposes; agents write — see §15.3), which may open a follow-up pass.
- **Edit manually** → operator writes the fix; node un-stales on re-check.
- **Dismiss** (requires a reason) → records an accepted-inconsistency note so the audit trail stays honest.

Downstream stages with any stale node are flagged **"needs review"** and their gate re-locks until cleared.

---

## 14. Deep dive — Stack Advisor + ADR logic

### 14.1 Pipeline (constrained generation, not free opinion)
```
1. Decision decomposition  → from the PRD, derive the set of decision points the system needs
                             (datastore, backend runtime, frontend, auth, hosting, async/messaging, ...).
                             This list makes "decision coverage" measurable.
2. Candidate generation    → per decision point, candidates = radar entries of that category.
3. Ring filter             → drop Hold; rank Adopt > Trial.
4. Compliance gate         → eliminate candidates violating any hard_constraint; note soft conflicts.
5. Selection + ADR author  → choose, write ADR with mandatory citations.
6. Cross-decision coherence→ mini impact pass: do the choices compose? (ORM supports DB, hosting supports runtime…)
```

### 14.2 Ring & gap handling (the interesting edge cases)
- **Adopt** → default, no caveat needed.
- **Trial** → allowed, but the ADR *must* include a caveat + a named Adopt fallback + a risk note; flagged amber in UI.
- **Hold** → excluded. If the PRD essentially *demands* a Hold technology, the Advisor does **not** silently violate — it raises a **conflict escalation** to the architect ("PRD-7 implies real-time collaboration, which our radar only supports via [Hold] tech X; options: relax requirement, accept off-radar exception, or rescope").
- **Profile gap** (no radar entry covers a needed category) → raise a *profile gap*: architect picks nearest category, accepts a logged off-radar exception, or amends the profile.

This escalation behavior is a key "feels like a real architect" signal — it negotiates constraints rather than rubber-stamping.

### 14.3 ADR granularity & sets
**One ADR per decision point** (atomic, individually supersedable) grouped into a *Stack Decision Record set*. Atomicity is what lets the Impact Analyzer flag exactly which decision a later change invalidates. Superseding keeps history: `ADR-3 status: superseded-by ADR-9`.

ADR template (fields are mandatory → forces grounding):
```
decision · context(PRD/COMP ids) · options_considered(with rings) ·
chosen · rationale(cites ids) · satisfies(ids) · risks · status
```

### 14.4 The architect "challenge" flow (same co-edit loop as the spec)
```
architect selects ADR-n, states objection in natural language
→ Stack Advisor reopens *only that decision point*
→ re-run candidate gen with the new preference/constraint folded in
→ emit a superseding ADR-m (ADR-n → superseded-by ADR-m)
→ run cross-decision coherence + Impact Analyzer (may flag spec/PRD nodes)
→ architect confirms; affected downstream marked needs-review
```
So stages 3 and 4 share one mechanism: *NL objection → scoped regeneration → superseding artifact → consistency sweep*.

---

## 15. Deep dive — Agent orchestration internals

### 15.1 State machine & project state
```
ProjectState {
  current_stage, persona,                 // persona ∈ {business_user, tech_architect}
  gate_status: {stage: locked|passed|needs_review},
  graph_ref, threads: {stage: conversation},
  project_brief                            // rolling summary injected into every agent (see 15.4)
}
```
States = the five stages. Forward transitions guarded by gates (§13.2). **Reopen** transitions allowed (hybrid model) and set downstream `needs_review`. The orchestrator also enforces *persona/stage validity* — e.g., architect-only actions are rejected in stages 1–2.

### 15.2 Orchestrator (Conductor) responsibilities
- Route each user message to the active stage's agent given current persona.
- Invoke the **Readiness Engine** on demand during a stage; invoke the **Impact Analyzer** after any confirmed edit or reopen.
- Manage gate checks and the needs-review propagation.
- Maintain `project_brief` so later agents inherit earlier nuance.

### 15.3 Blackboard protocol (the critical design rule)
Agents read a **scoped view** (their inputs) and write **only their own artifact type**. They never directly edit another stage's nodes. Cross-stage changes flow as **proposed patches** through the Impact Analyzer → human ack → the *owning* agent applies them.

> Example: in stage 4 the Architect agent wants a PRD tweak. It does **not** edit the PRD. It emits a proposed PRD change → impact review → on accept, the **PRD Author** applies it. This keeps each artifact single-writer and the audit trail clean, and prevents agents from trampling each other's work.

### 15.4 Agent anatomy & tool surfaces
Every agent = Claude + role system prompt (incl. its rubric awareness) + a small tool surface + a scratchpad.

| Agent | Reads | Writes | Key tools |
|-------|-------|--------|-----------|
| Requirements Analyst | profile, thread | Requirement | `query_profile`, `upsert_requirement`, `run_readiness`, `ask_followup` |
| PRD Author | requirements | PRDItem | `read_requirements`, `upsert_prd`, `run_readiness` |
| Stack Advisor | PRD, profile | ADR | `query_profile`, `decompose_decisions`, `upsert_adr`, `run_coherence`, `escalate_conflict` |
| Architect | PRD, ADR | SpecComponent + ADR (via supersede) | `read_prd`, `read_adr`, `upsert_spec`, `propose_adr_change`, `run_impact` |
| Planner | spec | Task | `read_spec`, `upsert_task`, `check_dependency_cycles` |
| (shared) | — | — | Readiness Engine, Impact Analyzer, Profile Retriever |

### 15.5 Memory & grounding
- **Per-stage threads** hold the live conversation; the orchestrator maintains a compact **project_brief** (decisions + key constraints + stage-1 nuance) injected into every agent so context survives stage transitions without dumping full transcripts.
- All agents **cite node IDs** in their outputs; un-cited downstream artifacts are consistency defects (§3). This is the anti-hallucination backbone.

### 15.6 Sequence sketches
```
Stage-1 turn:
  User(business) → Conductor → Requirements Analyst → upsert Requirement(s)
                 → Conductor → Readiness Engine (rescore) → scorecard + followups → UI

Stage-4 edit that ripples:
  User(architect) → Conductor → Architect agent → upsert SpecComponent
                  → Conductor → Impact Analyzer (BFS) → consistency_diff
                  → UI review session → on accept → owning agent applies patch → re-check
```

### 15.7 Concurrency & tech note
PoC is single-operator → interactions are sequential, so no multi-writer concurrency is needed (a real multi-user version would add locking/optimistic-versioning on nodes). All agents are the **same Claude model** differentiated by system prompt + tools; scoring/analyzer calls run at low temperature with structured outputs for stability.
