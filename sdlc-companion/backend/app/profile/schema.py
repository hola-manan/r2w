"""Company Profile schema (P03 contract). Design doc §7."""
from __future__ import annotations

from pydantic import BaseModel, Field

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
