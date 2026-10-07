"""The figures on /singularity (Part 45k). Every count and position is laid out by singularity.figures from the built
page (its lanes, its due list, its worlds), the outlook's scenario grid and the Futures idea bank; the web only places
it. The figures change no forecast, outcome or record."""

import copy
import json
import re
from collections import Counter
from pathlib import Path

from ai_tracker import futures
from ai_tracker import singularity as sg

from .test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
FIGS = WEB / "components" / "LongRunFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "longrun.tsx"
PAGE = WEB / "app" / "singularity" / "page.tsx"
DOC = json.loads((ROOT / "web" / "data" / "singularity.json").read_text())
F = DOC.get("figures") or {}
TOP = {"as_of", "intro", "axis", "lanes", "due", "table", "stops", "tallies", "questions", "worlds", "fiction", "fiction_slots",
       "sources", "words"}  # what the page read before the figures


def _m(i, made, lane_x=None, *, low=None, mid=None, high=None, settles=None, step=False, word="too_early", undated=False):
    at = None if undated else mid or high
    return {
        "id": i, "who": f"Writer {i}", "line": "A plain line.", "made": made, "made_year": int(made[:4]), "step": step,
        "low": low, "mid": mid, "high": high, "x_low": sg.x(low) if low else None, "x_high": sg.x(high) if high else None,
        "x": sg.x(at) if at else None, "word": word, "settles": settles, "href": f"/predictions#{i}",
        "years": None if at is None else str(at),
    }


def _doc(lanes, as_of="2026-10-06", worlds=()):
    built = [{"id": k, "label": k.upper(), "forecasts": [m for m in ms if m["x"] is not None],
              "undated": [m for m in ms if m["x"] is None]} for k, ms in lanes.items()]
    flat = [{**m, "lane": la["id"]} for la in built for m in la["forecasts"] + la["undated"]]
    return {"as_of": as_of, "lanes": built, "due": sorted((m for m in flat if m["settles"] and m["settles"] < as_of), key=lambda m: m["settles"]),
            "worlds": list(worlds), "words": {"happening": "Happening", "slower": "Slower than said", "too_early": "Too early to tell"}}


GRID = {
    "progress": [{"id": "steady", "label": "Steady"}, {"id": "fast", "label": "Fast"}],
    "rules": [{"id": "unclear", "label": "Unsettled"}, {"id": "licensed", "label": "Licensed"}],
    "cells": [
        {"progress": "steady", "rules": "unclear", "consistent": True, "tested": True, "signposts": [{"claim": "c1", "state": "both"}]},
        {"progress": "fast", "rules": "unclear", "consistent": False, "tested": True,
         "signposts": [{"claim": "c2", "state": "failing"}, {"claim": "c3", "state": "untestable"}]},
        {"progress": "fast", "rules": "licensed", "consistent": True, "tested": False, "signposts": []},
    ],
}
WORLDS = [
    {"id": "slow", "label": "Slow", "short": "Slow", "consistent": True, "grid": [{"progress": "steady", "rules": "unclear"}]},
    {"id": "quick", "label": "Quick", "short": "Quick", "consistent": False,
     "grid": [{"progress": "fast", "rules": "unclear"}, {"progress": "fast", "rules": "licensed"}]},
]
IDEAS = [
    {"imagined": 1901, "arrival": {"state": "marked_built", "kind": "year", "year": 1909, "decade": 1900, "lag_years": 8}},
    {"imagined": 1955, "arrival": {"state": "marked_built", "kind": "decade", "year": None, "decade": 1970, "lag_decades": 2}},
    {"imagined": 1958, "arrival": {"state": "marked_built", "kind": "year", "year": 1979, "decade": 1970, "lag_years": 21}},
    {"imagined": 1700, "arrival": {"state": "marked_built", "kind": "year", "year": 1990, "decade": 1990, "lag_years": 290}},
    {"imagined": 1950, "arrival": {"state": "marked_built_date_unclear"}},
    {"imagined": 1950, "arrival": {"state": "already_existed", "kind": "year", "year": 1940, "decade": 1940}},
    {"imagined": 1950, "arrival": {"state": "not_marked_built"}},
]


