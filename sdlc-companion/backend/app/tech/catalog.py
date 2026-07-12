"""Tech Capability Catalog: loads the team's per-tool capability docs.

The docs live *inside this package* (`app/tech/docs/*.md`) so the whole feature is one
self-contained, copy-pasteable folder. Each doc is markdown with a tiny YAML-ish
front-matter (`id`, `name`, `category`, `summary`) — parsed here without any YAML
dependency. Add a tool later by dropping a 4th `.md`; it is auto-discovered.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from app.tech.schema import TechCapability


def docs_dir() -> Path:
    """backend/app/tech/catalog.py -> backend/app/tech/docs"""
    return Path(__file__).resolve().parent / "docs"


def _parse_doc(doc_id: str, text: str) -> TechCapability:
    """Split leading `--- ... ---` front-matter (simple `key: value` lines) from the body."""
    meta: dict[str, str] = {}
    body = text.strip()
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is not None:
            for line in lines[1:end]:
                if ":" not in line or not line.strip():
                    continue
                key, _, val = line.partition(":")
                meta[key.strip().lower()] = val.strip()
            body = "\n".join(lines[end + 1 :]).strip()
    return TechCapability(
        id=meta.get("id", doc_id),
        name=meta.get("name", doc_id),
        category=meta.get("category", ""),
        summary=meta.get("summary", ""),
        body=body,
    )


class TechCatalog:
    """In-memory view of the loaded capability docs, keyed by id and name (case-insensitive)."""

    def __init__(self, items: list[TechCapability]) -> None:
        self._items = list(items)
        self._by_key: dict[str, TechCapability] = {}
        for it in self._items:
            self._by_key[it.id.lower()] = it
            self._by_key[it.name.lower()] = it

    def all(self) -> list[TechCapability]:
        return list(self._items)

    def names(self) -> list[str]:
        return [it.name for it in self._items]

    def get(self, name_or_id: str | None) -> TechCapability | None:
        if not name_or_id:
            return None
        return self._by_key.get(name_or_id.strip().lower())

    def is_empty(self) -> bool:
        return not self._items

    def docs_text(self) -> str:
        """Full docs, concatenated, for grounding the matcher prompt."""
        blocks = [
            f"### {it.name} (id={it.id}, category={it.category})\n{it.summary}\n\n{it.body}"
            for it in self._items
        ]
        return "\n\n---\n\n".join(blocks)


@lru_cache
def load_catalog() -> TechCatalog:
    """Singleton catalog over `docs/*.md`. Empty (never raises) if the folder is absent."""
    d = docs_dir()
    items: list[TechCapability] = []
    if d.exists():
        for path in sorted(d.glob("*.md")):
            items.append(_parse_doc(path.stem, path.read_text(encoding="utf-8")))
    return TechCatalog(items)


def catalog_entry(name: str):
    """A catalog tool as an Adopt `RadarEntry`, so existing validation/grounding/gates treat
    it exactly like an Adopt radar entry. Returns None if `name` is not a catalog tool.

    Imported lazily by `ProfileRetriever.lookup()` (integration Seam 1). The RadarEntry/Ring
    imports are deferred to keep this package import-cycle-free.
    """
    cap = load_catalog().get(name)
    if cap is None:
        return None
    from app.profile.schema import RadarEntry
    from app.schemas import Ring

    return RadarEntry(name=cap.name, category=cap.category, ring=Ring.ADOPT, notes=cap.summary)
