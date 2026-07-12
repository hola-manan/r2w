# `app/tech` — Team Tech Capability Catalog + task→tool matching

A **self-contained** feature: each team tool (Alteryx, UiPath, Power Apps) has its own
**capability doc**, and the Stack Advisor gets an **explicit, per-task fit ranking** of those
tools so the AI picks the right one for the job — and cites it in a normal ADR.

Everything the feature needs lives in this one folder (code **and** the docs). To add a
tool, drop a 4th markdown file in `docs/`; it is auto-discovered.

```
app/tech/
  schema.py    TechCapability, TechMatch, TechMatchOutput
  catalog.py   doc loader + front-matter parser; TechCatalog; catalog_entry()
  matcher.py   TechMatcher + rank_tools() -> Ranking  (best-effort; never raises)
  docs/        alteryx.md, uipath.md, powerapps.md  (front-matter + capability body)
  README.md    this file
```

## How it plugs in — the TWO seams

This feature is deliberately isolated. It reaches into the host app through exactly two
small edits. Porting it to a differently-structured copy = re-create these two seams
wherever the equivalent logic lives.

### Seam 1 — make catalog tools valid tech choices
**Where:** the function that resolves a technology *name* to a radar entry — here
`ProfileRetriever.lookup()` in `app/profile/retriever.py`.
**What:** after the profile radar misses, fall back to the catalog.

```python
# --- app.tech catalog fallback (team capability tools) ---
from app.tech import catalog_entry
return catalog_entry(name)          # None if not a catalog tool either
```

`catalog_entry` returns a real `RadarEntry` with `ring=adopt`, so every consumer of
`lookup()` — the advisor's `validate_choice`, ADR `radar_refs` grounding, and the
deterministic `radar_compliance` gate — treats a catalog tool exactly like an Adopt radar
entry. No other file needs to know the catalog exists. (Profile radar names win on any
name collision, since the radar is checked first.)

### Seam 2 — run the matching step and show it
**Where:** the agent that authors stack decisions — here `StackAdvisor.handle()` in
`app/agents/stack_advisor.py`.
**What:** rank the tools *before* generation (so the choice is informed) and prepend the
rendered ranking to the reply (so it's visible).

```python
from app import tech
task = f"{render_type(ctx.repo, DocumentType.PRD_ITEM)}\nUser: {ctx.message}"
ranking = tech.rank_tools(self.llm, task)         # empty Ranking on no catalog / any error
out = self._generate(StackAdvisorOutput,
                     self._prompt(ctx, extra=ranking.prompt_block),
                     self._system(ROLE, ctx.project_brief))
result = self._apply(ctx, out)
result.reply = ranking.reply_block + result.reply
return result
```

Also append one line to the advisor's role prompt: *prefer the top-ranked team tool when the
task needs data-prep / RPA / low-code-app capability, else choose from the radar as before.*

## Best-effort by design
`rank_tools` returns an **empty `Ranking`** if the catalog folder is missing or the matcher
LLM call fails for any reason. An empty ranking renders nothing and injects nothing, so the
advisor behaves exactly as it did before this feature existed. That is why adding the feature
requires **no changes to existing tests or flows**.

## Optional upgrade (not included)
To surface the ranking as a structured API field + UI panel instead of reply text, add a
`tech_matches` field to the agent result and thread it through the turn response / WebSocket
event / frontend. Left out here to keep the footprint to the two seams above.
