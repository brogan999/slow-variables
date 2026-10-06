"""The figures on /diffusion (Part 45c). Every count, place and age is laid out by the export from the stage's own
indicator cards, so the page only draws; the new block changes nothing the page already read."""

import os
import re
from datetime import date
from pathlib import Path
from statistics import median

import pytest

from ai_tracker import store as st
from ai_tracker.analysis.bands import _band, _on_edge, flow_status
from ai_tracker.analysis.metrics import run_metrics

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web" / "src"
TSX = WEB / "components" / "DiffusionFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "diffusion.tsx"
PAGE = WEB / "app" / "diffusion" / "page.tsx"
STOCKFLOW = WEB / "components" / "StockFlowDiagram.tsx"
CONTENTS = WEB / "lib" / "contents.ts"
HELD = ("edge", "interval", "tier", "single")
TODAY = date(2026, 10, 6)
GROUPS = ("fast", "normal", "slow", "unscored", "other")
ZONES = ("slow", "normal", "between", "fast")
YEAR = re.compile(r"\b(19|20)\d\d\b")


@pytest.fixture(scope="module")
def built():
    cwd = os.getcwd()
    os.chdir(REPO)
    try:
        s = st.Store()
        s.derived = run_metrics(s.con)
        cards = {i.id: s._card(i) for i in s.seed.indicators}
        lens = s._diffusion_lens(cards, [], "2026-10-06", today=TODAY)
    finally:
        os.chdir(cwd)
    return s, cards, lens


def _rows(lens, fig):
    by = {b["id"]: b for b in lens["buckets"]}
    rows = lens["figures"][fig]["rows"]
    assert [r["stage"] for r in rows] == [b["id"] for b in lens["buckets"]]
    return [(r, by[r["stage"]]) for r in rows]


def test_the_figures_block_changes_nothing_the_page_already_read(built):
    s, cards, lens = built
    assert set(lens) - {"figures"} == {"as_of", "verdict", "buckets", "valves", "n_sources", "recent_status_events", "what_would_change"}
    for b in lens["buckets"]:
        assert set(b) == {"id", "name", "order", "stock", "valve", "speed_limit", "indicators", "n_indicators", "status", "tally"}
        flow = [c for c in b["indicators"] if not next(i for i in s.seed.indicators if i.id == c["id"]).direction_rule]
        assert b["status"] == st._summarise(flow) and b["tally"] == st._tally(flow)
        assert b["indicators"] == [cards[c["id"]] for c in b["indicators"]]  # the cards are untouched


def test_every_gauge_is_one_mark_and_the_counts_are_the_stages_own(built):
    s, _, lens = built
    rule = {i.id: bool(i.direction_rule) for i in s.seed.indicators}
    for r, b in _rows(lens, "gauges"):
        assert [d["id"] for d in sorted(r["dots"], key=lambda d: d["id"])] == sorted(c["id"] for c in b["indicators"])
        assert len(r["dots"]) == b["n_indicators"] == sum(r["counts"][g] for g in GROUPS)
        assert [GROUPS.index(d["group"]) for d in r["dots"]] == sorted(GROUPS.index(d["group"]) for d in r["dots"])  # drawn group by group
        for d in r["dots"]:
            c = next(c for c in b["indicators"] if c["id"] == d["id"])
            want = "other" if rule[d["id"]] else {"faster_than_normal": "fast", "consistent_with_normal": "normal", "slower_than_normal": "slow"}.get(c["status"], "unscored")
            assert d["group"] == want and d["status"] == c["status"] and d["href"] == f"/indicators/{d['id']}"
            assert d["id"] in r["ids"][d["group"]]
        assert all(len(r["ids"][g]) == r["counts"][g] for g in GROUPS)
        assert sum(d["votes"] for d in r["dots"]) == r["votes"] == b["tally"]["scored"]  # the card's "N votes cast"
        assert not any(d["votes"] for d in r["dots"] if d["group"] in ("unscored", "other"))


