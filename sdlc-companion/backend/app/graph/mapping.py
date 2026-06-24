"""ORM <-> Pydantic mapping (P02).

Centralizes payload typing so node serialization is identical everywhere.
"""
from __future__ import annotations

from app.db.models import NodeRow
from app.schemas import ARTIFACT_MODELS, DocumentType, Envelope


def to_model(row: NodeRow) -> Envelope:
    doc_type = DocumentType(row.type)
    model_cls = ARTIFACT_MODELS[doc_type]
    data = dict(row.payload)
    # Scalar columns are authoritative for the envelope fields.
    data.update(
        id=row.id,
        project_id=row.project_id,
        doc_type=doc_type.value,
        version=row.version,
        created_by_agent=row.created_by_agent,
        stale=row.stale,
    )
    return model_cls.model_validate(data)


def payload_of(node: Envelope) -> dict:
    return node.model_dump(mode="json")
