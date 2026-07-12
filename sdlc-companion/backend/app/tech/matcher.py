"""Task→tool matcher: the explicit "which team tool fits this task" step.

`rank_tools(llm, task_text)` is the single entry point used by the Stack Advisor
(integration Seam 2). It is **best-effort**: if the catalog is empty or the LLM call fails
for any reason, it returns an empty `Ranking` and the caller proceeds exactly as before —
so the feature can never break an existing flow (and offline tests without a matcher handler
keep passing).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from app.tech.catalog import TechCatalog, load_catalog
from app.tech.schema import TechMatch, TechMatchOutput

log = logging.getLogger(__name__)

_SYSTEM = (
    "You match a software delivery task to the team's automation / low-code tools, using ONLY "
    "the capability docs provided. Score each listed tool 0-100 for how well it fits THIS task, "
    "give a one-line rationale grounded in its documented capabilities, and set recommended=true "
    "for the single best fit only if it genuinely fits (if none fit well, recommend none). "
    "Never invent tools beyond those provided."
)


class TechMatcher:
    """Wraps one `llm.structured` call that scores the catalog against a task."""

    def __init__(self, llm) -> None:
        self.llm = llm

    def match(self, task_text: str, catalog: TechCatalog) -> TechMatchOutput:
        prompt = (
            f"Task (requirements / PRD + latest request):\n{task_text}\n\n"
            f"Team tools (capability docs):\n{catalog.docs_text()}\n\n"
            "Return a fit assessment for every listed tool."
        )
        out = self.llm.structured(
            [{"role": "user", "content": prompt}],
            TechMatchOutput,
            system=_SYSTEM,
            temperature=0.0,
        )
        out.matches.sort(key=lambda m: (-m.score, m.tool_name.lower()))
        return out


@dataclass
class Ranking:
    """Rendered result of a match, with the two text blocks the advisor seam consumes."""

    matches: list[TechMatch] = field(default_factory=list)
    summary: str = ""

    def is_empty(self) -> bool:
        return not self.matches

    @property
    def prompt_block(self) -> str:
        """Injected into the advisor prompt so the LLM's `chosen` is biased by fit."""
        if not self.matches:
            return ""
        lines = [
            "Team automation / low-code tools available for this task, with a per-task fit "
            "score (0-100) and rationale:"
        ]
        for m in self.matches:
            tag = " (recommended)" if m.recommended else ""
            lines.append(f"- {m.tool_name} [{m.score}]{tag}: {m.rationale}")
        lines.append(
            "When a decision point needs a data-prep / RPA / low-code-app capability, prefer the "
            "top-ranked team tool above and set it as `chosen`; otherwise choose from the company "
            "radar as usual.\n"
        )
        return "\n".join(lines)

    @property
    def reply_block(self) -> str:
        """Prepended to the advisor reply so the ranking is visible to the user."""
        if not self.matches:
            return ""
        lines = ["**Team tool fit for this task**"]
        for i, m in enumerate(self.matches, 1):
            tag = " ✓ recommended" if m.recommended else ""
            lines.append(f"{i}. {m.tool_name} — {m.score}/100{tag} — {m.rationale}")
        return "\n".join(lines) + "\n\n"


def rank_tools(llm, task_text: str) -> Ranking:
    """Best-effort task→tool ranking. Returns an empty Ranking on no catalog / any LLM error."""
    catalog = load_catalog()
    if catalog.is_empty():
        return Ranking()
    try:
        out = TechMatcher(llm).match(task_text, catalog)
    except Exception as exc:  # noqa: BLE001 - matching is advisory; never break the stack turn
        log.warning("tech match skipped: %s", exc)
        return Ranking()
    return Ranking(matches=out.matches, summary=out.summary)