def test_each_banded_reading_is_placed_by_its_own_bands(built):
    s, _, lens = built
    ind = {i.id: i for i in s.seed.indicators}
    fig = lens["figures"]["bands"]
    zones = fig["zones"]
    assert [z["id"] for z in zones] == [z for z in ZONES if z in {x["id"] for x in zones}] and {"normal", "between", "fast"} <= {z["id"] for z in zones} and zones[0]["x"] == 0 and abs(zones[-1]["x"] + zones[-1]["w"] - 100) < 0.02
    assert all(abs(a["x"] + a["w"] - b["x"]) < 0.02 for a, b in zip(zones, zones[1:]))
    edge = {z["id"]: (z["x"], z["x"] + z["w"]) for z in zones}
    drawn = 0
    for r, b in _rows(lens, "bands"):
        assert sorted([d["id"] for d in r["dots"]] + [x["id"] for x in r["left_out"]]) == sorted(c["id"] for c in b["indicators"])
        assert all(x["why"] for x in r["left_out"]) and r["h"] > 0
        for d in r["dots"]:
            i = ind[d["id"]]
            value, _, ids, _ = s.band_input(i)
            assert d["value"] == value and d["obs_ids"] == ids and ids
            lo, hi = edge[d["zone"]]
            assert lo <= d["x"] <= hi and 0 <= d["y"] <= 100, d
            reads = {"consistent_with_normal": "normal", "faster_than_normal": "fast", "emerging": "between", "slower_than_normal": "slow"}[_band(value, i.normal_band, i.fast_band, i.falsifying_band).value]
            assert d["zone"] == reads, d["id"]  # the rule's own reading of tonight's number
            assert d["status"] == next(c["status"] for c in b["indicators"] if c["id"] == d["id"])
            drawn += 1
    assert drawn >= 40
    by = {d["id"]: d for r in fig["rows"] for d in r["dots"]}
    assert by["bls_labor_productivity_yoy"]["zone"] == "normal" and by["metr_horizon_50"]["zone"] == "fast"


def _evaluator_reads(s, i):
    """Tonight's status as `evaluate` proposes it: the band rule with its edge, interval and tier checks, then the
    two-source rule."""
    from ai_tracker.cli import _single_non_primary
    from ai_tracker.schema import UNSCORED

    value, _, _, tier = s.band_input(i)
    lo, hi = s.band_interval(i)
    new = flow_status(value, i.normal_band, i.fast_band, i.falsifying_band, tier, lo, hi).value
    return "emerging" if new not in UNSCORED and _single_non_primary(s, i) else new


def test_a_gauge_on_the_line_between_ranges_is_drawn_on_the_line_not_inside_a_range(built):
    s, _, lens = built
    ind = {i.id: i for i in s.seed.indicators}
    fig = lens["figures"]["bands"]
    span = {z["id"]: (z["x"], z["x"] + z["w"]) for z in fig["zones"]}
    on = 0
    for r in fig["rows"]:
        for d in r["dots"]:
            i = ind[d["id"]]
            assert d["on_edge"] in (None, "normal", "fast"), d
            if d["on_edge"]:
                assert _on_edge(d["value"], i.normal_band, i.fast_band, i.falsifying_band), d["id"]
                assert abs(d["x"] - (span["normal"][1] if d["on_edge"] == "normal" else span["fast"][0])) < 0.02, d
                on += 1
            elif d["zone"] in ("normal", "fast") and _on_edge(d["value"], i.normal_band, i.fast_band, i.falsifying_band):
                # on some other line (a falsifying one): never left looking as if it were well inside a range
                assert "edge" in d["held"] or d["status"] != "emerging", d
    assert on  # tonight some gauges sit on a line
    by = {d["id"]: d for r in fig["rows"] for d in r["dots"]}
    assert by["rsi_agent_workdays_per_human"]["on_edge"] == "fast" and by["expert_data_market_run_rate"]["on_edge"] == "fast"


def test_every_gauge_held_at_emerging_says_why_and_the_reason_is_the_evaluators_own(built):
    s, cards, lens = built
    ind = {i.id: i for i in s.seed.indicators}
    seen = set()
    for r in lens["figures"]["bands"]["rows"]:
        for d in r["dots"]:
            i = ind[d["id"]]
            assert set(d["held"]) <= set(HELD) and len(set(d["held"])) == len(d["held"]), d
            raw = _band(d["value"], i.normal_band, i.fast_band, i.falsifying_band).value
            tonight = _evaluator_reads(s, i)
            if d["status"] != "emerging":
                assert d["held"] == [], d  # a scored gauge is not held
                continue
            # a reason is exported exactly when the range would score the number and the evaluator's rule does not
            assert bool(d["held"]) == (raw != "emerging" and tonight == "emerging"), (d["id"], raw, tonight, d["held"])
            if d["zone"] != "between" and not cards[d["id"]]["pending"]:
                assert d["held"], d["id"]  # drawn in a range, published emerging: never without its reason
            seen |= set(d["held"])
    assert seen == set(HELD)  # each of the rule's reasons is in play tonight
    by = {d["id"]: d for r in lens["figures"]["bands"]["rows"] for d in r["dots"]}
    assert by["aei_augmentation_share"]["held"] == ["edge"] and by["expert_data_market_run_rate"]["held"] == ["edge"]


