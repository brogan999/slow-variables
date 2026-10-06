"""The predictions board's figures: every count and position is the export's, so the page only places it."""

import copy
import json
import re
from pathlib import Path

from ai_tracker import board

from .test_board import ARGUMENT, JUDGED, LEANS, OUTLOOK, SPEC
from .test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
LEDGER = [
    {"id": "p1", "claimant": "Lab (Ann, Bo et al.)", "status": "behind", "window_end": "2020-06-30", "claim_url": None,
     "related_indicators": ["i1"]},
    {"id": "p2", "claimant": "Lab", "status": "confirmed", "window_end": "2027-12-31", "claim_url": None, "related_indicators": []},
    {"id": "p3", "claimant": "Lab", "status": None, "window_end": "2090-01-01", "claim_url": None, "related_indicators": []},
    {"id": "p4", "claimant": "Quiet Writer", "status": "emerging", "window_end": None, "claim_url": None, "related_indicators": []},
]


ALIASES = {"Lab Group": "Lab", "Quiet Writer": "Q. Writer (Quiet House)"}
FALSE_PHRASES = (  # what the staff review of 6 Oct 2026 found untrue or misleading in the figures' words
    "Who is right so far", "name no date", "never not happening", "a reading has tested", "a reading cannot test",
    "A model of the method", "A reading arrives", "when a reading arrives", "Given a test", "tested forecast",
)


def _doc(judged=JUDGED, ledger=LEDGER, aliases=None):
    spec = {**SPEC, "leans": LEANS, "ledger": {k: {"folio": "capability", "line": "A plain line."} for k in ("p1", "p2", "p3", "p4", "p5")}}
    spec = {**spec, **({"forecaster_aliases": aliases} if aliases else {})}
    judged = judged and {**judged, "judgements": [*judged["judgements"], {"kind": "ledger", "id": "p3", "lean": "likely_false", "reason": "r", "rests_on": []}]}
    return board.build(
        spec, ledger, OUTLOOK, ARGUMENT, [{"id": "e1", "state": "contradicted"}],
        [{"monitor": "e1", "label": "Profit moves", "text": "If profit moves."}], {}, judged,
    )


def _rows(doc):
    return [r for f in doc["folios"] for r in f["rows"]]


def test_the_figures_change_no_word_and_no_tally():
    doc = _doc()
    bare = {k: v for k, v in doc.items() if k != "figures"}
    before = copy.deepcopy(bare)
    assert board.figures(bare) == doc["figures"] and bare == before  # pure: it reads the board and writes nothing to it
    assert doc["tally"] == {w: sum(1 for r in _rows(doc) if r["word"] == w) for w in board.ORDER}
    assert {r["id"]: r["word"] for r in _rows(doc)} == {
        "p1": "slower", "p2": "happening", "p3": "too_early", "p4": "too_early",
        "c1": "both", "c2": "too_early", "m1": "not_happening", "e1": "not_happening",
    }


def test_the_tally_by_section_sums_to_the_board_and_every_bar_ends_at_one_hundred():
    doc = _doc()
    whole, *sections = doc["figures"]["sections"]
    assert whole["id"] == "all" and whole["counts"] == doc["tally"] and whole["n"] == doc["n"]
    assert [s["id"] for s in sections] == [f["id"] for f in doc["folios"]]
    assert {w: sum(s["counts"][w] for s in sections) for w in board.ORDER} == doc["tally"]
    for s in doc["figures"]["sections"]:
        assert s["n"] == sum(s["counts"].values()) and [b["n"] for b in s["bar"]] == [s["counts"][b["word"]] for b in s["bar"]]
        assert s["bar"][0]["x"] == 0 and abs(s["bar"][-1]["x"] + s["bar"][-1]["w"] - 100) < 1e-6
        assert all(abs(a["x"] + a["w"] - b["x"]) < 1e-6 and a["w"] > 0 for a, b in zip(s["bar"], s["bar"][1:]))


def test_the_calendar_places_every_dated_forecast_once_and_counts_the_rest():
    doc = _doc()
    cal = doc["figures"]["calendar"]
    marks = [m for b in cal["bins"] for m in b["marks"]]
    assert sorted(m["key"] for m in marks) == ["ledger-p1", "ledger-p2", "ledger-p3"]  # a falsifier in words is not a date
    assert cal["dated"] == 3 and cal["dated"] + cal["undated"] == doc["n"]
    assert all(b["n"] == len(b["marks"]) == sum(b["counts"].values()) and b["n"] for b in cal["bins"])
    by = {m["key"]: (b["label"], m) for b in cal["bins"] for m in b["marks"]}
    assert by["ledger-p1"][0] == "Before 2026" and by["ledger-p1"][1]["due"] and by["ledger-p1"][1]["word"] == "slower"
    assert by["ledger-p2"][0] == "2027" and not by["ledger-p2"][1]["due"]
    assert by["ledger-p3"][0] == "After 2050"
    assert all(m["href"] and m["who"] for m in marks)


