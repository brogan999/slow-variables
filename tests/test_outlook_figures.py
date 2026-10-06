"""The outlook page's figures of the debate itself (Part 45j): the rival positions face to face, how far each dispute is
from a reading that could settle it, whose arguments these are, when the dated claims fall due, and how a claim gets
its word. `outlook.figures` reads the built page and lays everything out; the web only places it."""

import copy
import json
import re
from pathlib import Path

from ai_tracker import outlook as ol

from .test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
FIGS = WEB / "components" / "OutlookFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "outlook.tsx"
NEW = ("sides", "method", "settle", "whose", "due")


def _p(i, rival, folio="capability", attribution="author", visible=False, layer=None):
    return {"id": i, "rival": rival, "folio": folio, "attribution": attribution, "visible": visible, "title": i.upper(),
            **({"layer": layer} if layer else {})}


def _c(i, position, state, test=False, attribution="author", due=None, rival_until=None, folio="capability"):
    return {"id": i, "position": position, "state": state, "test": {"fact": "f", "gt": 1} if test else None,
            "attribution": attribution, "due": due, "rival_until": rival_until, "folio": folio, "text": f"Claim {i}."}


DOC = {
    "as_of": "2026-10-05",
    "folios": [{"id": "capability", "kicker": "First?"}, {"id": "value", "kicker": "Second?"}],
    "positions": [
        _p("a", "b", visible=True), _p("b", "a", attribution="site"), _p("c", "a", attribution="extension"),
        _p("d", "none_found", folio="value", attribution="site", layer="model"),
        _p("e", "f", folio="value"), _p("f", "e", folio="value"), _p("g", "e", folio="value", visible=True),
    ],
    "claims": [
        _c("c1", "a", "holding", test=True), _c("c2", "a", "both", test=True, rival_until="2027-12-31"),
        _c("c3", "c", "untestable", due="2028-06-30"),
        _c("c4", "e", "untestable", test=True, due="2030-12-31", folio="value"),
        _c("c5", "f", "failing", test=True, folio="value"),
        _c("c6", "g", "untestable", attribution="site", folio="value"),
    ],
}
DOC["tally"] = {k: sum(1 for c in DOC["claims"] if c["state"] == k) for k in ol.STATES}
F = ol.figures(DOC)
REAL = json.loads((ROOT / "web" / "data" / "outlook.json").read_text())


def _disputes(fig):
    return [d for f in fig["sides"]["folios"] for d in f["main"] + f["more"]]


def _sides(fig):
    return [s for d in _disputes(fig) for s in (d["left"], d["right"]) if s]


def test_the_figures_read_the_page_and_change_nothing_on_it():
    before = copy.deepcopy(DOC)
    assert ol.figures(DOC) == F and DOC == before
    assert set(F) == {"looks", "counts", "sides", "settle", "whose", "due"}


def test_every_claim_has_one_look_and_the_looks_sum_to_the_pages_tally():
    assert F["looks"] == {"c1": "holding", "c2": "both", "c3": "no_test", "c4": "waiting", "c5": "failing", "c6": "no_test"}
    assert set(F["counts"]) == set(ol.LOOKS) and sum(F["counts"].values()) == len(DOC["claims"])
    assert all(F["counts"][k] == DOC["tally"][k] for k in ("holding", "failing", "both"))
    assert F["counts"]["waiting"] + F["counts"]["no_test"] == DOC["tally"]["untestable"]  # the page's word, split by why


def test_each_position_on_the_page_is_drawn_once_and_each_claim_is_counted_once():
    s = F["sides"]
    assert [x["id"] for x in _sides(F)] == ["a", "b", "c", "e", "f", "g"]  # the layer unit lives on its layer page
    assert s["positions"] == 6 and s["layer_positions"] == 1 and s["positions"] + s["layer_positions"] == len(DOC["positions"])
    marks = [c for x in _sides(F) for c in x["claims"]]
    assert sorted(marks) == sorted(c["id"] for c in DOC["claims"]) and s["claims"] == len(marks) == len(set(marks))
    by = {d["key"]: d for d in _disputes(F)}
    assert by["a"]["kind"] == "pair" and by["a"]["right"]["id"] == "b" and by["a"]["right"]["claims"] == []
    # a position that argues against one already drawn is a row of its own, and the rival's claims are not drawn again
    assert by["c"]["kind"] == "challenge" and by["c"]["right"] is None and by["c"]["against"] == "a"
    assert s["pairs"] == 2 and s["challenges"] == 2 and s["pairs"] + s["challenges"] == len(_disputes(F))


