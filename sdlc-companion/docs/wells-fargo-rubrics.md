# Wells Fargo Rubrics — Stage 1 (Clarification) & Stage 3 (ADR)

> **Status:** living working doc. Fill in the Wells Fargo tables below with the
> rubrics you want; leave `TBD` where you're unsure and we'll resolve it together
> in **§6 Gaps & Considerations**. Nothing here is wired into code yet — this doc
> is the source we'll transcribe into `sdlc-companion/backend/app/engines/rubrics.py`
> (and, where needed, `structural.py` / a Wells Fargo Company Profile) in a later step.

---

## 1. Purpose & scope

`r2w` gates each pipeline stage on a rubric of scored **metrics** (dimensions).
We're making the metrics for **two stages** reflect Wells Fargo's priorities as a
large, regulated US bank:

- **Stage 1 — Requirements / Clarification.** Drives the gap-closing follow-up
  questions the Requirements Analyst asks. Reworking these dimensions changes
  *what the assistant clarifies* with a business user.
- **Stage 3 — Stack / ADR.** Scores the Architecture Decision Records. Reworking
  these dimensions changes *what makes a stack decision "ready."*

**Out of scope for this doc:** Stages 2 (PRD), 4 (Tech Spec), 5 (Tasks). The
existing demo profiles (`eu-fintech`, `startup-web`) are **kept as-is**.

---

## 2. Rubric anatomy (so entries map straight into code)

Each metric is a `Dimension`; a stage's `Rubric` groups them into **hard** and
**soft**. Fields you need to provide per dimension:

| Field | Meaning | Notes |
|---|---|---|
| `key` | snake_case identifier | stable; cited nowhere user-facing, but don't churn it |
| `name` | display name | shown on the scorecard |
| `question` | the single yes/no-ish scoring question | what the scorer/agent optimizes |
| kind | `hard` or `soft` | **hard** = must reach L3 (green) or the gate is blocked; **soft** = weighted, contributes to the aggregate |
| weight | soft dims only | relative float, e.g. `1.0`, `0.5` |
| `deterministic` | name of a structural checker, or blank | blank ⇒ LLM scores it at temp 0; set ⇒ code scores it (reproducible, needs a checker in `structural.py`) |
| anchors | the 0–3 scale | L0 = worst … L3 = best; **L3 is the "green" bar** |

Stage-level: **`threshold`** = the weighted-soft score (0–1) required to pass,
currently `0.6` for every stage.

**Gate rule (unchanged):** `gate_passed = (all hard dims at L3) AND (weighted soft ≥ threshold)`.

