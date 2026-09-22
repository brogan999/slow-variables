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


def test_a_level_due_by_a_date_cannot_fail_before_it():
    from datetime import date

    c = {"test": {"fact": "rli", "gt": 0.5}, "due": "2027-12-31"}
    assert state(c, F, date(2026, 9, 22)) == "untestable" and state(c, F, date(2028, 1, 1)) == "failing"
    assert (
        state({**c, "test": {"fact": "rli", "gt": 0.2}}, F, date(2026, 9, 22)) == "holding"
    )  # reached early


def test_a_reading_both_sides_expect_settles_nothing():
    c = {"test": {"fact": "gap", "gt": 2}, "rival_test": {"fact": "gap", "gt": 1}}
    assert state(c, F) == "both"
    assert state({**c, "rival_test": {"fact": "gap", "lt": 1}}, F) == "holding"


SPEC = {
    "sources": [
        {
            "id": "jones",
            "who": "Benjamin Jones",
            "field": "economics of innovation",
            "finding": "x",
            "work": "w",
            "year": 2026,
            "url": "https://ex.test",
            "quote": "research moves at the pace of its slowest task",
        }
    ],
    "positions": [
        {"id": "slow", "folio": "capability", "holders": ["jones"], "attribution": "author", "rival": "fast"},
        {"id": "fast", "folio": "capability", "holders": [], "attribution": "site", "rival": "slow"},
    ],
    "claims": [
        {
            "id": "c1",
            "position": "slow",
            "text": "t",
            "test": {"fact": "rli", "lt": 0.5},
            "row": "pretraining",
            "stage": "methods",
            "expect_state": "holding",
        }
    ],
}


def test_claims_carry_their_position_and_state():
    (c,) = claims(SPEC, F)
    assert (c["state"], c["folio"], c["holders"], c["rival"], c["expected"]) == (
        "holding",
        "capability",
        ["jones"],
        "fast",
        "holding",
    )


def test_a_ledger_that_cannot_resolve_names_each_problem():
    assert problems(SPEC, F, {"pretraining"}, {"methods"}) == []
    bad = {
        "sources": [
            {
                **SPEC["sources"][0],
                "quote": "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen",
            }
        ],
        "positions": [
            {"id": "slow", "folio": "later", "holders": ["nobody"], "attribution": "author", "rival": "ghost"}
        ],
        "claims": [
            {"id": "c2", "position": "ghost", "row": "nowhere", "test": {"fact": "rli", "between": 1}},
            {"id": "c3", "position": "slow"},
        ],
    }
    errs = problems(bad, F, {"pretraining"}, {"methods"})
    for needle in (
        "quotes fifteen words",
        "unknown folio",
        "unknown source nobody",
        "no rival position",
        "unknown position",
        "unknown map row nowhere",
        "needs exactly one of",
        "neither a test nor",
    ):
        assert any(needle in e for e in errs), needle


def test_a_scenario_is_consistent_unless_a_signpost_fails_its_test():
    from ai_tracker.outlook import scenarios

    spec = {
        "scenarios": {
            "cells": [
                {"progress": "steady", "signposts": ["a", "b"]},
                {"progress": "fast", "signposts": ["c"]},
            ]
        }
    }
    cl = [{"id": "a", "state": "holding"}, {"id": "b", "state": "both"}, {"id": "c", "state": "failing"}]
    steady, fast = scenarios(spec, cl)["cells"]
    assert (
        steady["consistent"] and not fast["consistent"]
    )  # every cell tonight's readings allow is marked, not one
    assert fast["signposts"] == [{"claim": "c", "state": "failing"}]


def test_an_essay_token_or_quote_that_does_not_resolve_is_named():
    from ai_tracker.outlook import essay_problems

    spec = {
        **SPEC,
        "facts": {"rli": {}},
        "claims": [*SPEC["claims"], {"id": "c2", "position": "slow", "test": {"fact": "rli", "lt": "rli"}}],
    }
    ok = 'Jones argues that "research moves at the pace of its slowest task" [cite:jones], below [test:c1] [fact:rli].'
    assert essay_problems(ok + " [plate:board]", spec) == []
    bad = essay_problems(
        ok
        + ' "a phrase nobody said" [cite:nobody] [test:c2] [plate:nowhere] "research moves at the pace of its slowest task"',
        spec,
    )
    for needle in (
        "no source's checked quote",
        "[cite:nobody]",
        "[test:c2]",
        "[plate:nowhere]",
        "quoted more than once",
    ):
        assert any(needle in e for e in bad), (
            needle
        )  # [test:] renders a number, so a claim tested against a fact has none


# The real ledger and essay, read without a Store: nothing here depends on tonight's data.
import re  # noqa: E402

import yaml  # noqa: E402

from ai_tracker import outlook as ol  # noqa: E402
from ai_tracker.bottleneck_map import load as load_map  # noqa: E402

YEAR = re.compile(r"\(?(1[6-9]\d\d|20\d\d)s?[\"”]?[,.;:)]?")
NUMBER_WORD = re.compile(
    r"\b(half|halves|twice|double[sd]?|triple[sd]?|percent|per cent|fifths?|tenths?|hundreds?|thousands?|millions?"
    r"|billions?|trillions?|dozens?|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen"
    r"|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\b|-fold\b",
    re.I,
)
ADVICE = re.compile(  # advice to the reader; describing what labs or firms buy is not advice
    r"own it|double down|size as|enter when|exit when|stop when|don't buy|you are late|inflecting|investors should"
    r"|should (buy|sell|invest)|time to (buy|sell)|(buy|sell) now|position yourself",
    re.I,
)


def _texts() -> list[str]:
    spec = ol.load()
    return [ol.ESSAY.read_text(), *ol.strings(spec)]


def test_the_outlook_types_no_figure():
    for t in _texts():
        stray = [w for w in ol.TOKEN.sub("", t).split() if re.search(r"\d", w)]
        assert all(YEAR.fullmatch(w) for w in stray), stray  # a figure is a [fact:], [test:] or [cite:] token


def test_a_number_word_travels_with_its_token():
    for t in _texts():
        for sentence in re.split(r"(?<=[.!?])\s+", t):
            if NUMBER_WORD.search(ol.TOKEN.sub("", sentence)):
                assert ol.TOKEN.search(sentence), (
                    sentence
                )  # "a fifth", "twice": a figure in words still needs its source


def test_the_outlook_forecasts_and_never_advises():
    hits = [m.group(0) for t in _texts() for m in ADVICE.finditer(t)]
    assert hits == [], hits


def test_the_ledger_and_the_essay_resolve():
    spec, m = ol.load(), load_map()
    rows = (
        {r["input"] for r in m["chain"]}
        | {r["id"] for r in m["nber"]}
        | {f"family_{k}" for k in range(len(m["families"]))}
    )
    assert ol.problems(spec, spec["facts"], rows, {s["id"] for s in m["stages"]}) == []
    assert ol.essay_problems(ol.ESSAY.read_text(), spec) == []
    folios = [p["folio"] for p in spec["positions"]]
    assert all(
        sum(1 for p in spec["positions"] if p["folio"] == f and p.get("visible")) == 3 for f in ol.FOLIOS
    ), folios
    assert all(s["url"].startswith("https://") or s["url"].startswith("http://") for s in spec["sources"])
    assert len(re.findall(r"^### Folio ", ol.ESSAY.read_text(), re.M)) == len(
        ol.FOLIOS
    )  # the page seats positions by folio
    assert yaml.safe_load(ol.SPEC.read_text()) == spec
