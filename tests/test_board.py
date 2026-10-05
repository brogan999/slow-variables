import re

from ai_tracker import board

SPEC = {
    "folios": [{"id": "capability", "label": "Making it work"}, {"id": "value", "label": "Who keeps the money"}],
    "words": {w: {"label": w, "meaning": w} for w in board.ORDER},
    "ledger": {"p1": {"folio": "capability", "line": "A plain line."}},
    "migration": {"m1": {"folio": "value"}},
    "exits": {"e1": {"folio": "value", "indicators": ["i2"]}},
    "folio_overrides": {"c2": "value"},
    "questions": [{"question": "Q?", "indicator": "i1"}, {"question": "R?", "indicator": None, "note": "none"}],
}
OUTLOOK = {
    "as_of": "2026-09-23",
    "sources": [{"id": "s1", "who": "Ann Author", "url": "https://example.org/a"}],
    "facts": {"f1": {"value": 0.4, "unit": "share", "as_of": "2026-06-30", "obs_ids": ["o1"], "href": "/indicators/i3"}},
    "claims": [
        {"id": "c1", "folio": "value", "attribution": "author", "holders": ["s1"], "text": "It holds.",
         "state": "both", "test": {"fact": "f1", "lt": 0.7}, "falsifier": "It stops."},
        {"id": "c2", "folio": "capability", "attribution": "site", "holders": [], "text": "Ours.",
         "state": "untestable", "falsifier": "Not ours."},
    ],
}
ARGUMENT = {"migration": {"predictions": [{"id": "m1", "claim": "Power binds.", "state": "failing"}], "facts": {}}}


def test_every_family_maps_to_one_word_and_the_board_groups_by_folio():
    doc = board.build(
        SPEC,
        [{"id": "p1", "claimant": "Lab", "status": "behind", "window_end": "2027-01-01", "claim_url": None,
          "related_indicators": ["i1"]}],
        OUTLOOK,
        ARGUMENT,
        [{"id": "e1", "state": "contradicted"}],
        [{"monitor": "e1", "label": "Profit moves", "text": "If profit moves."}],
        {"i1": {"status": "emerging"}},
    )
    rows = {r["id"]: r for f in doc["folios"] for r in f["rows"]}
    assert {k: r["word"] for k, r in rows.items()} == {
        "p1": "slower", "c1": "both", "c2": "too_early", "m1": "not_happening", "e1": "not_happening"
    }
    assert rows["c1"]["who"] == "Ann Author" and rows["c2"]["who"] == "This site"
    assert rows["c1"]["reading"]["obs_ids"] == ["o1"] and rows["c1"]["test"] == {"fact": "f1", "op": "lt", "against": 0.7}
    assert rows["c2"]["folio"] == "value"  # the owner's page files it there, whatever its position's folio
    assert [rows[k]["indicators"] for k in ("p1", "c1", "c2", "e1")] == [["i1"], ["i3"], [], ["i2"]]
    assert doc["questions"][0]["status"] == "emerging" and doc["questions"][1]["href"] is None
    assert sum(doc["tally"].values()) == 5
    assert doc["n"] == 5


def test_the_seed_resolves_and_its_lines_type_no_number_but_years():
    spec = board.load()
    assert board.problems(spec, set(spec["ledger"]), set(spec["migration"]), set(spec["exits"]), set(spec["ledger"])) == []
    for k, v in spec["ledger"].items():  # a singularity row has no line: its claim text is already the site's words
        assert not re.search(r"\d", re.sub(r"\b(19|20)\d\d\b", "", v.get("line", ""))), k
    for q in spec["questions"]:
        assert q.get("indicator") or q.get("note"), q["question"]


def test_a_row_without_a_line_reads_its_claim_text():
    spec = {**SPEC, "ledger": {"p1": {"folio": "capability"}}}
    rows = board.rows(spec, [{"id": "p1", "claimant": "A", "claim_text": "Our words for it.", "status": None}], {}, {}, [], [])
    assert rows[0]["line"] == "Our words for it."


def test_an_author_named_by_two_posts_is_named_once():
    srcs = {"a": {"who": "Ann Author"}, "b": {"who": "Ann Author"}, "c": {"who": "Bo Writer"}}
    assert board._who({"holders": ["a", "b", "c"], "attribution": "author"}, srcs) == "Ann Author and Bo Writer"