def test_a_gauge_inside_its_refresh_window_is_not_framed_as_excused(built):
    s, _, lens = built
    ind = {i.id: i for i in s.seed.indicators}
    excused = [d for r in lens["figures"]["fresh"]["rows"] for d in r["dots"] if d["excused"]]
    assert excused
    for d in excused:
        assert st.is_stale(d["as_of"], ind[d["id"]].cadence_expected, TODAY) and d["why"] and not d["stale"], d["id"]
    by = {d["id"]: d for r in lens["figures"]["fresh"]["rows"] for d in r["dots"]}
    assert not by["cl_refresh_cadence_hours"]["excused"]  # quarterly, inside its limit on the test's date


def test_the_age_axis_keeps_its_end_label_on_a_phone_and_framed_marks_do_not_touch(built):
    _, _, lens = built
    fig = lens["figures"]["fresh"]
    ticks = fig["ticks"]
    assert not ticks[0]["minor"] and not ticks[-1]["minor"]  # both ends of the scale are always labelled
    shown = [t["x"] for t in ticks if not t["minor"]]
    assert all(b - a >= 20 for a, b in zip(shown, shown[1:])), shown  # the labels a phone keeps have room
    for r in fig["rows"]:
        lanes = {}
        for d in r["dots"]:
            lanes.setdefault(d["y"], []).append(d["x"])
        for xs in lanes.values():
            xs.sort()
            assert all(b - a >= 7.5 for a, b in zip(xs, xs[1:])), (r["stage"], xs)  # a framed mark is wider than a bare one


def test_axis_labels_typed_in_python_are_a_count_and_a_unit_and_nothing_else(built):
    """The no-digit test reads only the page's components. Tick labels are axis values, where digits are allowed; this
    says so, and keeps them to a bare value."""
    _, _, lens = built
    assert all(re.fullmatch(r"today|\d+ (week|month|year)s?", t["label"]) for t in lens["figures"]["fresh"]["ticks"])
    assert all(z["tick"] == str(z["lo"]) for z in lens["figures"]["sure"]["zones"])


def test_freshness_is_each_cards_own_newest_date(built):
    _, _, lens = built
    fig = lens["figures"]["fresh"]
    assert fig["today"] == TODAY.isoformat()
    xs = [t["x"] for t in fig["ticks"]]
    assert xs == sorted(xs) and xs[0] == 0 and xs[-1] == 100
    seen = []
    for r, b in _rows(lens, "fresh"):
        dated = [c for c in b["indicators"] if c["latest"]]
        assert sorted(d["id"] for d in r["dots"]) == sorted(c["id"] for c in dated)
        for d in r["dots"]:
            c = next(c for c in dated if c["id"] == d["id"])
            assert d["as_of"] == c["latest"]["as_of"] and d["age_days"] == max(0, (TODAY - date.fromisoformat(d["as_of"][:10])).days)
            assert d["stale"] == bool(c["stale_as_of"]) and not (d["stale"] and d["excused"])
            assert 0 <= d["x"] <= 100 and 0 <= d["y"] <= 100
            seen.append((d["age_days"], d["x"]))
        ages = [d["age_days"] for d in r["dots"]]
        assert r["median_days"] == median(ages) and r["oldest_days"] == max(ages) and r["newest_days"] == min(ages)
        assert r["n_stale"] == sum(d["stale"] for d in r["dots"]) and 0 <= r["median_x"] <= 100
        assert r["n_excused"] == sum(d["excused"] for d in r["dots"])
    seen.sort()
    assert all(a[1] <= b[1] for a, b in zip(seen, seen[1:]))  # older is never drawn to the left of newer


def test_confidence_is_each_cards_own_and_the_rubric_fills_the_scale(built):
    s, _, lens = built
    fig = lens["figures"]["sure"]
    zones = fig["zones"]
    assert zones[0]["x"] == 0 and abs(zones[-1]["x"] + zones[-1]["w"] - 100) < 0.02
    assert all(abs(a["x"] + a["w"] - b["x"]) < 0.02 for a, b in zip(zones, zones[1:]))
    assert [z["label"] for z in zones] == [z["label"] for z in st.confidence_rubric()]
    for r, b in _rows(lens, "sure"):
        scored = [c for c in b["indicators"] if c["confidence"] is not None]
        assert sorted(d["id"] for d in r["dots"]) == sorted(c["id"] for c in scored)
        for d in r["dots"]:
            c = next(c for c in scored if c["id"] == d["id"])
            assert d["confidence"] == c["confidence"] and 0 <= d["x"] <= 100 and 0 <= d["y"] <= 100
            z = next(z for z in zones if z["lo"] <= d["confidence"] <= z["hi"])
            assert z["x"] <= d["x"] <= z["x"] + z["w"]


