"""Graph traversal (P02). BFS over typed edges, used by the Impact Analyzer (P04)."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.schemas import EdgeType, Envelope


@dataclass
class TraversalResult:
    nodes: dict[str, Envelope] = field(default_factory=dict)
    # (from_id, to_id, edge_type) tuples walked during traversal
    path_edges: list[tuple[str, str, EdgeType]] = field(default_factory=list)


def bfs(
    repo,
    start_ids: list[str],
    *,
    direction: str = "both",
    edge_filter: list[EdgeType] | None = None,
    max_depth: int = 3,
) -> TraversalResult:
    """Breadth-first walk from start_ids, excluding the start nodes themselves
    from `nodes` (callers already have those)."""
    result = TraversalResult()
    visited: set[str] = set(start_ids)
    frontier: list[str] = list(start_ids)
    depth = 0

    while frontier and depth < max_depth:
        next_frontier: list[str] = []
        for node_id in frontier:
            for neighbor_id, edge in repo.adjacent(
                node_id, direction=direction, edges=edge_filter
            ):
                result.path_edges.append((node_id, neighbor_id, edge))
                if neighbor_id in visited:
                    continue
                visited.add(neighbor_id)
                node = repo.get_optional(neighbor_id)
                if node is not None:
                    result.nodes[neighbor_id] = node
                    next_frontier.append(neighbor_id)
        frontier = next_frontier
        depth += 1

    return result