def _small():
    agi = [_m(f"a{k}", f"{2019 + k}-06-01", high=y) for k, y in enumerate((2027, 2030, 2040, 2029, 2028, 2060))]
    agi += [_m("a_step", "2025-01-01", high=2026, step=True), _m("a_odds", "2024-01-01", undated=True),
            _m("a_range", "2010-01-01", low=2030, mid=2040, high=2070)]
    coder = [_m("c1", "2025-04-03", high=2027), _m("c2", "2025-04-03", high=2027)]  # made the same day for the same year
    growth = [_m("g_old", "1965-01-01", high=2000, settles="2000-12-31", word="slower"),
              _m("g_done", "2025-04-03", high=2025, settles="2025-12-31", word="happening"),
              _m("g_open", "2001-01-01", mid=2025, word="slower")]  # its year has passed; no closing date on record
    return _doc({"agi": agi, "superhuman_coder": coder, "explosive_growth": growth}, worlds=WORLDS)


def test_the_figures_add_a_block_and_change_no_field_the_page_already_read():
    assert set(DOC) == TOP | {"figures"}
    assert set(F) == {"spread", "said", "due", "worlds", "lag"}
    bare = {k: v for k, v in DOC.items() if k != "figures"}
    before = copy.deepcopy(bare)
    again = sg.figures(bare, GRID, futures.ideas())
    assert bare == before  # pure: it reads the built page and writes nothing to it
    assert all(again[k] == F[k] for k in ("spread", "said", "due", "lag"))  # and these are drawn from the page's own records alone


def test_the_spread_counts_every_forecast_in_its_lane_once():
    lanes = {la["id"]: la for la in DOC["lanes"]}
    assert [s["id"] for s in F["spread"]["lanes"]] == list(lanes)
    for s in F["spread"]["lanes"]:
        la = lanes[s["id"]]
        dated = [m for m in la["forecasts"] if not m["step"]]
        assert s["n_dated"] == len(dated) == len(s["marks"]) and s["n_steps"] == len(la["forecasts"]) - len(dated)
        assert s["n_undated"] == len(la["undated"]) and s["n"] == len(la["forecasts"]) + len(la["undated"])
        assert sorted(m["id"] for m in s["marks"]) == sorted(m["id"] for m in dated)
        years = sorted(m["mid"] or m["high"] for m in dated)
        assert [m["at"] for m in s["marks"]] == years and (s["first"], s["last"]) == (years[0], years[-1])
        assert all(0 <= m["x"] <= 100 and m["x"] == sg.x(m["at"]) for m in s["marks"])  # the timeline's own scale
        assert abs(s["x"] + s["w"] - sg.x(years[-1])) < 0.011 and s["x"] == sg.x(years[0])


def _fn(name: str) -> str:
    return FIGS.read_text().split(f"export function {name}")[1].split("\nexport function")[0]


def test_no_middle_is_exported_or_drawn_for_any_milestone():
    # the marks on a row are not one statistic (deadlines, most likely years, range ends, years at odds), so a middle
    # would read as a consensus date the records do not hold
    assert set(F["spread"]) == {"lanes"} and not hasattr(sg, "MIDDLE_FLOOR")
    for s in F["spread"]["lanes"]:
        assert not any("middle" in k for k in s) and s["theme"] == (s["id"] not in sg.TABLE_LANES)
    small = {s["id"]: s for s in sg.figures(_small(), GRID, IDEAS)["spread"]["lanes"]}
    assert small["agi"]["n_dated"] == 7 and small["agi"]["n_steps"] == 1 and small["agi"]["n_undated"] == 1
    src = _fn("LaneSpread")
    assert ".middle" not in src and "middle:" not in src and ">Middle<" not in src and "bg-s1" not in src
    assert "No middle or average is drawn" in _prose(src) and "not where opinion settles" in _prose(src)


def test_the_spread_says_placed_where_the_end_of_a_range_is_what_is_drawn():
    src = _prose(_fn("LaneSpread"))
    assert "from the earliest year a forecast is placed at to the latest" in src and "earliest year given" not in src
    assert "Earliest placed" in src and "Latest placed" in src
    assert "a row can begin later than the earliest year a forecast names" in src
    assert "Each forecast is named on the timeline above" in src and "a forecast of an early sign of it" in src  # nothing hover-only


