"""The bottleneck map's builder is pure, so it is tested on made-up inputs rather than a live store."""

from ai_tracker.bottleneck_map import build, load, problems

STAGES = [{"id": s, "label": s} for s in ("methods", "products", "early_adoption", "adaptation")]
SPEC = {
    "stages": STAGES,
    "chain": [
        {"input": "chips", "layer": "compute", "sublayer": "semis", "bites": {"methods": "Chips train models."}},
        {"input": "grid", "layer": "compute", "bites": {"methods": "Sites wait to connect.", "products": "So does serving."}},
        {"input": "money", "layer": "compute", "bites": {"methods": "Runs are paid for first."}},
    ],
    "families": [
        {"name": "Law family", "label": "Law", "placed": "site", "why": "They say these act across every stage.",
         "also": {"early_adoption": {"by": "author", "why": "Their own item on liability."}}},
        {"name": "Stage family", "label": "Stage", "placed": "author", "why": "Their own second stage, people."},
    ],
    "nber": [{"id": "pay", "label": "Work and pay", "what": "Who is paid.", "bites": {"adaptation": "Slowly."},
              "indicators": ["labour_share", "draft"], "ledgers": ["agent_access_fences"]}],
    "predictions": [{"id": "grid_now", "cells": {"grid": "methods"}}, {"id": "money_now", "rows": ["money"]}],
}
SCORECARD = {"inputs": [
    {"id": "chips", "name": "Chips", "what": "The chips.", "kind": "supply", "score": 46, "word": "moderate",
     "confidence": 59, "hatched": False, "withheld": None, "obs_ids": ["o1"], "reads": "Supply growth.",
     "gauges": [{"label": "Supply growth", "reading": {"href": "/query#x"}}]},
    {"id": "grid", "name": "Grid", "what": "The grid.", "kind": "supply", "score": None, "word": None, "confidence": None,
     "hatched": False, "withheld": {"kind": "not_read_yet", "because": "Queues are not read yet."}, "obs_ids": [], "gauges": []},
    {"id": "money", "name": "Capital", "what": "Money.", "kind": "money", "score": 18, "word": "slack", "confidence": 72,
     "hatched": False, "withheld": None, "obs_ids": ["o2"], "gauges": []},
]}
PREDICTIONS = [
    {"id": "grid_now", "claim": "The grid binds now.", "state": "holding", "when": "now"},
    {"id": "money_now", "claim": "Money is not scarce.", "state": "holding", "when": "now"},
]
LINKED = [
    {"id": "a", "name": "Alpha", "status": "faster_than_normal", "published": True},
    {"id": "b", "name": "Beta", "status": "emerging", "published": True},
    {"id": "c", "name": "Gamma", "status": None, "published": False},  # unpublished: listed, never counted
]
BOTTLENECKS = {
    "sections": [{"name": "Law family", "bucket_id": "adaptation"}, {"name": "Stage family", "bucket_id": "early_adoption"}],
    "grid": [{"name": "Law family", "cells": {"law": [10, 11], "medicine": []}}, {"name": "Stage family", "cells": {}}],
    "items": [{"section": "Law family", "related": LINKED[:2]}, {"section": "Law family", "related": LINKED},
              {"section": "Stage family", "related": []}],
}
CARDS = {"labour_share": {"name": "Labour share", "status": "consistent_with_normal", "published": True},
         "draft": {"name": "Draft", "status": None, "published": False}}
READINGS = {"ledger:agent_access_fences:for": {"label": "fences", "value": 1, "unit": "count", "as_of": "2025-11-04",
                                              "obs_ids": ["f1"], "href": "/query#ledger_events_12m"}}
NAMES = {"compute": "Compute", "semis": "Semiconductors"}


def _map():
    return build(SPEC, SCORECARD, PREDICTIONS, BOTTLENECKS, CARDS, READINGS, NAMES, [])


def _rows(g):
    return {r["id"]: r for sec in _map()["groups"][g]["sections"] for r in sec["rows"]}


def test_a_scored_input_is_measured_carries_its_rows_and_a_withheld_one_is_unmeasured():
    chain = _rows(0)
    assert chain["chips"]["reading"]["obs_ids"] == ["o1"] and chain["chips"]["cells"]["methods"]["measured"]
    grid = chain["grid"]
    assert grid["reading"]["kind"] == "withheld" and grid["reading"]["because"] == "Queues are not read yet."
    assert set(grid["cells"]) == {"methods", "products"} and not grid["cells"]["products"]["measured"]


def test_a_prediction_marks_the_cell_it_names_and_one_that_says_no_binding_is_only_listed():
    chain = _rows(0)
    (w,) = chain["grid"]["cells"]["methods"]["writers"]
    assert (w["who"], w["state"]) == ("This site", "holding") and not chain["grid"]["cells"]["products"]["writers"]
    assert not any(c["writers"] for c in chain["money"]["cells"].values()) and chain["money"]["claims"][0]["text"] == "Money is not scarce."


