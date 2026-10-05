"""The firm page (/firm): an essay argued from the outlook's ledger. Its claims, facts and sources are outlook records;
seed/firm.yaml only says which positions sit under which folio, holds the rent-or-own table, and names the claims on
which the essay says the board's leans disagree with it."""

import re

from ai_tracker import census, firm
from ai_tracker import outlook as ol
from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.board import judgements

from .test_outlook import NUMBER_WORD, YEAR

OUTLOOK = {
    "as_of": "2026-10-01",
    "facts": {"deals": {"value": 3, "unit": "count"}, "unused": {"value": 1, "unit": "count"}},
    "tests": {"c1": {"line": 1, "unit": "count"}, "c9": {"line": 2, "unit": "count"}},
    "sources": [{"id": "b", "who": "B", "n": 1}, {"id": "a", "who": "A", "n": 2}, {"id": "z", "who": "Z", "n": 3}],
    "positions": [
        {"id": "owns", "holders": ["a"], "rival": "rents", "case": "It is so [fact:deals]."},
        {"id": "rents", "holders": [], "rival": "owns"},
        {"id": "elsewhere", "holders": ["z"], "rival": "owns"},
    ],
    "claims": [
        {"id": "c1", "position": "owns", "state": "holding", "holders": ["a"], "test": {"fact": "deals", "gte": 1}},
        {"id": "c2", "position": "rents", "state": "untestable", "holders": [], "test": None},
        {"id": "c9", "position": "elsewhere", "state": "failing", "holders": ["z"], "test": {"fact": "unused", "gte": 2}},
    ],
}
SPEC = {
    "folios": {"rule": ["owns", "rents"]},
    "leans_against": ["c2"],
    "regimes": {"title": "When to rent", "note": "A judgement.", "columns": ["What is scarce", "Who wins"], "rows": [["Nothing", "The customer"]]},
}
NEW_CLAIMS = {
    "firms_do_not_dissolve", "asking_leaks", "liability_priced_apart", "operators_bought", "ownership_pays", "lab_runs_operations",
    "firms_rent", "sensing_owns", "line_not_side", "edge_floor", "check_binds", "pooled_premium",
}
ESSAY = "# T\n\nLede.\n\n### Folio I · the rule\n\n## A claim\n\nB said so [cite:b].\n\n[plate:regimes]\n"


def test_the_page_carries_only_its_own_positions_claims_facts_and_sources():
    doc = firm.build(SPEC, OUTLOOK, ESSAY)
    assert [p["id"] for p in doc["positions"]] == ["owns", "rents"] and doc["folios"] == {"rule": ["owns", "rents"]}
    assert [c["id"] for c in doc["claims"]] == ["c1", "c2"]  # a claim of a position seated elsewhere stays there
    assert doc["tally"] == {"holding": 1, "failing": 0, "both": 0, "untestable": 1}
    assert set(doc["facts"]) == {"deals"} and set(doc["tests"]) == {"c1"}
    assert [(x["id"], x["n"]) for x in doc["sources"]] == [("b", 1), ("a", 2)]  # numbered as this essay cites them
    assert doc["regimes"]["rows"] == [["Nothing", "The customer"]] and doc["as_of"] == "2026-10-01"
    assert doc["census_cut"] == {} and doc["shapes"] == {}  # a page without them still builds
    cut = {"version": "v", "groups": [{"name": "Management"}]}
    assert firm.build(SPEC, OUTLOOK, ESSAY, cut)["census_cut"] == cut  # the census cut rides in the page's own file


def test_a_page_that_cannot_resolve_names_each_problem():
    spec = {"positions": OUTLOOK["positions"], "claims": OUTLOOK["claims"], "sources": [{"id": "b"}], "facts": {}}
    leans = {"judgements": [{"kind": "outlook", "id": "c2", "lean": "leans_false"}]}
    assert firm.problems(SPEC, spec, leans, ESSAY) == []
    bad = firm.problems(
        {
            "folios": {"rule": ["owns", "nobody"], "missing": ["rents"]},
            "leans_against": ["c2", "c1"],
            "regimes": {"title": "T", "note": "N", "columns": ["a", "b"], "rows": [["only one cell"], ["3 firms", "x"]]},
        },
        spec,
        {"judgements": [{"kind": "outlook", "id": "c2", "lean": "leans_true"}]},
        ESSAY + "\nUnsourced [cite:nobody] [plate:nowhere].\n",
    )
    for needle in (
        "unknown position nobody",
        "folio missing is not in the essay",
        "c2 no longer leans against",  # the essay says the board disagrees; a re-made lean must change the sentence
        "c1 has no lean",
        "row 0 does not fill every column",
        "types a figure",
        "[cite:nobody]",
        "[plate:nowhere]",
    ):
        assert any(needle in e for e in bad), (needle, bad)