> Anchor-writing tip: keep L0/L1/L2/L3 as observable states ("none / few / most /
> all"), not adjectives. The LLM and the agent both read these verbatim.

---

## 3. Baseline — current rubrics (reference / starting point)

Transcribed from `engines/rubrics.py`. Use these as the diff base: keep, edit, or
replace each row.

### Stage 1 — Requirements (current)

| key | name | kind | weight | det? | L0 | L1 | L2 | L3 |
|---|---|---|---|---|---|---|---|---|
| `clarity` | Clarity | hard | — | — | nothing is defined | some terms defined | most defined, a few vague | all entities/terms unambiguous |
| `testability` | Testability | hard | — | — | no requirement is verifiable | some are | most are, a few vague | every requirement has a checkable condition |
| `scope_boundedness` | Scope boundedness | hard | — | — | no scope stated | vague scope | scope mostly clear | in/out of scope explicit |
| `completeness` | Completeness | soft | 1.0 | — | none | few | most | personas + flows + edge cases present |
| `feasibility` | Feasibility | soft | 1.0 | — | clearly infeasible | doubtful | mostly feasible | feasible within profile |
| `nfr_coverage` | NFR coverage | soft | 1.0 | — | none | few | most | perf/security/compliance all stated |
| `success_metrics` | Success-metric measurability | soft | 1.0 | — | none | vague | some measurable | clear measurable success metrics |

Stage 1 threshold: **0.6**.

### Stage 3 — Stack / ADR (current)

| key | name | kind | weight | det? | L0 | L1 | L2 | L3 |
|---|---|---|---|---|---|---|---|---|
| `radar_compliance` | Radar-compliance | hard | — | `radar_compliance` | none on radar | some off-radar/Hold | one off-radar/Hold | all on radar, no Hold |
| `compliance_satisfaction` | Compliance-satisfaction | hard | — | `compliance_satisfaction` | none satisfied | few | most | all hard constraints satisfied |
| `decision_coverage` | Decision coverage | soft | 1.0 | — | none | few | most | every capability has a decision |
| `rationale_grounding` | Rationale grounding | soft | 1.0 | — | ungrounded | weakly cited | mostly cited | all rationales cite IDs |
| `risk_ack` | Risk acknowledgement | soft | 0.5 | — | none | few | most | risks acknowledged where relevant |

Stage 3 threshold: **0.6**.

> Note: the two Stage 3 **hard** dims are **deterministic** and driven by the
> **Company Profile** (tech radar + compliance rules). Making them
> Wells-Fargo-specific ultimately means authoring a WF profile
> (`data/profiles/wells-fargo.json`) — flagged in §6, not built here.

---

## 4. Wells Fargo rubric — Stage 1 (Clarification)

Fill this in. The seeded rows below are **suggestions** to illustrate the shape —
keep / edit / delete freely. Add as many rows as you like.

| key | name | kind | weight | det? | L0 | L1 | L2 | L3 |
|---|---|---|---|---|---|---|---|---|
| `regulatory_mapping` | Regulatory mapping *(suggested)* | hard | — | — | no regulatory obligations identified | some named | most mapped to requirements | every requirement maps to its governing regulation/control (e.g. SOX, GLBA, PCI-DSS, FFIEC) |
| `data_classification` | Data classification *(suggested)* | hard | — | — | data sensitivity unstated | some data typed | most typed | all data elements classified (Public/Internal/Confidential/Restricted) with handling stated |
| `auditability` | Auditability *(suggested)* | soft | 1.0 | — | no audit needs | vague | most flows covered | every state-changing flow states its audit-trail requirement |
| _TBD_ | _add your dimension_ | _hard/soft_ | _—/weight_ | _—_ | _L0_ | _L1_ | _L2_ | _L3_ |

**Stage 1 threshold:** _TBD (current 0.6)_

**Which baseline dims to keep?** (mark keep/edit/drop)
- `clarity` — _keep / edit / drop_
- `testability` — _keep / edit / drop_
- `scope_boundedness` — _keep / edit / drop_
- `completeness` — _keep / edit / drop_
- `feasibility` — _keep / edit / drop_
- `nfr_coverage` — _keep / edit / drop_
- `success_metrics` — _keep / edit / drop_

---

## 5. Wells Fargo rubric — Stage 3 (ADR)

Same as above. Seeded rows are **suggestions**.

| key | name | kind | weight | det? | L0 | L1 | L2 | L3 |
|---|---|---|---|---|---|---|---|---|
| `approved_tech` | Approved-technology compliance *(suggested)* | hard | — | `radar_compliance`* | none on approved list | some off-list | one off-list | all chosen tech is on the Wells Fargo approved/standards list |
| `control_satisfaction` | Control satisfaction *(suggested)* | hard | — | `compliance_satisfaction`* | no controls satisfied | few | most | every applicable mandatory control is satisfied by an ADR |
| `residency_sovereignty` | Data residency / sovereignty *(suggested)* | soft | 1.0 | — | unaddressed | vague | mostly addressed | every data-handling ADR states region/residency & meets policy |
| `resiliency_dr` | Resiliency / DR posture *(suggested)* | soft | 0.75 | — | none | few | most | ADRs state availability tier, RTO/RPO, and failover approach |
| `third_party_risk` | Third-party / vendor risk *(suggested)* | soft | 0.5 | — | none | few | most | external dependencies note vendor-risk tier & exit strategy |
| _TBD_ | _add your dimension_ | _hard/soft_ | _—/weight_ | _—_ | _L0_ | _L1_ | _L2_ | _L3_ |

`*` = reuses/renames an existing deterministic checker. New deterministic dims
need a checker written in `structural.py` **and** the backing data in a WF
Company Profile — see §6.

**Stage 3 threshold:** _TBD (current 0.6)_

**Which baseline dims to keep?** (mark keep/edit/drop)
- `radar_compliance` — _keep / edit / drop_
- `compliance_satisfaction` — _keep / edit / drop_
- `decision_coverage` — _keep / edit / drop_
- `rationale_grounding` — _keep / edit / drop_
- `risk_ack` — _keep / edit / drop_

---

## 6. Gaps & Considerations (to resolve together)

Open questions — annotate inline as you fill §4/§5:

1. **Hard vs soft.** Which WF dimensions are truly gate-blocking (hard, must be
   green) vs. quality signals (soft)? Too many hard dims makes the gate hard to
   ever pass. (Current: Stage 1 = 3 hard, Stage 3 = 2 hard.)
2. **Soft weights & threshold.** Do the default weights and `0.6` threshold still
   fit once WF dims are added, or should specific stages be stricter?
3. **Deterministic vs LLM.** Which WF dims can be checked structurally from the
   graph (reproducible, no LLM) vs. must be LLM-judged? Deterministic dims need a
   function in `structural.py` and something concrete in the graph/profile to
   check against.
4. **Wells Fargo Company Profile.** Stage 3's hard dims read the tech radar +
   compliance rules from a profile. Making them WF-specific implies a
   `data/profiles/wells-fargo.json` (approved tech radar + mandatory controls as
   `COMP-*` rules). Do we build this, and what goes in it? Keeps
   `eu-fintech`/`startup-web` untouched, adds WF alongside.
5. **Regulations in scope.** Which frameworks should the metrics explicitly name
   (SOX, GLBA, PCI-DSS, FFIEC, OCC guidance, internal control catalog)? Naming
   them in anchors makes the follow-up questions concrete.
6. **Agent-prompt ripple.** Rubric text is fed to the Requirements Analyst and
   Stack Advisor via `describe_rubric()`. New dims automatically change what they
   ask/optimize — confirm the resulting follow-up questions read the way WF wants.
7. **Test impact.** `tests/test_engines.py` and `tests/test_agents.py` assert on
   specific dimension keys/levels. New/renamed dims will need those tests updated
   in the implementation step.

---

## 7. Next steps (after this doc is filled)

1. You fill §4 and §5; we resolve §6 together.
2. Transcribe finalized dimensions into `engines/rubrics.py` (`Dimension` +
   `Rubric` entries for stages 1 and 3).
3. Add any new deterministic checkers to `engines/structural.py` and register
   them.
4. If agreed in §6.4, author `data/profiles/wells-fargo.json` and use it as the
   demo/default profile.
5. Update `tests/test_engines.py` / `tests/test_agents.py` for the new keys and
   expected levels; run the backend test suite green.
