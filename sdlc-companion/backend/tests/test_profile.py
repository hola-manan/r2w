"""P03 verification: load, ring ranking, validation, profile divergence."""
from __future__ import annotations

from app.profile import (
    ProfileRetriever,
    check_constraints,
    list_profile_ids,
    load_profile,
    validate_choice,
)
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