def test_who_is_right_counts_by_kind_of_source_and_by_forecaster_without_a_rate():
    doc = _doc()
    fig = doc["figures"]
    tested = {w: n for w, n in doc["tally"].items() if w != "too_early"}
    assert {w: sum(s["counts"][w] for s in fig["sources"]) for w in tested} == tested
    assert sum(s["too_early"] for s in fig["sources"]) == doc["tally"]["too_early"]
    assert sum(s["n"] for s in fig["sources"]) == doc["n"]
    for s in fig["sources"]:  # one mark for each forecast a reading has tested; the untested ones are a count
        assert len(s["marks"]) == sum(s["counts"].values()) == s["n"] - s["too_early"]
    who = {f["who"]: f for f in fig["forecasters"]}
    assert list(who) == sorted(who, key=str.casefold)  # alphabetical: no ranking on a handful of forecasts
    assert set(who) == {"Ann Author", "Lab"}  # the site's own are in the kinds of source; the untested writer is left out
    assert fig["forecasters_left_out"] == {"n": 1, "names": [{"who": "Quiet Writer", "n": 1}]}  # counted and named, not dropped
    assert [m["word"] for m in who["Lab"]["marks"]] == ["happening", "slower", "too_early"]  # one name however it is credited
    assert who["Lab"]["n"] == 3 and who["Lab"]["counts"] == {"happening": 1, "not_happening": 0, "slower": 1, "both": 0, "too_early": 1}
    assert not any(re.search(r"rate|share|pct|percent", k) for f in fig["forecasters"] + fig["sources"] for k in f)


def test_the_sites_warning_signs_have_a_row_of_their_own_and_the_rows_still_sum():
    doc = _doc()
    rows = {s["id"]: s for s in doc["figures"]["sources"]}
    assert list(rows) == ["ledger", "writers", "exits", "site"]  # no claim extends a writer in this fixture
    # a warning sign that reads not happening means the site's argument stands: it is not one of the site's misses
    assert rows["exits"]["n"] == 1 and rows["exits"]["counts"]["not_happening"] == 1 and [m["key"] for m in rows["exits"]["marks"]] == ["exit-e1"]
    assert rows["site"]["n"] == 2 and rows["site"]["counts"]["not_happening"] == 1 and rows["site"]["too_early"] == 1
    assert [m["key"] for m in rows["site"]["marks"]] == ["migration-m1"]
    assert sum(s["n"] for s in rows.values()) == doc["n"]
    assert sum(s["counts"]["not_happening"] for s in rows.values()) == doc["tally"]["not_happening"]
    assert rows["ledger"]["counts"]["not_happening"] == 0  # a dated claim by someone else has no word for wrong


def test_one_forecaster_credited_under_two_names_is_one_row():
    ledger = [*LEDGER, {"id": "p5", "claimant": "Lab Group (Ann, Bo)", "status": "ahead", "window_end": None, "claim_url": None,
                        "related_indicators": []}]
    plain, merged = _doc(ledger=ledger), _doc(ledger=ledger, aliases=ALIASES)
    assert {"Lab", "Lab Group"} <= {f["who"] for f in plain["figures"]["forecasters"]}
    who = {f["who"]: f for f in merged["figures"]["forecasters"]}
    assert "Lab Group" not in who and who["Lab"]["n"] == 4  # the alias is applied after the trailing bracket is dropped
    assert who["Lab"]["counts"]["happening"] == 2 and len(who["Lab"]["marks"]) == 4
    assert merged["figures"]["forecasters_left_out"]["names"] == [{"who": "Q. Writer (Quiet House)", "n": 1}]  # an alias may restore a house
    strip = lambda d: {k: v for k, v in d.items() if k != "figures"}  # noqa: E731
    assert strip(plain) == strip(merged)  # the merge is the figure's alone: no row, word or tally moves
    assert {r["id"]: r["who"] for r in _rows(merged)}["p5"] == "Lab Group (Ann, Bo)"  # the ledger's own credit stays


