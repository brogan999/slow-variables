"""The outlook's claim states are pure: a claim is tested on made-up facts, never on a live store."""

from ai_tracker.outlook import claims, problems, state

F = {
    "rli": {"value": 0.21, "as_of": "2026-09-03"},
    "old": {"value": 0.9, "as_of": "2025-01-01", "stale": True},
    "gap": {"value": 4.4, "as_of": "2026-09-20"},
}


def test_a_claim_holds_fails_or_cannot_be_tested():
    assert state({"test": {"fact": "rli", "gt": 0.2}}, F) == "holding"
    assert state({"test": {"fact": "rli", "gt": 0.5}}, F) == "failing"
    assert state({"test": {"fact": "old", "gt": 0.5}}, F) == "untestable"  # a stale reading tests nothing
    assert state({"test": {"fact": "missing", "gt": 0.5}}, F) == "untestable"
    assert state({"falsifier": "Proved wrong if X."}, F) == "untestable"


def test_a_reading_both_sides_expect_settles_nothing():
    c = {"test": {"fact": "gap", "gt": 2}, "rival_test": {"fact": "gap", "gt": 1}}
    assert state(c, F) == "both"
    assert state({**c, "rival_test": {"fact": "gap", "lt": 1}}, F) == "holding"


SPEC = {
    "sources": [{"id": "jones", "who": "Benjamin Jones", "field": "economics of innovation", "finding": "x",
                 "work": "w", "year": 2026, "url": "https://ex.test", "quote": "research moves at the pace of its slowest task"}],
    "positions": [
        {"id": "slow", "folio": "capability", "holders": ["jones"], "attribution": "author", "rival": "fast"},
        {"id": "fast", "folio": "capability", "holders": [], "attribution": "site", "rival": "slow"},
    ],
    "claims": [{"id": "c1", "position": "slow", "text": "t", "test": {"fact": "rli", "lt": 0.5}, "row": "pretraining",
                "stage": "methods", "expect_state": "holding"}],
}


def test_claims_carry_their_position_and_state():
    (c,) = claims(SPEC, F)
    assert (c["state"], c["folio"], c["holders"], c["rival"], c["expected"]) == ("holding", "capability", ["jones"], "fast", "holding")


def test_a_ledger_that_cannot_resolve_names_each_problem():
    assert problems(SPEC, F, {"pretraining"}, {"methods"}) == []
    bad = {
        "sources": [{**SPEC["sources"][0], "quote": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen"}],
        "positions": [{"id": "slow", "folio": "later", "holders": ["nobody"], "attribution": "author", "rival": "ghost"}],
        "claims": [{"id": "c2", "position": "ghost", "row": "nowhere", "test": {"fact": "rli", "between": 1}},
                   {"id": "c3", "position": "slow"}],
    }
    errs = problems(bad, F, {"pretraining"}, {"methods"})
    for needle in ("quotes fifteen words", "unknown folio", "unknown source nobody", "no rival position",
                   "unknown position", "unknown map row nowhere", "needs exactly one of", "neither a test nor"):
        assert any(needle in e for e in errs), needle