def test_a_dispute_the_essay_argues_is_shown_and_the_rest_are_folded_under_their_question():
    first, second = F["sides"]["folios"]
    assert (first["id"], first["kicker"]) == ("capability", "First?")
    assert [d["key"] for d in first["main"]] == ["a"] and [d["key"] for d in first["more"]] == ["c"]
    assert [d["key"] for d in second["main"]] == ["g"] and [d["key"] for d in second["more"]] == ["e"]


def test_a_dispute_reads_as_far_as_its_furthest_claim_has_got():
    rows = {r["id"]: r for r in F["settle"]["rows"]}
    cells = {c["key"]: c for r in F["settle"]["rows"] for c in r["cells"]}
    assert {k: c["reach"] for k, c in cells.items()} == {"a": "read", "c": "no_test", "e": "read", "g": "no_test"}
    assert [c["key"] for r in F["settle"]["rows"] for c in r["cells"]] == [d["key"] for d in _disputes(F)]  # the same disputes
    assert cells["a"]["claims"] == 2 and cells["a"]["tested"] == 2 and cells["e"]["tested"] == 2 and cells["c"]["tested"] == 0
    for r in rows.values():
        assert r["n"] == len(r["cells"]) == sum(r["counts"].values()) and set(r["counts"]) == set(ol.REACH)
    assert F["settle"]["n"] == 4 and F["settle"]["counts"] == {"read": 2, "shared": 0, "waiting": 0, "no_test": 2}
    only = lambda looks: ol.figures({**DOC, "claims": [  # noqa: E731
        _c(f"x{n}", "a", "untestable" if k in ("waiting", "no_test") else k, test=k != "no_test") for n, k in enumerate(looks)
    ]})["settle"]["rows"][0]["cells"][0]["reach"]
    assert [only(x) for x in (["both", "waiting"], ["waiting", "no_test"], ["failing", "both"], [])] == ["shared", "waiting", "read", "no_test"]


def test_whose_arguments_counts_positions_once_on_one_scale_and_draws_no_rate():
    w = F["whose"]
    assert [r["id"] for r in w["rows"]] == list(ol.ATTRIBUTIONS)
    assert sum(r["n"] for r in w["rows"]) == F["sides"]["positions"]
    assert {r["id"]: (r["n"], r["with_claim"], r["without"]) for r in w["rows"]} == {"author": (4, 4, 0), "extension": (1, 1, 0), "site": (1, 0, 1)}
    for r in w["rows"]:
        assert r["n"] == r["with_claim"] + r["without"] == sum(b["n"] for b in r["bar"])
        assert all(b["w"] > 0 and 0 <= b["x"] and b["x"] + b["w"] <= 100 + 1e-6 for b in r["bar"])
    assert max(b["x"] + b["w"] for r in w["rows"] for b in r["bar"]) == 100  # the longest row fills the scale
    assert sum(r["claims"] for r in w["rows"]) == len(DOC["claims"])  # a claim is credited once, as the page credits it
    assert w["site_readings"] == 1  # c6: this site's reading of a writer's position
    assert not any(re.search(r"rate|share|pct|percent|rank", k) for r in w["rows"] for k in r)


def test_the_calendar_places_each_dated_claim_once_in_its_year_and_leaves_no_year_out():
    d = F["due"]
    assert [y["year"] for y in d["years"]] == [2027, 2028, 2029, 2030]
    marks = [(y["year"], m["claim"], m["kind"]) for y in d["years"] for m in y["marks"]]
    assert marks == [(2027, "c2", "rival_until"), (2028, "c3", "due"), (2030, "c4", "due")]
    assert d["dated"] == 3 and d["dated"] + d["undated"] == len(DOC["claims"])
    assert d["with_test"] == 2  # a date on a claim no reading tests settles nothing when it passes
    assert not any(m["passed"] for y in d["years"] for m in y["marks"])
    late = ol.figures({**DOC, "as_of": "2028-01-02"})["due"]
    assert [m["passed"] for y in late["years"] for m in y["marks"]] == [True, False, False]
    both = ol.figures({**DOC, "claims": [_c("z", "a", "both", test=True, due="2029-01-01", rival_until="2027-01-01")]})["due"]
    assert [(y["year"], len(y["marks"])) for y in both["years"]] == [(2029, 1)]  # one claim, one mark


