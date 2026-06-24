"""Per-edge consistency invariants (P04). What the checker enforces across each edge."""
from __future__ import annotations

from app.schemas import EdgeType

EDGE_MEANING: dict[EdgeType, str] = {
    EdgeType.DERIVES_FROM: (
        "A PRD item derives from a requirement: the PRD item must still faithfully "
        "reflect the requirement's intent."
    ),
    EdgeType.SATISFIES: (
        "An ADR satisfies a PRD item / compliance rule: the decision must still "
        "fulfill that need or constraint."
    ),
    EdgeType.REALIZES: (
        "A spec component realizes a PRD item (and uses ADR choices): the component "
        "must still implement the PRD item under the current decisions."
    ),
    EdgeType.CONSTRAINS: (
        "A profile entry constrains an ADR: the decision must still respect that "
        "radar/compliance entry."
    ),
    EdgeType.IMPLEMENTS: (
        "A task implements a spec component: the task must still build the component "
        "as specified."
    ),
}
