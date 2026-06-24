"""Node-ID conventions (P01 contract).

Human-legible, prefixed, per-project sequential IDs (REQ-1, PRD-2, ADR-3, ...).
The graph repository (P02) owns sequence allocation; this module only defines
the prefix mapping and formatting so IDs look identical everywhere.

Note: `COMP-*` IDs refer to compliance entries in the Company Profile (P03),
not graph nodes; they appear in ADR `satisfies` / `context` references.
"""
from __future__ import annotations

from .enums import DocumentType

PREFIXES: dict[DocumentType, str] = {
    DocumentType.REQUIREMENT: "REQ",
    DocumentType.PRD_ITEM: "PRD",
    DocumentType.ADR: "ADR",
    DocumentType.SPEC_COMPONENT: "SPEC",
    DocumentType.TASK: "TASK",
}


def prefix_for(doc_type: DocumentType) -> str:
    return PREFIXES[doc_type]


def format_id(doc_type: DocumentType, seq: int) -> str:
    return f"{prefix_for(doc_type)}-{seq}"
