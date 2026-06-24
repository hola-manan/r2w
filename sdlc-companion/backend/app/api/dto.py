"""DTO mapping (P07). The single place P01 schemas become wire shapes.

Nodes expose their links as chips for traceability views.
"""
from __future__ import annotations

from app.graph import GraphRepository
from app.schemas import Envelope


def node_to_dto(repo: GraphRepository, node: Envelope) -> dict:
    out = node.model_dump(mode="json")
    out["links_out"] = [
        {"to": nid, "edge": edge.value}
        for nid, edge in repo.adjacent(node.id, direction="out")
    ]
    out["links_in"] = [
        {"from": nid, "edge": edge.value}
        for nid, edge in repo.adjacent(node.id, direction="in")
    ]
    return out


def graph_dto(repo: GraphRepository) -> dict:
    nodes = [node_to_dto(repo, n) for n in repo.list_all()]
    edges = [
        {"from": e.from_id, "to": e.to_id, "edge": e.edge_type} for e in repo.edges()
    ]
    return {"nodes": nodes, "edges": edges}