def test_said_against_given_draws_each_dated_forecast_of_the_four_milestones_once():
    said = F["said"]
    want = [m for la in DOC["lanes"] if la["id"] in sg.TABLE_LANES for m in la["forecasts"] if not m["step"]]
    assert sorted(m["id"] for m in said["marks"]) == sorted(m["id"] for m in want) and said["n"] == len(want)
    by = {m["id"]: m for m in want}
    for m in said["marks"]:
        assert m["at"] == (by[m["id"]]["mid"] or by[m["id"]]["high"]) and m["at"] >= int(m["made"][:4])
        assert 0 <= m["x"] <= 100 and 0 <= m["y"] <= 100 and m["href"] == by[m["id"]]["href"]
        if m["y_low"] is not None:  # a stated range is drawn whole, top to bottom
            assert 0 <= m["y_high"] <= m["y"] <= m["y_low"] <= 100 and by[m["id"]]["low"] and by[m["id"]]["high"]
        else:
            assert not (by[m["id"]]["low"] and by[m["id"]]["high"])
    ys = [m["y"] for m in sorted(said["marks"], key=lambda m: m["at"])]
    assert ys == sorted(ys, reverse=True)  # a later year sits higher
    still = sorted((m for m in said["marks"] if not m["moved"]), key=lambda m: m["made"])
    assert [m["x"] for m in still] == sorted(m["x"] for m in still)  # a later forecast sits further right
    year = int(DOC["as_of"][:4])
    assert all((m["y"] > said["this_year"]) == (m["at"] < year) and (m["y"] == said["this_year"]) == (m["at"] == year) for m in said["marks"])
    steps = [tuple(map(float, p.split(","))) for p in said["said_line"].split()]  # the year made, as a year: a step for each
    assert all(a[0] <= b[0] and a[1] >= b[1] for a, b in zip(steps, steps[1:])) and steps[-1][1] == said["this_year"]
    for m in said["marks"]:  # no forecast names a year before the one it was made in
        if not m["moved"] and m["x"] >= steps[0][0]:  # the steps begin where the year-given scale does
            assert m["y"] <= max(y for sx, y in steps if sx <= m["x"] + 0.011), m["id"]
    assert said["left_out"] == {"steps": sum(m["step"] for la in DOC["lanes"] if la["id"] in sg.TABLE_LANES for m in la["forecasts"]),
                                "undated": sum(len(la["undated"]) for la in DOC["lanes"] if la["id"] in sg.TABLE_LANES)}


def test_marks_that_would_cover_each_other_are_set_side_by_side_and_say_so():
    for doc_marks in (F["said"]["marks"], sg.figures(_small(), GRID, IDEAS)["said"]["marks"]):
        for i, a in enumerate(doc_marks):
            assert not any(abs(a["x"] - b["x"]) < sg.BOX[0] - 0.011 and abs(a["y"] - b["y"]) < sg.BOX[1] - 0.011 for b in doc_marks[i + 1:]), a["id"]
    small = {m["id"]: m for m in sg.figures(_small(), GRID, IDEAS)["said"]["marks"]}
    assert not small["c1"]["moved"] and small["c2"]["moved"] and small["c2"]["x"] != small["c1"]["x"]
    assert small["a_range"]["y_low"] > small["a_range"]["y"] > small["a_range"]["y_high"]
    assert "a_step" not in small and "a_odds" not in small and "g_old" not in small  # not one of the four milestones' dated forecasts