def test_each_stage_has_a_headline_reading_with_a_series_to_draw(built):
    _, _, lens = built
    gauges = {d["id"]: d for r in lens["figures"]["gauges"]["rows"] for d in r["dots"]}
    heads = lens["figures"]["headline"]
    assert [h["stage"] for h in heads] == [b["id"] for b in lens["buckets"]]
    for h, b in zip(heads, lens["buckets"]):
        cards = {c["id"]: c for c in b["indicators"]}
        c = cards[h["id"]]
        assert c["spark"], h  # more than one reading, so there is a line to draw
        assert gauges[h["id"]]["group"] != "other"  # a reading of speed, not of who keeps the money
        if any(gauges[i]["votes"] and cards[i]["spark"] for i in cards):
            assert gauges[h["id"]]["votes"], h  # where a drawable reading counts toward the status, the headline is one


def test_the_lag_model_is_a_drawing_with_no_number_of_its_own(built):
    _, _, lens = built
    m = lens["figures"]["model"]
    main = [b for b in lens["buckets"] if b["id"] != "return_arrow"]
    assert [c["stage"] for c in m["curves"]] == [b["id"] for b in main]
    for c, b in zip(m["curves"], main):
        assert c["name"] == b["name"] and c["limit"] == b["speed_limit"] and c["order"] == b["order"]  # labels are the seed's
        pts = [tuple(map(float, p.split(","))) for p in re.findall(r"[-\d.]+,[-\d.]+", c["d"])]
        assert len(pts) > 10 and all(0 <= x <= 100 and 0 <= y <= 100 for x, y in pts)
        assert all(a[0] < b_[0] and a[1] >= b_[1] for a, b_ in zip(pts, pts[1:]))  # rises left to right
        assert "value" not in c
    mids = [c["mid"]["x"] for c in m["curves"]]
    assert mids == sorted(mids) and len(set(mids)) == len(mids)  # each stage starts after the one before
    assert m["loop"]["name"] == next(b["name"] for b in lens["buckets"] if b["id"] == "return_arrow")


def _words(src: str) -> list[str]:
    """What a reader sees: JSX text and the strings handed to title, aria-label and label props."""
    return re.findall(r"(?<!=)>([^<>{}]+)<", src) + re.findall(r'(?:title|aria-label|label|note)="([^"]+)"', src)


def test_at_least_five_figures_each_with_a_kind_a_key_and_a_foot():
    src = TSX.read_text()
    figs = src.split("<Figure")[1:]
    assert len(figs) >= 5
    for f in figs:
        head = f[: f.index(">\n")] if ">\n" in f else f
        assert "note={KIND_LABEL." in f.split("foot=")[0] or "note={`${KIND_LABEL." in f.split("foot=")[0], head[:80]
        assert "keys={" in f and "foot={" in f and "title=" in f, head[:80]
    charts = [f for f in figs if "KIND_LABEL.chart" in f.split("foot=")[0]]
    assert charts and all("table={" in f for f in charts)  # a chart's numbers are folded beneath it
    page = PAGE.read_text()
    assert "StockFlowDiagram" in page and "What limits its speed" in page  # the page keeps what it had
    names = re.findall(r"export function (\w+)", src)
    assert len([n for n in names if f"<{n}" in page]) >= 5


def test_the_figures_words_type_no_digit_but_years_and_no_number_word():
    from .test_outlook import NUMBER_WORD

    for path in (TSX, PARTS):
        src = path.read_text()
        for w in _words(src):
            assert not re.search(r"\d", YEAR.sub("", w)), w
        for line in src.splitlines():
            assert not NUMBER_WORD.search(line), line.strip()[:120]
    assert "hatch" not in TSX.read_text()  # hatching is kept for judgement; these charts draw records


def test_the_status_has_one_name_and_the_words_say_what_is_counted():
    tsx, parts, page = TSX.read_text(), PARTS.read_text(), PAGE.read_text()
    assert "too early to score" not in (tsx + parts).lower()  # the site's word is emerging
    assert "emerging (not yet scored)" in parts and "the next figure" not in tsx
    assert "published readings count" not in page and "cast, from {b.tally.published} gauges read for speed" in page
    assert "One gauge from each stage, over time" in tsx and "One reading from each stage" not in tsx
    assert "h.counts" in tsx and "does not count toward the stage" in tsx  # a panel whose gauge casts no vote says so
    assert "A tie goes to the gauge with more records behind it" in tsx
    assert "Why it is not scored" in tsx and "Height within a strip means nothing" in tsx
    assert "old by design" not in tsx.lower() and "outline-dashed" in parts
    assert "which this site calls a gauge" in page and "or is held at" in page


def test_the_fifth_stage_has_one_name_and_the_contents_line_ends_where_the_page_does():
    name = "(feedback into methods)"
    assert name in TSX.read_text() and "Return arrow " + name in STOCKFLOW.read_text()
    assert "Feedback into methods" not in STOCKFLOW.read_text()
    c = CONTENTS.read_text()
    assert "to how work is reorganised?" in c and "what workers are paid" not in c