def test_the_committed_export_carries_the_figures_and_they_agree_with_the_page():
    fig = REAL["figures"]
    assert set(REAL) >= {"as_of", "essay", "facts", "sources", "tests", "folios", "positions", "claims", "tally", "scenarios", "shifts", "agree"}
    assert fig == ol.figures({k: v for k, v in REAL.items() if k != "figures"})
    claims = {c["id"]: c for c in REAL["claims"]}
    assert REAL["tally"] == {k: sum(1 for c in claims.values() if c["state"] == k) for k in ol.STATES}
    assert all(fig["counts"][k] == REAL["tally"][k] for k in ("holding", "failing", "both"))
    assert fig["counts"]["waiting"] + fig["counts"]["no_test"] == REAL["tally"]["untestable"]
    drawn = [x["id"] for x in _sides(fig)]
    assert sorted(drawn) == sorted(p["id"] for p in REAL["positions"] if not p.get("layer")) and len(drawn) == len(set(drawn))
    marks = [c for x in _sides(fig) for c in x["claims"]]
    assert sorted(marks) == sorted(claims)  # every claim on the page, once
    assert [f["id"] for f in fig["sides"]["folios"]] == [f["id"] for f in REAL["folios"]]
    shown = {p["id"] for p in REAL["positions"] if p.get("visible")}
    assert {x["id"] for f in fig["sides"]["folios"] for d in f["main"] for x in (d["left"], d["right"]) if x} >= shown
    assert fig["settle"]["n"] == len(_disputes(fig)) == sum(fig["settle"]["counts"].values())
    assert sum(r["n"] for r in fig["whose"]["rows"]) == len(drawn)
    assert fig["due"]["dated"] == sum(1 for c in claims.values() if c["due"] or c["rival_until"])


def test_the_new_plates_are_named_in_the_essay_the_page_and_the_validation():
    essay, page = ol.ESSAY.read_text(), (WEB / "app" / "outlook" / "page.tsx").read_text()
    for name in NEW:
        assert name in ol.PLATES and essay.count(f"[plate:{name}]") == 1 and re.search(rf"\b{name}: <", page), name
    assert ol.essay_problems(essay, ol.load()) == []
    assert ol.PLATES[:6] == ("frontier", "reliability", "adoption", "stack", "scenarios", "board")  # the figures already there stay
    assert all(f"[plate:{p}]" in essay for p in ol.PLATES)
    assert len(ol.TOKEN.sub("", essay).split()) <= 3150  # a figure is introduced by a sentence at most


def _figures(src):
    return ["<Figure" + b.split("</Figure>")[0] for b in src.split("<Figure")[1:]]


def test_each_figure_states_its_kind_and_has_a_key_and_a_foot():
    src = FIGS.read_text()
    blocks = _figures(src)
    assert 3 <= len(blocks) <= 5
    for b in blocks:
        assert re.search(r'id="fig-[a-z-]+"', b) and "KIND_LABEL." in b.split("foot=")[0] and "foot=" in b and "keys=" in b, b[:80]
    charts = [b for b in blocks if "KIND_LABEL.chart" in b]
    assert charts and all("table=" in b for b in charts)  # a chart's numbers are folded beneath it
    assert "hatch" not in src and "hatch" not in PARTS.read_text()  # these figures count records; none draws a judgement
    page = (WEB / "app" / "outlook" / "page.tsx").read_text()
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name


def test_the_figures_say_what_the_marks_do_not_mean():
    src = FIGS.read_text()
    part = lambda name: src.split(f"export function {name}")[1].split("\nexport function ")[0]  # noqa: E731
    sides, settle, whose, due = (part(n) for n in ("SidesMap", "DisputeReach", "WhoseBars", "DueCalendar"))
    # a mark is tonight's reading of a claim, not a score for whoever wrote it; a claim that can't be tested is not wrong
    assert "not a score" in sides and "is not wrong" in sides and "counted once" in sides
    assert "made by Anthropic" in sides and "made by Anthropic" in whose  # whose model drafted them, where labs are drawn
    assert "does not say which side is right" in settle
    assert "not a ranking" in whose
    assert "no reading tests" in due
    for phrase in ("Who is right", "winning", "ahead of", "settled tonight"):
        assert phrase not in src, phrase


def test_the_figures_words_type_no_digit_but_years_and_no_number_word():
    for f in (FIGS, PARTS):
        src = f.read_text()
        words = re.findall(r'(?:title|label|note|tableLabel)="([^"]+)"', src) + re.findall(r">([^<>{}]*[a-z]{3}[^<>{}]*)<", src)
        # the words kept in maps; a string with a hyphenated token is a list of style classes, not words
        words += [w for w in re.findall(r'"([^"]*[a-z]{3} [^"]*)"', src) if not re.search(r"(^| )[a-z:]+-[a-z0-9\[]", w)]
        assert words, f
        for w in words:
            assert not re.search(r"\d", re.sub(r"\b(19|20)\d\d\b|&[a-z]+;", "", w)), w
            assert not NUMBER_WORD.search(w), w