def test_no_forecaster_is_dropped_between_the_drawn_and_the_left_out():
    fig = _doc(aliases=ALIASES)["figures"]
    named = [r for r in _rows(_doc()) if not r["who"].startswith("This site")]
    assert sum(f["n"] for f in fig["forecasters"]) + sum(f["n"] for f in fig["forecasters_left_out"]["names"]) == len(named)
    assert fig["forecasters_left_out"]["n"] == len(fig["forecasters_left_out"]["names"])


def _span(label):
    if m := re.fullmatch(r"Before (\d{4})", label):
        return range(0, int(m[1]))
    if m := re.fullmatch(r"After (\d{4})", label):
        return range(int(m[1]) + 1, 9999)
    a, b = re.fullmatch(r"(\d{4})(?: to (\d{4}))?", label).groups()
    assert int(b or a) >= int(a), label
    return range(int(a), int(b or a) + 1)


def test_no_two_calendar_rows_cover_the_same_year_whatever_the_boards_date():
    for now in range(2026, 2046):
        labels = {board._bin(y, now)[1] for y in range(now - 3, 2070)}
        for y in range(now - 3, 2070):  # a year sits under the one label that names it
            assert [lab for lab in labels if y in _span(lab)] == [board._bin(y, now)[1]], (now, y)


def test_the_leans_are_drawn_either_side_of_a_centre_line_and_sum_to_the_judged_tally():
    doc = _doc()
    leans = doc["figures"]["leans"]
    whole, *sections = leans["rows"]
    assert whole["id"] == "all" and whole["counts"] == doc["judged"]["tally"] and whole["n"] == sum(doc["judged"]["tally"].values())
    assert whole["n"] + whole["unjudged"] == doc["tally"]["too_early"]
    assert {w: sum(s["counts"][w] for s in sections) for w in LEANS} == doc["judged"]["tally"]
    for r in leans["rows"]:
        assert r["true"] == r["counts"]["likely_true"] + r["counts"]["leans_true"]
        assert r["false"] == r["counts"]["likely_false"] + r["counts"]["leans_false"]
        assert all(0 <= b["x"] and b["x"] + b["w"] <= 100 + 1e-6 and b["w"] > 0 for b in r["bar"])
        for b in r["bar"]:  # true to the left of the centre, false to the right, a toss-up across it
            side = b["lean"].split("_")[1]
            assert (side == "true" and b["x"] + b["w"] <= leans["centre"] + 1e-6) or (side == "false" and b["x"] >= leans["centre"] - 1e-6) or (
                side == "up" and abs(b["x"] + b["w"] / 2 - leans["centre"]) < 1e-6
            )
    assert any(abs(r["bar"][0]["x"]) < 1e-6 or abs(r["bar"][-1]["x"] + r["bar"][-1]["w"] - 100) < 1e-6 for r in leans["rows"])  # the scale is used
    assert "leans" not in _doc(None)["figures"]  # no judgement, no figure of one


def test_the_flow_counts_are_the_boards():
    doc = _doc()
    flow = doc["figures"]["flow"]
    assert flow["stated"] == doc["n"] == flow["tested"] + flow["too_early"]
    assert flow["too_early"] == doc["tally"]["too_early"] == flow["leaned"] + flow["unleaned"]
    assert flow["leaned"] == sum(doc["judged"]["tally"].values())


def test_the_committed_export_carries_the_figures_the_page_reads():
    doc = json.loads((ROOT / "web/data/board.json").read_text())
    fig = doc["figures"]
    assert fig["sections"][0]["counts"] == doc["tally"] and fig["flow"]["stated"] == doc["n"]
    assert fig["calendar"]["dated"] + fig["calendar"]["undated"] == doc["n"]
    assert fig["leans"]["rows"][0]["counts"] == doc["judged"]["tally"]
    rows = [r for f in doc["folios"] for r in f["rows"]]
    assert doc["tally"] == {w: sum(1 for r in rows if r["word"] == w) for w in board.ORDER}
    src = {s["id"]: s for s in fig["sources"]}
    exits = [r for r in rows if r["kind"] == "exit"]
    assert src["exits"]["n"] == len(exits) and all(m["key"].startswith("exit-") for m in src["exits"]["marks"])
    assert not any(m["key"].startswith("exit-") for m in src["site"]["marks"])
    assert sum(s["n"] for s in fig["sources"]) == doc["n"]
    drawn, left = fig["forecasters"], fig["forecasters_left_out"]
    assert left["n"] == len(left["names"]) and sum(f["n"] for f in drawn + left["names"]) == sum(1 for r in rows if not r["who"].startswith("This site"))
    surnames = lambda who: frozenset(p.split()[-1] for p in re.split(r",| and | & ", re.sub(r"\s*\([^)]*\)$", "", who)) if p.strip())  # noqa: E731
    names = [f["who"] for f in drawn + left["names"]]
    assert len({surnames(n) for n in names}) == len(names)  # the same people in another order or spelling are one row
    assert not any(NUMBER_WORD.search(n) for n in names)  # a name drawn on the page types no number word


