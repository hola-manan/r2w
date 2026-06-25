"""Graph enums (P01 contract). Defined once, imported everywhere."""
from __future__ import annotations

from enum import Enum


class DocumentType(str, Enum):
    REQUIREMENT = "requirement"
    PRD_ITEM = "prd_item"
    ADR = "adr"
    SPEC_COMPONENT = "spec_component"
    TASK = "task"


class EdgeType(str, Enum):
    # PRD item -> Requirement
    DERIVES_FROM = "derives_from"
    # ADR -> PRD / COMP
    SATISFIES = "satisfies"
    # SpecComponent -> PRD
    REALIZES = "realizes"
    # Profile entry -> ADR
    CONSTRAINS = "constrains"
    # Task -> SpecComponent
    IMPLEMENTS = "implements"
    # SpecComponent -> ADR (component depends on a stack decision)
    DEPENDS_ON = "depends_on"


class Ring(str, Enum):
    ADOPT = "adopt"
    TRIAL = "trial"
    HOLD = "hold"


class GateStatus(str, Enum):
    LOCKED = "locked"
    PASSED = "passed"
    NEEDS_REVIEW = "needs_review"


class Persona(str, Enum):
    BUSINESS_USER = "business_user"
    TECH_ARCHITECT = "tech_architect"
