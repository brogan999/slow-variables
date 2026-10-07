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
NEW = ("method", "settle", "whose", "due")  # the sides map is the page's summary, drawn above the essay, not a plate
PAGE = WEB / "app" / "outlook" / "page.tsx"


def _p(i, rival, folio="capability", attribution="author", visible=False, layer=None, holders=()):
    return {"id": i, "rival": rival, "folio": folio, "attribution": attribution, "visible": visible, "title": i.upper(),
            "holders": list(holders), **({"layer": layer} if layer else {})}


def _c(i, position, state, test=False, attribution="author", due=None, rival_until=None, folio="capability", rival_test=False):
    return {"id": i, "position": position, "state": state, "test": {"fact": "f", "gt": 1} if test else None,
            "rival_test": {"fact": "f", "lt": 1} if rival_test else None,
            "attribution": attribution, "due": due, "rival_until": rival_until, "folio": folio, "text": f"Claim {i}."}


DOC = {
    "as_of": "2026-10-05",
    "folios": [{"id": "capability", "kicker": "First?"}, {"id": "value", "kicker": "Second?"}],
    # two sources can be the same writer: s1 and s4 are both Ann's
    "sources": [{"id": "s1", "who": "Ann"}, {"id": "s2", "who": "Bo"}, {"id": "s3", "who": "Cy"}, {"id": "s4", "who": "Ann"}],
    "positions": [
        _p("a", "b", visible=True, holders=["s1"]), _p("b", "a", attribution="site"),
        _p("c", "a", attribution="extension", holders=["s1", "s2"]),
        _p("d", "none_found", folio="value", attribution="site", layer="model"),
        _p("e", "f", folio="value", holders=["s2"]), _p("f", "e", folio="value", holders=["s3"]),
        _p("g", "e", folio="value", visible=True, holders=["s4"]),
    ],
    "claims": [
        _c("c1", "a", "holding", test=True, rival_test=True), _c("c2", "a", "both", test=True, rival_until="2027-12-31"),
        _c("c3", "c", "untestable", due="2028-06-30", attribution="site"),
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
    assert set(F) == {"looks", "texts", "counts", "holding_no_rival_test", "sides", "settle", "whose", "due"}
    assert F["texts"]["c1"] == "Claim c1."  # a mark is named without hovering over a token


def test_every_claim_has_one_look_and_the_looks_sum_to_the_pages_tally():
    assert F["looks"] == {"c1": "holding", "c2": "both", "c3": "no_test", "c4": "waiting", "c5": "failing", "c6": "no_test"}
    assert set(F["counts"]) == set(ol.LOOKS) and sum(F["counts"].values()) == len(DOC["claims"])
    assert all(F["counts"][k] == DOC["tally"][k] for k in ("holding", "failing", "both"))
    assert F["counts"]["waiting"] + F["counts"]["no_test"] == DOC["tally"]["untestable"]  # the page's word, split by why


def test_each_position_on_the_page_is_drawn_once_and_each_claim_is_counted_once():
    s = F["sides"]
    assert sorted(x["id"] for x in _sides(F)) == ["a", "b", "c", "e", "f", "g"]  # the layer unit lives on its layer page
    assert s["positions"] == 6 and s["layer_positions"] == 1 and s["positions"] + s["layer_positions"] == len(DOC["positions"])
    marks = [c for x in _sides(F) for c in x["claims"]]
    assert sorted(marks) == sorted(c["id"] for c in DOC["claims"]) and s["claims"] == len(marks) == len(set(marks))
    assert {k: sum(f["counts"][k] for f in s["folios"]) for k in ol.LOOKS} == F["counts"]  # by question, the same claims
    assert all(f["claims"] == sum(f["counts"].values()) for f in s["folios"]) and sum(f["positions"] for f in s["folios"]) == s["positions"]
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


def test_a_dispute_read_on_a_failed_claim_is_not_drawn_like_one_read_on_a_claim_that_held():
    s = F["settle"]
    cells = {c["key"]: c for r in s["rows"] for c in r["cells"]}
    # a: its holding claim carries a test of what the rival expects. e: the only line read was missed.
    assert {k: c["mark"] for k, c in cells.items()} == {"a": "told_apart", "c": "no_test", "e": "missed", "g": "no_test"}
    assert all(c["mark"] in ol.SETTLE_MARKS and (c["mark"] == c["reach"]) == (c["reach"] != "read") for c in cells.values())
    assert s["marks"] == {"told_apart": 1, "held": 0, "missed": 1, "shared": 0, "waiting": 0, "no_test": 2}
    assert s["told_apart"] == 1 and s["dark"] == s["marks"]["told_apart"] + s["marks"]["held"] == 1  # dark never stands for a failed test
    assert s["marks"]["told_apart"] + s["marks"]["held"] + s["marks"]["missed"] == s["counts"]["read"]
    for r in s["rows"]:
        assert sum(r["marks"].values()) == r["n"] and set(r["marks"]) == set(ol.SETTLE_MARKS)
    one = lambda *cl: ol.figures({**DOC, "claims": list(cl)})["settle"]["rows"][0]["cells"][0]["mark"]  # noqa: E731
    assert one(_c("x", "a", "holding", test=True)) == "held"  # met its line; what the rival expects is not written down
    assert one(_c("x", "a", "holding", test=True), _c("y", "b", "failing", test=True)) == "held"  # a claim that held comes first
    assert one(_c("x", "a", "failing", test=True), _c("y", "a", "both", test=True, rival_test=True)) == "missed"
    assert F["holding_no_rival_test"] == 0
    assert ol.figures({**DOC, "claims": [_c("x", "a", "holding", test=True)]})["holding_no_rival_test"] == 1


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
    assert w["site_readings"] == 2  # c3, c6: this site's reading of a writer's position
    assert w["site_rivals"] == 1  # b: this site's own position, set against a writer's, each naming the other
    assert not any(re.search(r"rate|share|pct|percent|rank", k) for r in w["rows"] for k in r)


def test_whose_arguments_says_how_few_writers_the_positions_rest_on_and_names_none():
    w = F["whose"]
    assert w["named"] == 5  # every drawn position but this site's own
    assert w["writers"] == 3  # Ann, Bo, Cy: a writer is counted once however many of their works are cited
    assert w["top_two"] == 4  # Ann (a, c, g) and Bo (c, e); c credits both and is counted once
    assert not any(isinstance(v, str) for k, v in w.items() if k != "rows")  # a count, never a name


def test_the_calendar_places_each_dated_claim_once_in_its_year_and_leaves_no_year_out():
    d = F["due"]
    assert [y["year"] for y in d["years"]] == [2027, 2028, 2029, 2030]
    marks = [(y["year"], m["claim"], m["kind"]) for y in d["years"] for m in y["marks"]]
    assert marks == [(2027, "c2", "rival_until"), (2028, "c3", "due"), (2030, "c4", "due")]
    assert d["dated"] == 3 and d["dated"] + d["undated"] == len(DOC["claims"])
    assert d["with_test"] == 2  # a date on a claim no reading tests settles nothing when it passes
    assert d["site"] == 1 and {m["claim"]: m["site"] for y in d["years"] for m in y["marks"]} == {"c2": False, "c3": True, "c4": False}
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
    # what the feet say in words has to stay true of the page: most of this site's own positions name no claim yet,
    # and some dated claim has no test (so "for the rest" names something)
    site = next(r for r in fig["whose"]["rows"] if r["id"] == "site")
    assert site["without"] > site["with_claim"] and 0 < fig["whose"]["site_rivals"] <= site["n"]
    assert 0 < fig["due"]["with_test"] < fig["due"]["dated"]
    assert all(c.get("falsifier") for c in claims.values())  # "each names what would prove it wrong"
    # "most claims have no test yet"; "in only ... of the dark disputes"; "the rest"; "the writers are few"
    assert fig["counts"]["no_test"] * 2 > len(claims)
    assert 0 < fig["settle"]["told_apart"] < fig["settle"]["dark"] <= fig["settle"]["counts"]["read"]
    assert 0 < fig["holding_no_rival_test"] <= REAL["tally"]["holding"]
    assert fig["whose"]["top_two"] * 4 > fig["whose"]["named"] and fig["whose"]["writers"] > 2
    assert 0 < fig["due"]["site"] < fig["due"]["dated"]
    # "the side the ledger lists first is on the left ... and never a position this site wrote"
    by = {p["id"]: p for p in REAL["positions"]}
    assert all(by[d["left"]["id"]]["attribution"] != "site" for d in _disputes(fig) if d["kind"] == "pair")
    # "where it reads argues against ... the one on the right does not name it back"
    assert all(by[d["against"]]["rival"] != d["key"] for d in _disputes(fig) if d["kind"] == "challenge")


def test_the_disclosure_prints_only_ties_the_ledger_states_for_writers_who_are_drawn():
    said = FIGS.read_text().split("const DRAFTED")[1].split("\n")[0]
    drawn = [p for p in REAL["positions"] if not p.get("layer")]
    fields = [s["field"] for s in REAL["sources"] if any(s["id"] in p["holders"] for p in drawn)]
    ties = {  # the words in the sentence, and the words in a drawn writer's `field` that back them
        "advisers to it": r"adviser to Anthropic|Anthropic's economic advisory council",
        "at its institute": r"at the Anthropic Institute",
        "a firm that holds a stake in it": r"investment firm that holds stakes in [^;]*Anthropic",
    }
    for words, backing in ties.items():
        assert words in said and any(re.search(backing, f) for f in fields), words
    assert "work for it" not in said  # no drawn writer's field says so


def test_the_new_plates_are_named_in_the_essay_the_page_and_the_validation():
    essay, page = ol.ESSAY.read_text(), PAGE.read_text()
    # the summary of every question is not filed under the first: it is drawn once, above the essay
    assert "sides" not in ol.PLATES and "[plate:sides]" not in essay and not re.search(r"\bsides: <", page)
    assert page.count("<SidesMap ") == 1 and page.index("<SidesMap ") < page.index("<Folios ")
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
    page = PAGE.read_text()
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name


def test_the_figures_say_what_the_marks_do_not_mean():
    src = FIGS.read_text()
    part = lambda name: src.split(f"export function {name}")[1].split("\nexport function ")[0]  # noqa: E731
    sides, settle, whose, due = (part(n) for n in ("SidesMap", "DisputeReach", "WhoseBars", "DueCalendar"))
    # a mark is tonight's reading of a claim, not a score for whoever wrote it; a claim that can't be tested is not wrong
    assert "not a score" in sides and "is not wrong" in sides and "counted once" in sides
    assert "left and right carry no meaning" not in src
    assert "never a position this site wrote" in sides and "does not name it back" in sides
    assert "with its test where it has one" in sides and "listed with its test in" not in sides
    assert "made by Anthropic" in src.split("const DRAFTED")[1].split("\n")[0]  # whose model drafted them
    for block in (sides, settle, whose, due):  # said on every figure that draws positions held by people with ties to a lab
        assert "{DRAFTED}" in block
    assert "this does not say which side is right" in src.split("const REACH_WORD")[1].split("};")[0]
    assert "does not mean either side has the better of the argument" in settle
    assert "no claim on either side has a test" in settle and "in this order" in settle
    assert "where no claim has a test" in settle and "with no test</>" not in settle
    assert "{f.told_apart}" in settle and "{f.dark}" in settle and "{doc.figures.holding_no_rival_test}" in settle
    assert "not a ranking" in whose
    assert "each naming the other as its rival" in whose and "are the named rival of" not in whose
    assert "{f.top_two}" in whose and "{f.named}" in whose and "{f.writers}" in whose
    assert "no reading tests" in due
    assert src.count("the date by which the claim says it will be shown right or wrong") == 2  # the key and the table
    assert "will have happened by then" not in src  # wrong for a claim that says something will not happen
    assert "{d.site}" in due and "<Whose " in due and "the date is this site&apos;s too" in due
    assert "bg-axis" not in due  # a key swatch is an outline: no mark is filled tan
    for phrase in ("Who is right", "winning", "ahead of", "settled tonight"):
        assert phrase not in src, phrase


def test_each_question_on_the_sides_map_is_folded_to_one_line():
    sides = FIGS.read_text().split("export function SidesMap")[1].split("\nexport function ")[0]
    assert sides.count("<details") == 1 and "<summary" in sides  # one fold for each question, none inside it
    summary = sides.split("<summary")[1].split("</summary>")[0]
    assert "fo.kicker" in summary and "<ClaimMarks " in summary and "fo.positions" in summary
    assert "More positions on this question" not in sides
    src = FIGS.read_text()
    assert "↔ each other" in src and "argues against →" in src  # which way a row runs is in its label
    assert "drawn under" in src  # a position argued against under another question names that question


def test_the_method_figures_words_say_what_the_code_does():
    from datetime import date

    src = FIGS.read_text().split("export function MethodFlow")[1].split("\nexport function ")[0]
    day = date(2026, 10, 1)
    f = {"a": {"value": 1.0, "as_of": "2026-09-01"}, "old": {"value": 1.0, "as_of": "2025-01-01", "stale": True}}
    meets, misses, gone = {"fact": "a", "gt": 0.5}, {"fact": "a", "gt": 2}, {"fact": "missing", "gt": 0}
    state = lambda c, facts=f, today=day: ol.state(c, facts, today)  # noqa: E731
    # gate one: no test, no reading, or the reading it is compared with too old
    assert state({}) == state({"test": gone}) == state({"test": {"fact": "old", "gt": 0}}) == state({"test": {"fact": "a", "gt": "old"}}) == "untestable"
    assert "when the reading or the reading it is compared with is missing or too old" in src
    # ... or short of a line whose date has not come; a dated claim that already meets its line does not wait
    assert state({"test": misses, "due": "2027-12-31"}) == "untestable" and state({"test": meets, "due": "2027-12-31"}) == "holding"
    assert "by a date that has not come and the reading is still short of it" in src
    # an unreadable rival test blocks a win, never a loss
    assert state({"test": meets, "rival_test": gone}) == "untestable" and state({"test": misses, "rival_test": gone}) == "failing"
    assert "A claim that meets its line also can&apos;t be tested while its rival&apos;s test has no reading" in src
    assert "a claim that misses its line is failing either way" in src
    # the rival's date: after it the rival test no longer applies, and a shared reading becomes the claim's own
    shared = {"test": meets, "rival_test": meets, "rival_until": "2026-12-31"}
    late = {"a": {"value": 1.0, "as_of": "2027-01-05"}}
    assert state(shared) == "both" and state(shared, late) == "holding" and state({"test": meets}) == "holding"
    assert re.search(r"no, the rival names no test, or the rival(&apos;|')s date has passed", src)
    # the clock is the reading's own date, not the calendar
    assert state(shared, f, date(2027, 6, 1)) == "both" and state({"test": misses, "due": "2026-12-31"}, f, date(2027, 6, 1)) == "untestable"
    assert state({"test": misses, "due": "2026-12-31"}, late, date(2027, 6, 1)) == "failing"
    assert "A date has come when the reading itself is dated on or after it, not when the calendar says so" in src  # `clock < due`
    # a running record is the one case the calendar counts: `grace_days`
    record = {"test": misses, "due": "2026-12-31", "grace_days": 90}
    assert state(record, f, date(2027, 3, 1)) == "untestable" and state(record, f, date(2027, 6, 1)) == "failing"
    assert "only for a record that moves just when it is broken does the calendar count" in src
    assert "not that the rival expected otherwise" in src and src.count("{f.holding_no_rival_test}") == 2  # the foot and the end box
    assert "aria-hidden" not in PARTS.read_text().split("export function Onward")[1]  # a screen reader hears the answers too


def test_the_pages_older_words_no_longer_say_every_claim_is_tested():
    essay = ol.ESSAY.read_text()
    old = "Each claim is tested every night"
    assert old not in (WEB / "components" / "OutlookParts.tsx").read_text() and old not in (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert "Each claim that has a test is read every night against one reading and one line" in (WEB / "components" / "OutlookParts.tsx").read_text()
    assert "a claim with no test reads can&apos;t be tested yet" in (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert "Most claims have no test yet. The tests that exist run every night" in essay and "is listed with its test, tonight" not in essay
    for text in (essay, PAGE.read_text()):  # the lede and the page's description promise only what the page has
        assert "and, where this site has one, the reading that would tell the sides apart" in text
    assert "Some claims carry a deadline of their own" not in essay
    assert "Some claims name a date, a few of them a date this site set where the writer gave none, and the calendar shows the year in which each date falls." in essay
    # the owner's to settle, not this change's: the essay's credit for the commodity view is left as it was
    assert "Narayanan and Kapur's commodity view wins" in essay


def test_the_figures_words_type_no_digit_but_years_and_no_number_word():
    for f in (FIGS, PARTS):
        src = f.read_text()
        words = re.findall(r'(?:title|label|note|tableLabel)="([^"]+)"', src) + re.findall(r">([^<>{}]*[a-z]{3}[^<>{}]*)<", src)
        # the words kept in maps; a string with a hyphenated token is a list of style classes, not words
        words += [w for w in re.findall(r'"([^"]*[a-z]{3} [a-z]{2,}[^"]*)"', src) if not re.search(r"(^| )[a-z:]+-[a-z0-9\[]", w)]
        assert words, f
        for w in words:
            assert not re.search(r"\d", re.sub(r"\b(19|20)\d\d\b|&[a-z]+;", "", w)), w
            assert not NUMBER_WORD.search(w), w
