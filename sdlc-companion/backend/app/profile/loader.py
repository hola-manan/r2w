"""Profile loader (P03). Loads seeded JSON profiles; supports swapping by id."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.profile.schema import CompanyProfile


def profiles_dir() -> Path:
    # backend/app/profile/loader.py -> backend/data/profiles
    return Path(__file__).resolve().parents[2] / "data" / "profiles"


def list_profile_ids() -> list[str]:
    d = profiles_dir()
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob("*.json"))


@lru_cache
def load_profile(profile_id: str) -> CompanyProfile:
    path = profiles_dir() / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"profile '{profile_id}' not found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    profile = CompanyProfile.model_validate(data)
    if profile.id != profile_id:
        raise ValueError(
            f"profile id '{profile.id}' does not match its filename '{profile_id}' "
            f"(ids are cited in ADRs and must be stable)"
        )
    return profile