def test_a_mark_set_aside_is_tied_back_to_its_date_and_none_sits_right_of_today():
    year = int(DOC["as_of"][:4])
    for said in (F["said"], sg.figures(_small(), GRID, IDEAS)["said"]):
        today = sg._said_x(sg._year(DOC["as_of"]), year)
        for m in said["marks"]:
            assert m["x_made"] == sg._said_x(sg._year(m["made"]), year), m["id"]  # the true place of the date it was made
            assert m["moved"] == (m["x"] != m["x_made"]) and 0 <= m["x"] <= today and m["x_made"] <= today, m["id"]  # never into the future
        assert said["n_moved"] == sum(m["moved"] for m in said["marks"])
    assert F["said"]["y_breaks"] == [round(100 - p, 2) for _, _, p, _ in sg.GIVEN[1:]]  # where the scale up the side changes
    src = _fn("SaidAgainstGiven")
    assert "tie-" in src and "m.x_made" in src and "f.n_moved" in src and "f.y_breaks" in src
    words = _prose(src)
    assert "tied back by a short line to the date it was made" in words and "no mark is set right of today" in words
    assert "a mark set aside, tied back to the date it was made" in words  # the key
    assert "overflow-x-auto" in src and "No mark is named in the drawing" in words  # a phone has no hover and no room


def test_a_mark_made_today_beside_another_is_set_aside_to_the_left():
    late = _doc({"agi": [_m("t1", "2026-10-01", high=2030), _m("t2", "2026-10-05", high=2030)]})
    said = sg.figures(late, GRID, IDEAS)["said"]
    by = {m["id"]: m for m in said["marks"]}
    assert by["t2"]["moved"] and by["t2"]["x"] < by["t1"]["x"] and said["n_moved"] == 1


def test_said_against_given_claims_neither_that_height_is_distance_nor_that_forecasts_converge():
    words = _prose(_fn("SaidAgainstGiven"))
    assert "is how far ahead that forecast looked" not in words  # false on an uneven scale
    assert "equal heights are not equal numbers of years" in words
    assert "is not evidence that forecasts are converging" in words and "not because anyone here changed a date" in words
    assert 'stroke="var(--s2)" strokeWidth="1.5"' in _fn("SaidAgainstGiven")  # a range is not drawn in a milestone's colour


def test_the_worlds_wear_a_single_neutral_border_and_no_colour_that_means_something_elsewhere():
    both = FIGS.read_text() + PARTS.read_text()
    assert "WORLD_FILL" not in both and not re.search(r"var\(--(fast|slow|tight)", both)
    src = _fn("WorldsGrid")
    assert "style=" not in src and "border-l-4 border-s2 bg-surface-2" in src
    words = _prose(src)
    assert "a cell a world is drawn over, named in the cell" in words
    assert "counting one that sits in more than one cell each time" in words  # the count is by cell
    assert "the glyphs are tonight's readings" in FIGS.read_text() and "note={WORLDS_NOTE}" in src  # a model with readings on it


def test_the_page_words_the_review_asked_for():
    page, parts = PAGE.read_text(), (WEB / "components" / "SingularityParts.tsx").read_text()
    labels = re.findall(r'<Folio [^>]*?label="([^"]+)" title="([^"]+)"', page)
    assert labels and not any(NUMBER_WORD.search(w) for pair in labels for w in pair), labels
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert "The ways the next decade could go" in page and "The ways the next decade could go" in contents and "Four ways" not in contents
    assert "one due by the end of this year sits left of today while its window is still open" in parts  # the plate's foot
    assert "may be a different claim, not an older view" in page  # the latest word is not an update
    due = _prose(_fn("DueLines"))
    assert "This site's ledger of forecasts has no word for wrong" in due and "the day this site set for checking it" in due
    lag = _prose(_fn("FictionLag"))
    assert "Nor is it a guide to how long a story written today will wait" in lag and "the middle of the built ideas" in lag
    assert "the middle idea" not in lag


def test_the_due_figure_is_the_pages_own_list_with_no_rate():
    due = F["due"]
    assert [r["id"] for r in due["rows"]] == [m["id"] for m in DOC["due"]]
    for r, m in zip(due["rows"], DOC["due"]):
        assert (r["word"], r["who"], r["settles"], r["step"], r["href"]) == (m["word"], m["who"], m["settles"], m["step"], m["href"])
        assert 0 <= r["x_made"] <= r["x_due"] <= 100 and abs(r["x_made"] + r["w"] - r["x_due"]) < 0.011
        assert (r["x_low"] is None) == (m["low"] is None) and (r["x_low"] is None or abs(r["x_low"] + r["w_low"] - r["x_due"]) < 0.011)
        assert r["settles"] < DOC["as_of"]
    assert due["counts"] == {w: sum(1 for m in DOC["due"] if m["word"] == w) for w in DOC["words"]}
    assert sum(due["counts"].values()) == len(DOC["due"]) == due["n"]
    assert not any(re.search(r"rate|share|pct|percent|score", k) for r in [due, *due["rows"]] for k in r)  # counts only
    assert all(0 <= t["x"] <= 100 for t in due["ticks"])


