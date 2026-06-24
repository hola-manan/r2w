"""Profile Retriever (P03 contract).

Grounded retrieval over a Company Profile so recommendations cite specific
radar / compliance entries. Used by the Stack Advisor (P06) and the Stack
rubric (P04). This is the ONLY place radar/compliance ranking logic lives.
"""
from __future__ import annotations

from app.profile.schema import CompanyProfile, ComplianceRule, RadarEntry
from app.schemas import Ring

_RING_RANK = {Ring.ADOPT: 0, Ring.TRIAL: 1, Ring.HOLD: 2}


class ProfileRetriever:
    def __init__(self, profile: CompanyProfile) -> None:
        self.profile = profile

    # ----- radar ----------------------------------------------------------
    def categories(self) -> list[str]:
        return sorted({e.category for e in self.profile.radar})

    def candidates(self, category: str, *, include_hold: bool = False) -> list[RadarEntry]:
        """Radar entries for a category, ranked Adopt > Trial (Hold excluded by default)."""
        entries = [e for e in self.profile.radar if e.category == category]
        if not include_hold:
            entries = [e for e in entries if e.ring != Ring.HOLD]
        return sorted(entries, key=lambda e: (_RING_RANK[e.ring], e.name.lower()))

    def lookup(self, name: str) -> RadarEntry | None:
        for e in self.profile.radar:
            if e.name.lower() == name.lower():
                return e
        return None

    # ----- compliance -----------------------------------------------------
    def hard_constraints(self) -> list[ComplianceRule]:
        return [c for c in self.profile.compliance if c.hard_constraint]

    def compliance(self, comp_id: str) -> ComplianceRule | None:
        for c in self.profile.compliance:
            if c.id.lower() == comp_id.lower():
                return c
        return None

    # ----- grounding ------------------------------------------------------
    def citation_refs(self, names: list[str]) -> list[str]:
        """Return canonical radar names / COMP ids that actually exist in the profile."""
        refs: list[str] = []
        for n in names:
            entry = self.lookup(n)
            if entry:
                refs.append(entry.name)
                continue
            comp = self.compliance(n)
            if comp:
                refs.append(comp.id)
        return refs

    def summary(self) -> str:
        """Compact text the Stack Advisor can ground against."""
        lines = [f"Company Profile: {self.profile.name} (id={self.profile.id})", "Tech radar:"]
        for cat in self.categories():
            entries = ", ".join(
                f"{e.name}[{e.ring.value}]" for e in self.candidates(cat, include_hold=True)
            )
            lines.append(f"  - {cat}: {entries}")
        lines.append("Compliance:")
        for c in self.profile.compliance:
            tag = "HARD" if c.hard_constraint else "soft"
            lines.append(f"  - {c.id} ({tag}): {c.rule}")
        return "\n".join(lines)
