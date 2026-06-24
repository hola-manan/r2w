"""Shared schema contracts (P01).

Everything downstream imports these — they are the single source of truth for
artifact shapes, node-ID conventions, and graph enums.
"""
from .enums import DocumentType, EdgeType, GateStatus, Persona, Ring
from .ids import PREFIXES, format_id, prefix_for
from .artifacts import (
    ADR,
    ADROption,
    ARTIFACT_MODELS,
    Envelope,
    PRDItem,
    Requirement,
    SpecComponent,
    Task,
)

__all__ = [
    "DocumentType",
    "EdgeType",
    "GateStatus",
    "Persona",
    "Ring",
    "PREFIXES",
    "format_id",
    "prefix_for",
    "Envelope",
    "Requirement",
    "PRDItem",
    "ADR",
    "ADROption",
    "SpecComponent",
    "Task",
    "ARTIFACT_MODELS",
]
