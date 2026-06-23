# P03 — Company Profile & Profile Retriever

> Part of the **AI-Powered SDLC Companion** plan set. Master: `i-have-a-big-sparkling-manatee.md`.

## Context
The Company Profile is the grounding spine (design §7): a tech radar (Adopt/Trial/Hold) and compliance/security constraints. Every stack decision must cite it. This plan loads, serves, and validates against the profile, and supports **swappable** profiles (the "same request → different stack" demo move, §11).

## Depends on
P01 (schemas, enums incl. `Ring`).

## Produces (contract owned here)
`ProfileRetriever` — category/ring lookup, hard-constraint enumeration, citation refs, and the `validate_choice` helpers reused by the Stack Advisor (P06) and the Stack rubric (P04).

## Scope / tasks
1. **Profile schema** — `app/profile/schema.py`:
   ```python
   class RadarEntry(BaseModel):   name; category: str; ring: Ring; notes: str
   class ComplianceRule(BaseModel): id: str; rule: str; scope: str; hard_constraint: bool
   class CompanyProfile(BaseModel): id: str; name: str;
                                    radar: list[RadarEntry]; compliance: list[ComplianceRule]
   ```
2. **Loader** — `app/profile/loader.py`: load `CompanyProfile` from `data/profiles/<id>.json`; list available profile ids; cache parsed profiles.
3. **Retriever** — `app/profile/retriever.py`:
   ```python
   class ProfileRetriever:
       def candidates(self, category) -> list[RadarEntry]      # ranked Adopt > Trial, Hold last/excluded
       def hard_constraints(self) -> list[ComplianceRule]
       def lookup(self, name) -> RadarEntry | None
       def citation_refs(self, names) -> list[str]             # radar/COMP ids for ADR grounding
   ```
4. **Validation** — `app/profile/validation.py` (reused by Stack Advisor + Stack rubric):
   - `validate_choice(name) -> {in_radar: bool, ring: Ring|None}` — off-radar = error, not suggestion.
   - `check_hold(name)` and `check_constraints(decision_context)` helpers.
5. **Seed profiles** — `data/profiles/`: at least two contrasting profiles (e.g., "EU-regulated fintech" vs "startup web") so the swap demo yields different stacks.

## Key files
`backend/app/profile/{schema,loader,retriever,validation}.py`, `backend/data/profiles/*.json`.

## Verification (pytest)
- Load a seed profile; `candidates("datastore")` returns ring-ranked entries with Hold excluded/last.
- `validate_choice` flags an off-radar tech and a Hold tech correctly.
- `hard_constraints()` returns only `hard_constraint=true` rules.
- Two profiles load by id and differ in radar contents.

## Consistency notes
This is the **only** place radar/compliance logic lives. The Stack Advisor must call these helpers rather than re-implementing ring/compliance reasoning in its prompt.