JUDGED = {
    "made_by": {"model": "claude-opus-5-5", "date": "2026-10-05", "method": "m", "reviewed_by": "a second pass"},
    "judgements": [
        {"kind": "outlook", "id": "c2", "lean": "leans_true", "reason": "The trend points that way.", "rests_on": ["i1"]},
        {"kind": "outlook", "id": "c1", "lean": "likely_false", "reason": "Already settled, so this must not show.", "rests_on": []},
    ],
}
LEANS = {w: {"label": w.replace("_", " "), "meaning": w} for w in ("likely_true", "leans_true", "toss_up", "leans_false", "likely_false")}
LEDGER = [{"id": "p1", "claimant": "Lab", "status": None, "window_end": "2027-01-01", "claim_url": None, "related_indicators": ["i1"]}]


def _built(judgements=None):
    return board.build({**SPEC, "leans": LEANS}, LEDGER, OUTLOOK, ARGUMENT, [], [], {"i1": {"status": "emerging", "name": "Reading one"}}, judgements)


def test_a_models_lean_sits_beside_a_too_early_row_and_changes_no_word_or_tally():
    plain, doc = _built(), _built(JUDGED)
    rows = {r["id"]: r for f in doc["folios"] for r in f["rows"]}
    assert rows["c2"]["word"] == "too_early" and rows["c2"]["judgement"] == {
        "lean": "leans_true", "reason": "The trend points that way.",
        "rests_on": [{"id": "i1", "name": "Reading one", "href": "/indicators/i1"}],
    }
    assert rows["c1"]["word"] == "both" and "judgement" not in rows["c1"]  # settled since it was judged: the lean is dropped
    assert rows["p1"]["word"] == "too_early" and "judgement" not in rows["p1"]  # a too-early row may have no lean yet
    assert (doc["tally"], doc["n"]) == (plain["tally"], plain["n"])
    assert doc["judged"]["model"] == "claude-opus-5-5" and doc["judged"]["tally"]["leans_true"] == 1
    assert sum(doc["judged"]["tally"].values()) == 1
    value = next(f for f in doc["folios"] if f["id"] == "value")
    assert value["leans"] == {"leans_true": 1}
    assert "judged" not in plain and all("judgement" not in r for f in plain["folios"] for r in f["rows"])


def test_a_judgement_must_name_a_real_forecast_a_known_lean_and_type_no_figure():
    ok = {"kind": "outlook", "id": "c2", "lean": "toss_up", "reason": "By 2030 the evidence is thin either way.", "rests_on": ["i1"]}
    known, inds = {("outlook", "c2")}, {"i1"}
    assert board.judgement_problems({**JUDGED, "judgements": [ok]}, known, inds, set(LEANS)) == []
    bad = [
        {**ok, "id": "nope"}, {**ok, "lean": "probably"}, {**ok, "rests_on": ["ghost"]},
        {**ok, "reason": "Use reached 39% of workers."}, {**ok, "reason": "It is doubling each year."},
        {**ok, "reason": "See https://example.org for why."}, {**ok, "reason": "About twenty firms do this."},
    ]
    for b in bad:
        assert board.judgement_problems({**JUDGED, "judgements": [b]}, known, inds, set(LEANS)), b
    assert board.judgement_problems({**JUDGED, "judgements": [ok, ok]}, known, inds, set(LEANS))  # one lean per forecast
    assert board.judgement_problems({"judgements": [ok]}, known, inds, set(LEANS))  # who judged, and when, is required


def test_the_seeded_judgements_pass_their_checks_and_never_reach_the_table_ask_reads():
    from pathlib import Path

    import yaml

    from ai_tracker.store import Seed

    root = Path(__file__).resolve().parents[1]
    doc = board.judgements()
    spec = board.load()
    seed = Seed.load()
    known = (
        {("ledger", k) for k in spec["ledger"]} | {("migration", k) for k in spec["migration"]} | {("exit", k) for k in spec["exits"]}
        | {("outlook", c["id"]) for c in yaml.safe_load((root / "seed" / "outlook.yaml").read_text())["claims"]}
    )
    assert board.judgement_problems(doc, known, {i.id for i in seed.indicators}, set(spec["leans"])) == []
    assert "judgement" not in (root / "src/ai_tracker/store.py").read_text().split("def prediction_table")[1].split("\n    def ")[0]
    page = (root / "web/src/app/predictions/page.tsx").read_text()
    assert "judgement, not a reading" in page and "b.judged" in page