def test_a_familys_tally_counts_its_distinct_published_indicators_and_adds_up():
    law = _rows(1)["family_0"]
    r = law["reading"]
    assert (r["instruments"], r["fast"], r["normal"], r["other"]) == (2, 1, 0, 1)  # Gamma is unpublished
    assert r["instruments"] == r["fast"] + r["normal"] + r["other"] and law["cells"]["adaptation"]["measured"]
    assert [i["label"] for i in law["instruments"]] == ["Alpha", "Beta", "Gamma"] and law["instruments"][-1]["unpublished"]


def test_placements_are_credited_to_whoever_made_them():
    law, stage = _rows(1)["family_0"], _rows(1)["family_1"]
    assert law["cells"]["adaptation"]["site"] and not law["cells"]["early_adoption"]["site"]  # their own item
    assert not stage["cells"]["early_adoption"]["site"] and not stage["cells"]["early_adoption"]["measured"]
    assert law["domains"] == {"law": [10, 11]} and law["href"] == "#s-0"


def test_an_nber_row_counts_published_indicators_and_its_ledger_as_readings():
    pay = _rows(1)["pay"]
    assert pay["reading"] == {"kind": "tally", "instruments": 1, "fast": 0, "normal": 1, "other": 0, "readings": 1}
    assert pay["readings"][0]["obs_ids"] == ["f1"] and pay["cells"]["adaptation"]["measured"]


def test_chain_rows_are_grouped_by_their_layer_and_stages_are_numbered():
    m = _map()
    (sec,) = m["groups"][0]["sections"]
    assert (sec["name"], [r["id"] for r in sec["rows"]]) == ("Compute", ["chips", "grid", "money"])
    assert [s["n"] for s in m["stages"]] == [1, 2, 3, 4]


def test_the_seed_resolves_and_a_broken_one_names_each_problem():
    assert load()["stages"][0]["id"] == "methods"
    bad = {
        **SPEC,
        "chain": [*SPEC["chain"], {"input": "ghost", "layer": "nowhere", "bites": {"later": "x"}}],
        "families": [{"name": "Law family", "label": "Law", "placed": "who", "why": "short",
                      "also": {"someday": {"by": "author", "why": "x"}}}],
        "nber": [{**SPEC["nber"][0], "ledgers": ["unknown_ledger"]}],
        "predictions": [{"id": "nobody", "cells": {"chips": "someday", "phantom": "methods"}, "rows": ["phantom"]}],
    }
    errs = problems(bad, {"chips", "grid", "money", "orphan"}, {"Law family", "Missing family"}, {"labour_share"},
                    {"compute", "semis"}, {"grid_now"}, {"adaptation", "new_bucket"})
    for needle in ("no scorecard input ghost", "orphan is not on the map", "nowhere", "unknown stage later",
                   "Missing family is not on the map", "needs who placed it", "adds stage someday",
                   "bucket new_bucket is drawn at no stage", "unknown indicator draft", "unknown ledger unknown_ledger",
                   "no prediction nobody", "unknown row phantom", "unknown stage someday", "lists an unknown row phantom"):
        assert any(needle in e for e in errs), needle


def test_an_outlook_claim_marks_its_cell_in_plain_words_with_its_threshold_written_in():
    from ai_tracker.bottleneck_map import outlook_claims

    doc = {
        "sources": [{"id": "hk", "who": "Gillian Hadfield and Andrew Koh"}],
        "tests": {"c1": {"line": 0.5, "unit": "share"}},
        "claims": [
            {"id": "c1", "row": "chips", "stage": "products", "attribution": "author", "holders": ["hk"], "state": "both",
             "text": "Chips take more than [test:c1] of the profit [cite:hk]."},
            {"id": "c2", "row": None, "stage": "methods", "attribution": "site", "holders": [], "state": "holding", "text": "x"},
        ],
    }
    claims = outlook_claims(doc)
    assert claims == [{"row": "chips", "stage": "products", "who": "Gillian Hadfield and Andrew Koh", "state": "both",
                       "text": "Chips take more than 50% of the profit.", "href": "/outlook#claim-c1"}]
    doc["sources"].append({"id": "r", "who": "Pascual Restrepo"})
    doc["positions"] = [{"id": "pair", "holders": ["hk", "r"]}]
    doc["claims"] = [
        {"id": "e1", "position": "pair", "row": "grid", "attribution": "extension", "holders": ["hk", "r"], "state": "untestable", "text": "x"},
        {"id": "e2", "position": "pair", "row": "grid", "attribution": "extension", "holders": ["r"], "state": "untestable", "text": "y"},
    ]
    assert [c["who"] for c in outlook_claims(doc)] == [
        "This site, extending Gillian Hadfield and Andrew Koh; Pascual Restrepo",  # the position is the site's reach
        "Pascual Restrepo",  # a claim naming its own maker is theirs outright
    ]
    m = build(SPEC, SCORECARD, PREDICTIONS, BOTTLENECKS, CARDS, READINGS, NAMES, [], claims)
    chips = {r["id"]: r for sec in m["groups"][0]["sections"] for r in sec["rows"]}["chips"]
    assert chips["cells"]["products"]["writers"][0]["href"] == "/outlook#claim-c1"  # a stage it does not act on, marked