def test_the_real_page_resolves_and_types_no_figure():
    spec, essay = firm.load(), firm.ESSAY.read_text()
    assert firm.problems(spec, ol.load(), judgements(), essay) == []
    for t in [essay, *firm.strings(spec)]:
        stray = [w for w in ol.TOKEN.sub("", t).split() if re.search(r"\d", w)]
        assert all(YEAR.fullmatch(w) for w in stray), stray
        for sentence in re.split(r"(?<=[.!?])\s+", t):
            if NUMBER_WORD.search(ol.TOKEN.sub("", sentence)):
                assert ol.TOKEN.search(sentence), sentence  # a figure in words still needs its token
    assert 1800 <= len(ol.TOKEN.sub("", essay).split()) <= 3800  # raised from 2700 for the staff review's caveats, then for the folio on the firm's shape


def test_the_essay_says_who_drafted_it_and_whose_model_scored_the_census():
    essay = firm.ESSAY.read_text()
    assert "Anthropic, whose model also drafted this page" in essay and "paid adviser to Anthropic" in essay
    assert "this site's judgement" in essay  # the picture of the firm in the limit is labelled
    assert "has since joined a research institute run by Anthropic" in essay  # Hitzig's present tie
    assert "The case against renting is Garicano's" not in essay  # they argue for renting, with a remedy
    assert "Their remedy is not to own the model" in essay


def test_tonights_readings_settle_the_claims_the_records_can_settle():
    s = st.Store()
    s.derived = run_metrics(s.con)  # derived rows are not committed; a fresh checkout computes them
    doc = ol.build(s)
    claims = {c["id"]: c for c in doc["claims"]}
    # its author wrote, after OpenAI launched its deployment company, that no lab had yet done this: the row is no test
    assert claims["lab_owns_services_firm"]["state"] == "untestable"
    assert claims["lab_runs_operations"]["attribution"] == claims["check_binds"]["attribution"] == "site"
    now, before = doc["facts"]["rollup_service_deals"], doc["facts"]["rollup_service_deals_year_ago"]
    assert now and before and now["obs_ids"] and now["value"] != doc["facts"]["rollup_software_deals"]["value"]
    assert claims["operators_bought"]["state"] == ("holding" if now["value"] > before["value"] else "failing")
    page = firm.build(firm.load(), doc, firm.ESSAY.read_text())
    assert NEW_CLAIMS <= {c["id"] for c in page["claims"]}
    assert all(c.get("falsifier") for c in page["claims"])  # every claim names what would prove it wrong


def test_the_shapes_plate_credits_every_row_and_fiction_is_labelled_and_tests_nothing():
    spec, outlook = firm.load(), ol.load()
    shapes = spec["shapes"]
    sources = {x["id"] for x in outlook["sources"]}
    assert len(shapes["rows"]) >= 5
    for row in shapes["rows"]:
        assert row["shape"] and row["goes_first"] and row["stays"] and row["would_show"]
        assert row["sources"] and set(row["sources"]) <= sources, row["shape"]  # someone argued it, and is on the page
    fiction = spec["fiction"]
    assert "fiction" in fiction["label"].lower() and "not evidence" in fiction["label"].lower()
    assert len(fiction["works"]) >= 4 and all(w["author"] and w["title"] and w["picture"] for w in fiction["works"])
    held = {h for c in outlook["claims"] for h in c.get("holders") or []} | {h for p in outlook["positions"] for h in p.get("holders") or []}
    assert not held & {w.get("source") for w in fiction["works"]}  # no claim or position rests on a novel


def test_the_shape_folio_says_what_the_census_can_and_cannot_read():
    essay = firm.ESSAY.read_text()
    assert "### Folio VII · the shape" in essay and "[plate:shapes]" in essay and "[plate:jobs]" in essay
    folio = essay.split("### Folio VII · the shape")[1].split("### Folio VIII")[0]
    assert "occupational groups" in folio and "not junior against senior" in folio  # the census has no seniority field
    assert "this site's judgement" in folio  # where the site lands is labelled
    assert "fiction" in folio.lower()
    groups = census.shape(census.load())["groups"]
    by = {g["name"]: g for g in groups}
    # the folio's sentences about the census, re-tested against the bundle
    assert all(g["share_waits_on_check"] > g["share_passes"] and g["share_passes"] < 0.5 for g in groups)
    low = sorted(groups, key=lambda g: g["share_passes"])
    assert {low[0]["name"], low[1]["name"]} == {"Management", "Legal"}
    assert {low[-1]["name"], low[-2]["name"]} == {"Office and administrative support", "Sales"}
    assert by["Management"]["mean_pay"] > by["Sales"]["mean_pay"]