def test_a_year_that_has_passed_with_no_closing_date_is_not_on_the_calendar_and_is_named():
    year = int(DOC["as_of"][:4])
    want = sorted(m["id"] for la in DOC["lanes"] for m in la["forecasts"] if not m["settles"] and (m["mid"] or m["high"]) < year)
    assert sorted(u["id"] for u in F["due"]["unclosed"]) == want
    assert not {u["id"] for u in F["due"]["unclosed"]} & {r["id"] for r in F["due"]["rows"]}
    small = sg.figures(_small(), GRID, IDEAS)["due"]
    assert [r["id"] for r in small["rows"]] == ["g_old", "g_done"] and [u["id"] for u in small["unclosed"]] == ["g_open"]
    assert small["counts"] == {"happening": 1, "slower": 1, "too_early": 0}


def test_the_worlds_sit_on_the_scenario_grid_where_the_seed_puts_them():
    fig = sg.figures(_small(), GRID, IDEAS)["worlds"]
    cells = {(c["progress"], c["rules"]): c for c in fig["cells"]}
    assert len(cells) == 4 and not cells[("steady", "licensed")]["argued"] and cells[("steady", "licensed")]["worlds"] == []
    assert cells[("fast", "unclear")]["worlds"] == ["quick"] and cells[("fast", "unclear")]["signs"] == GRID["cells"][1]["signposts"]
    by = {w["id"]: w for w in fig["worlds"]}
    assert by["quick"]["n_cells"] == 2 and by["quick"]["open"] == 1 and by["quick"]["bare"] == 1 and not by["quick"]["consistent"]
    assert by["quick"]["states"] == {"holding": 0, "failing": 1, "both": 0, "untestable": 1}
    assert by["slow"]["open"] == 1 and by["slow"]["consistent"]
    assert fig["states"] == {"holding": 0, "failing": 1, "both": 1, "untestable": 1} and fig["bare"] == 1 and fig["unplaced"] == 0
    real = F["worlds"]  # the committed export: every world keeps the page's own word, and every cell it names is on the grid
    assert {w["id"]: w["consistent"] for w in real["worlds"]} == {w["id"]: w["consistent"] for w in DOC["worlds"]}
    grid = {(c["progress"], c["rules"]): c for c in real["cells"]}
    assert len(grid) == len(real["progress"]) * len(real["rules"])
    for w in DOC["worlds"]:
        mine = [grid[(c["progress"], c["rules"])] for c in w["grid"]]
        assert all(w["id"] in c["worlds"] and c["argued"] for c in mine)
        assert w["consistent"] == all(c["consistent"] for c in mine)  # the page's word is the grid's
    assert sum(real["states"].values()) == sum(len(c["signs"]) for c in real["cells"])