def test_what_the_forecaster_figures_foot_says_of_named_people_is_still_true():
    """The foot names no one, but it says a lab's chief executive is drawn, what one of his marks is scored on, and that
    heads of other labs are left out. If the board moves, the sentence must move with it."""
    fig = json.loads((ROOT / "web/data/board.json").read_text())["figures"]
    amodei = next(f for f in fig["forecasters"] if f["who"] == "Dario Amodei")
    assert [m["key"] for m in amodei["marks"] if m["word"] == "happening"] == ["ledger-anthropic_10x_per_year"]
    assert {"Sam Altman", "Demis Hassabis"} <= {f["who"] for f in fig["forecasters_left_out"]["names"]}


def test_the_page_draws_at_least_five_figures_and_each_says_what_kind_it_is():
    src = (ROOT / "web/src/components/BoardFigures.tsx").read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z-]+)"[^>]*?note=\{?("[^"]+"|KIND_LABEL\.[a-z]+)', src, re.S)
    assert len(figures) >= 5, figures
    assert len(re.findall(r"<Figure\b", src)) == len(figures)  # none without a stated kind
    assert len(re.findall(r"\bfoot=", src)) == len(figures)  # each says what it draws and what it leaves out
    lean = src.split("export function LeanBars")[1].split("\nexport function ")[0]
    assert "judgement" in lean and "hatched" in lean  # a model's lean is labelled and hatched wherever it is drawn
    assert src.count("hatched") == lean.count("hatched")  # and nothing else is
    page = (ROOT / "web/src/app/predictions/page.tsx").read_text()
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name
    assert "<Rows " in page  # the figures summarise; the rows stay the record


def test_the_figures_words_say_only_what_the_scoring_supports():
    src = (ROOT / "web/src/components/BoardFigures.tsx").read_text()
    for phrase in FALSE_PHRASES:
        assert phrase not in src, phrase
    part = lambda name: src.split(f"export function {name}")[1].split("\nexport function ")[0]  # noqa: E731
    sources, leans, cal, who, flow = (part(n) for n in ("SourceMarks", "LeanBars", "DueCalendar", "ForecasterMarks", "BoardFlow"))
    assert "this family has no word for wrong" in sources and "A warning sign is the reverse of a forecast" in sources
    # the calendar leaves out rows with no closing date on record; it does not say they name none
    assert "gives them no closing date, though some name a year in their own words" in cal and "closing date on record" in cal
    assert "figures.forecasters_left_out" in who and "has no word for wrong" in who
    assert "made by Anthropic" in who and "chief executive" in who  # whose model drafts the page, and who is among the names
    note = re.search(r'note="([^"]+)"', leans)[1]
    foot = leans.split("foot=")[1]
    assert "Anthropic" in note and foot.index("Anthropic") < foot.index("A bar is")  # the disclosure comes first
    assert "A drawing of the method, not a measurement" in flow and "for someone else&apos;s dated claim, an outside check" in flow
    assert "MarkList" in sources and "MarkList" in cal and "MarkList" in who  # which forecast each mark is, without hover
    parts = (ROOT / "web/src/components/diagrams/board.tsx").read_text()
    assert "h-4 w-4" in parts and "p-1" in parts  # a mark's tap target is larger than the mark


def test_the_figures_words_type_no_digit_but_years_and_no_number_word():
    for f in ("web/src/components/BoardFigures.tsx", "web/src/components/diagrams/board.tsx"):
        src = (ROOT / f).read_text()
        words = re.findall(r'(?:title|label|note|tableLabel)="([^"]+)"', src) + re.findall(r">([^<>{}]*[a-z]{3}[^<>{}]*)<", src)
        assert words or "diagrams" in f, f  # the parts carry no words of their own
        for w in words:
            assert not re.search(r"\d", re.sub(r"\b(19|20)\d\d\b|&[a-z]+;", "", w)), w
            assert not NUMBER_WORD.search(w), w
