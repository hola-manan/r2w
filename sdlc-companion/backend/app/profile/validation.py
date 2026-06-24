"""Profile validation helpers (P03 contract).

Reused by the Stack Advisor (P06) and the Stack/ADR rubric (P04). A chosen
technology not on the radar is a validation error, not a suggestion (design §7).
"""
from __future__ import annotations

from pydantic import BaseModel

from app.profile.retriever import ProfileRetriever
from app.schemas import Ring


class ChoiceCheck(BaseModel):
    name: str
    in_radar: bool
    ring: Ring | None = None
    allowed: bool  # adopt/trial allowed; hold or off-radar not
    reason: str = ""


def validate_choice(retriever: ProfileRetriever, name: str) -> ChoiceCheck:
    entry = retriever.lookup(name)
    if entry is None:
        return ChoiceCheck(
            name=name,
            in_radar=False,
            ring=None,
            allowed=False,
            reason=f"'{name}' is not in the tech radar (off-radar exception required)",
        )
    if entry.ring == Ring.HOLD:
        return ChoiceCheck(
            name=name,
            in_radar=True,
            ring=Ring.HOLD,
            allowed=False,
            reason=f"'{name}' is ring=Hold and is blocked",
        )
    reason = "Adopt: default choice" if entry.ring == Ring.ADOPT else (
        "Trial: allowed with a caveat + named Adopt fallback + risk note"
    )
    return ChoiceCheck(
        name=name, in_radar=True, ring=entry.ring, allowed=True, reason=reason
    )


def check_hold(retriever: ProfileRetriever, name: str) -> bool:
    entry = retriever.lookup(name)
    return entry is not None and entry.ring == Ring.HOLD


def check_constraints(retriever: ProfileRetriever, satisfied_ids: list[str]) -> list[str]:
    """Return hard-constraint COMP ids NOT covered by `satisfied_ids`."""
    satisfied = {s.lower() for s in satisfied_ids}
    return [c.id for c in retriever.hard_constraints() if c.id.lower() not in satisfied]