def test_the_lag_counts_every_idea_marked_built_with_a_date_and_no_other():
    lag = sg.figures(_small(), GRID, IDEAS)["lag"]
    assert {b["key"]: b["n"] for b in lag["bins"] if b["n"]} == {"0": 1, "2": 2, "10": 1}  # counted in decades; the longest share a bin
    assert (lag["n"], lag["undated"], lag["existed"], lag["not_built"], lag["ideas"]) == (4, 1, 1, 1, 7)
    real, ideas = F["lag"], futures.ideas()
    states = Counter(i["arrival"]["state"] for i in ideas)
    assert sum(b["n"] for b in real["bins"]) == real["n"] == states["marked_built"]
    assert real["n"] + real["undated"] + real["existed"] + real["not_built"] == real["ideas"] == len(ideas)
    top = max(b["n"] for b in real["bins"])
    assert all(b["w"] == round(100 * b["n"] / top, 1) for b in real["bins"]) and max(b["w"] for b in real["bins"]) == 100
    order = [b["key"] for b in real["bins"] for _ in range(b["n"])]
    assert real["middle_key"] == order[(len(order) - 1) // 2]  # the bin the middle built idea falls in


def test_every_figure_states_its_kind_and_has_a_key_and_a_foot():
    src = FIGS.read_text()
    assert 'id = "fig-lag" }' in src and src.count("id={id}") == 1  # /story draws it beside another page's fig-lag, under its own id
    src = src.replace("id={id}", 'id="fig-lag"')
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"\s+title="[^"]+"\s+note=\{?("[^"]+"|KIND_LABEL\.[a-z]+|[A-Z_]+)', src)
    assert [f[0] for f in figures] == ["spread", "said", "due", "worlds", "lag"], figures
    assert len(re.findall(r"<Figure\b", src)) == len(figures)  # none without a stated kind
    blocks = re.split(r"(?=<Figure\b)", src)[1:]
    assert all("keys={" in b and "foot={" in b and "table={" in b for b in blocks)  # nothing is hover-only
    page = PAGE.read_text()
    for name in ("LaneSpread", "SaidAgainstGiven", "DueLines", "WorldsGrid", "FictionLag"):
        assert f"<{name} " in page, name
    assert len(figures) + 1 >= 5  # with the timeline plate


def test_the_page_keeps_the_plate_the_scrubber_and_every_list():
    page = PAGE.read_text()
    for part in ("<TimelinePlate doc={d} />", "<Scrubber ", "<Undated doc={d} />", "<Due doc={d} />", "<Latest doc={d} />",
                 "<Questions doc={d} />", "<Worlds doc={d} />", "<Fiction doc={d} />", "<Sources doc={d} />"):
        assert part in page, part


def _prose(src: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\{[^{}]*\}|<[^<>]*>", " ", src).replace("&apos;", "'").replace("&quot;", '"'))


def test_the_figures_say_what_reviewers_have_required_of_sister_pages():
    src = _prose(FIGS.read_text())
    assert "not on this calendar" in src and not re.search(r"names? no date", src)  # a row with no closing date
    assert "has no word for wrong" in src and not re.search(r"\b(was|were|proved|turned out) wrong\b", src)  # behind is not wrong
    for fig in ("LaneSpread", "SaidAgainstGiven"):  # wherever the heads of Anthropic and its rivals are drawn or counted
        assert "{DISCLOSE}" in FIGS.read_text().split(f"export function {fig}")[1].split("\nexport function")[0], fig
    assert re.search(r'DISCLOSE = "[^"]*a Claude model, made by Anthropic[^"]*rival labs', FIGS.read_text())
    assert "its own record in this site's ledger of forecasts" in src and "its row links to" not in src  # no link that is not there
    lag = _prose(FIGS.read_text().split("export function FictionLag")[1])
    assert "not evidence" in lag and "fiction" in lag.lower()  # the fiction lane is never evidence for a forecast
    assert not re.search(r"\b(accuracy|track record|hit rate|best forecaster|most accurate|ranked by)\b", src, re.I)  # no rate, no ranking
    assert "not a measurement" in (WEB / "components" / "diagrams" / "kit.tsx").read_text() and "KIND_LABEL.model" in FIGS.read_text()
    assert "gild" not in FIGS.read_text() + PARTS.read_text()  # the gilt accent is the page's ornament, never data


def test_figure_words_type_no_digit_but_a_year_and_no_number_word():
    for f in (FIGS, PARTS):
        src = re.sub(r"//[^\n]*", "", f.read_text())
        words = re.findall(r'(?:title|note|label|aria-label|tableLabel)="([^"]+)"', src) + re.findall(r">([^<>{}=;]+)<", src)
        words += [q for q in re.findall(r'"([^"\n]+)"', src) if len(q.split()) >= 3 and (q != q.lower() or "-" not in q)]
        for w in words:
            w = w.replace("&apos;", "'")
            stray = [t for t in w.split() if re.search(r"\d", t)]
            assert all(re.fullmatch(r"\(?(1[6-9]\d\d|2\d\d\d)(s|'s)?[,.;:)]?", t) for t in stray), (f.name, w)
            assert not NUMBER_WORD.search(w), (f.name, w)
