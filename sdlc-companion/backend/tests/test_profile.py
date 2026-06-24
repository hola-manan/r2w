"""P03 verification: load, ring ranking, validation, profile divergence."""
from __future__ import annotations

import json

import pytest

from app.profile import (
    CompanyProfile,
    ProfileRetriever,
    check_constraints,
    list_profile_ids,
    load_profile,
    validate_choice,
)
from app.profile.schema import ComplianceRule, RadarEntry
from app.schemas import Ring


def test_seed_profiles_present():
    ids = list_profile_ids()
    assert "eu-fintech" in ids
    assert "startup-web" in ids


def test_candidates_ranked_adopt_first_hold_excluded():
    r = ProfileRetriever(load_profile("eu-fintech"))
    datastore = r.candidates("datastore")
    names = [e.name for e in datastore]
    assert names[0] == "PostgreSQL"  # Adopt ranks first
    assert all(e.ring != Ring.HOLD for e in datastore)
    assert "DynamoDB" not in names  # Hold excluded


def test_validate_choice_flags_hold_and_offradar():
    r = ProfileRetriever(load_profile("eu-fintech"))
    assert validate_choice(r, "PostgreSQL").allowed is True
    assert validate_choice(r, "MongoDB").allowed is False  # Hold
    offradar = validate_choice(r, "CockroachDB")
    assert offradar.in_radar is False and offradar.allowed is False


def test_hard_constraints_only():
    r = ProfileRetriever(load_profile("eu-fintech"))
    hard = {c.id for c in r.hard_constraints()}
    assert "COMP-1" in hard
    assert "COMP-5" not in hard  # soft


def test_check_constraints_reports_uncovered():
    r = ProfileRetriever(load_profile("eu-fintech"))
    uncovered = check_constraints(r, ["COMP-1", "COMP-2"])
    assert "COMP-3" in uncovered and "COMP-4" in uncovered


def test_profiles_diverge_for_realtime():
    """The swap-demo backbone: realtime support differs across profiles."""
    eu = ProfileRetriever(load_profile("eu-fintech"))
    startup = ProfileRetriever(load_profile("startup-web"))
    # Firebase is blocked in fintech but adopted in startup.
    assert validate_choice(eu, "Firebase Realtime DB").allowed is False
    assert validate_choice(startup, "Firebase Realtime DB").allowed is True


def test_seed_profiles_validate_cleanly():
    # The integrity validators must not reject the shipped seeds.
    for pid in ("eu-fintech", "startup-web"):
        assert load_profile(pid).id == pid


def test_duplicate_radar_names_rejected():
    with pytest.raises(ValueError, match="duplicate radar entry names"):
        CompanyProfile(
            id="x", name="X",
            radar=[
                RadarEntry(name="Redis", category="cache", ring=Ring.ADOPT),
                RadarEntry(name="redis", category="datastore", ring=Ring.ADOPT),
            ],
        )


def test_duplicate_compliance_ids_rejected():
    with pytest.raises(ValueError, match="duplicate compliance ids"):
        CompanyProfile(
            id="x", name="X",
            compliance=[
                ComplianceRule(id="COMP-1", rule="a"),
                ComplianceRule(id="comp-1", rule="b"),
            ],
        )


def test_loader_rejects_id_filename_mismatch(tmp_path, monkeypatch):
    from app.profile import loader

    (tmp_path / "myprof.json").write_text(
        json.dumps({"id": "different", "name": "X"}), encoding="utf-8"
    )
    monkeypatch.setattr(loader, "profiles_dir", lambda: tmp_path)
    loader.load_profile.cache_clear()
    with pytest.raises(ValueError, match="does not match its filename"):
        loader.load_profile("myprof")
