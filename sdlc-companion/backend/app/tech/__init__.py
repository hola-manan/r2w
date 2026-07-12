"""Team Tech Capability Catalog + task→tool matching (self-contained feature).

See README.md for what this is and the TWO integration seams into the host app.
"""
from __future__ import annotations

from app.tech.catalog import TechCatalog, catalog_entry, docs_dir, load_catalog
from app.tech.matcher import Ranking, TechMatcher, rank_tools
from app.tech.schema import TechCapability, TechMatch, TechMatchOutput

__all__ = [
    "TechCapability",
    "TechMatch",
    "TechMatchOutput",
    "TechCatalog",
    "load_catalog",
    "catalog_entry",
    "docs_dir",
    "TechMatcher",
    "rank_tools",
    "Ranking",
]
