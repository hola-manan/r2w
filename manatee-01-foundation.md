# P01 — Foundation & Shared Contracts

> Part of the **AI-Powered SDLC Companion** plan set. Master index: `i-have-a-big-sparkling-manatee.md`. This plan is the **source of truth** every later plan imports — get the shapes right here and the rest stay consistent.

## Context
Greenfield. Before any logic exists we fix the monorepo layout, the artifact/edge schemas, the node-ID envelope, the LLM access wrapper, and the DB session. Plans P02–P10 reference these and never redefine them.

## Depends on
Nothing.

## Produces (contracts owned here)
- Pydantic **artifact schemas** (Requirement, PRDItem, ADR, SpecComponent, Task) + common envelope.
- **Node-ID conventions** and **enums** (`DocumentType`, `EdgeType`).
- **LLM client wrapper** (`complete`, `structured`).
- **DB engine/session** factory.

## Scope / tasks
1. **Monorepo scaffold**
   - `backend/` — FastAPI app managed with `uv` (or poetry); `pyproject.toml`, `ruff`, `pytest`.
   - `frontend/` — Vite + React + TypeScript + Tailwind (created here, fleshed out in P08).
   - Root `README` stub (filled in P10), `.gitignore`, `.env.example` (Anthropic key, DB path, model id).
2. **Artifact schemas** — `app/schemas/artifacts.py` per design §8:
   ```python
   class Envelope(BaseModel):
       id: str                      # prefixed: REQ-/PRD-/ADR-/SPEC-/TASK-/COMP-
       project_id: str
       version: int = 1
       created_by_agent: str | None = None
       last_changed: datetime
       stale: bool = False

   class Requirement(Envelope):     # statement, type: Literal["functional","nfr"],
                                    # source_turn, status, readiness: dict[str,int],
                                    # linked_prd: list[str], open_questions: list[str]
   class PRDItem(Envelope):         # title, description, acceptance_criteria: list[str],
                                    # priority, linked_requirements: list[str], status
   class ADR(Envelope):             # decision, context: list[str], options: list[Option],
                                    # chosen, rationale, satisfies: list[str],
                                    # radar_refs: list[str], risks: list[str], status
   class SpecComponent(Envelope):   # name, responsibility, tech_refs: list[str],
                                    # interfaces: list, data: dict, linked_prd: list[str], risks
   class Task(Envelope):            # title, epic, estimate, depends_on: list[str],
                                    # linked_spec: list[str]
   ```
3. **Enums & ID helpers** — `app/schemas/enums.py`: `DocumentType`, `EdgeType` (`derives_from, satisfies, realizes, constrains, implements`), `Ring` (`Adopt, Trial, Hold`), `GateStatus` (`locked, passed, needs_review`), `Persona`. `app/schemas/ids.py`: `new_id(DocumentType, project_id)`.
4. **LLM wrapper** — `app/llm/client.py`:
   - `complete(messages, *, temperature, system) -> str`
   - `structured(messages, schema: type[T], *, temperature=0, system) -> T` — uses tool/JSON mode, validates against the Pydantic `schema`, retries on validation failure (capped).
   - Config: model id from env (default latest Claude), timeout, low-temp default for scoring/analysis.
5. **DB layer** — `app/db/base.py` (declarative base), `app/db/session.py` (engine at `data/project.db`, `get_session()` dependency). PoC uses `create_all`; leave a hook for Alembic.
6. **App entrypoint** — `app/main.py`: FastAPI instance, `/health`, CORS allowing the Vite dev origin, settings via `app/config.py` (pydantic-settings).

## Key files
`backend/pyproject.toml`, `backend/app/{main,config}.py`, `backend/app/schemas/{artifacts,enums,ids}.py`, `backend/app/llm/client.py`, `backend/app/db/{base,session}.py`, `frontend/` skeleton.

## Verification
- `pytest`: each artifact schema round-trips (build → `model_dump` → rebuild); `new_id` produces correct prefixes.
- `uvicorn app.main:app` boots; `GET /health` → 200.
- `structured()` returns a validated sample `DimensionScore`-like object from a canned prompt (mock or live).
- `npm run dev` in `frontend/` serves the Vite skeleton.

## Consistency notes
Do **not** add persistence logic, traversal, or any agent/engine code here. This plan only fixes shapes + plumbing. Edge semantics and rubric data live in P02/P04.
