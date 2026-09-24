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
