"""Company Profile schema (P03 contract). Design doc §7."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas import Ring


class RadarEntry(BaseModel):
    name: str
    category: str  # language | backend_framework | frontend | datastore | cloud | auth | ...
    ring: Ring
    notes: str = ""


class ComplianceRule(BaseModel):
    id: str  # COMP-1, COMP-2, ...
    rule: str
    scope: str = ""
    hard_constraint: bool = True


class CompanyProfile(BaseModel):
    id: str
    name: str
    radar: list[RadarEntry] = Field(default_factory=list)
    compliance: list[ComplianceRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _unique_keys(self) -> "CompanyProfile":
        # The retriever treats radar names and COMP ids as unique keys
        # (lookup / compliance / check_constraints all key on them, case-insensitively),
        # so a duplicate would silently shadow an entry and corrupt grounding.
        names = [e.name.lower() for e in self.radar]
        name_dupes = sorted({n for n in names if names.count(n) > 1})
        if name_dupes:
            raise ValueError(f"duplicate radar entry names: {name_dupes}")
        comp_ids = [c.id.lower() for c in self.compliance]
        id_dupes = sorted({c for c in comp_ids if comp_ids.count(c) > 1})
        if id_dupes:
            raise ValueError(f"duplicate compliance ids: {id_dupes}")
        return self
