"""The figures on /diffusion (Part 45c). Every count, place and age is laid out by the export from the stage's own
indicator cards, so the page only draws; the new block changes nothing the page already read."""

import os
import re
from datetime import date
from pathlib import Path
from statistics import median

import pytest

from ai_tracker import store as st
from ai_tracker.analysis.bands import _band
from ai_tracker.analysis.metrics import run_metrics

REPO = Path(__file__).resolve().parents[1]
WEB = REPO / "web" / "src"
TSX = WEB / "components" / "DiffusionFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "diffusion.tsx"
PAGE = WEB / "app" / "diffusion" / "page.tsx"
TODAY = date(2026, 10, 6)
GROUPS = ("fast", "normal", "slow", "unscored", "other")
ZONES = ("normal", "between", "fast")
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
        assert sum(d["votes"] for d in r["dots"]) == r["votes"] == b["tally"]["scored"]  # the card's "N readings count"
        assert not any(d["votes"] for d in r["dots"] if d["group"] in ("unscored", "other"))


def test_each_banded_reading_is_placed_by_its_own_bands(built):
    s, _, lens = built
    ind = {i.id: i for i in s.seed.indicators}
    fig = lens["figures"]["bands"]
    zones = fig["zones"]
    assert [z["id"] for z in zones] == list(ZONES) and zones[0]["x"] == 0 and abs(zones[-1]["x"] + zones[-1]["w"] - 100) < 1e-6
    assert all(abs(a["x"] + a["w"] - b["x"]) < 1e-6 for a, b in zip(zones, zones[1:]))
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
            reads = {"consistent_with_normal": "normal", "faster_than_normal": "fast", "emerging": "between", "slower_than_normal": "normal"}[_band(value, i.normal_band, i.fast_band, i.falsifying_band).value]
            assert d["zone"] == reads, d["id"]  # the rule's own reading of tonight's number
            assert d["status"] == next(c["status"] for c in b["indicators"] if c["id"] == d["id"])
            drawn += 1
    assert drawn >= 40
    by = {d["id"]: d for r in fig["rows"] for d in r["dots"]}
    assert by["bls_labor_productivity_yoy"]["zone"] == "normal" and by["metr_horizon_50"]["zone"] == "fast"


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
            assert d["stale"] == bool(c["stale_as_of"]) and d["excused"] == bool(c["stale_reason"] and not c["stale_as_of"])
            assert 0 <= d["x"] <= 100 and 0 <= d["y"] <= 100
            seen.append((d["age_days"], d["x"]))
        ages = [d["age_days"] for d in r["dots"]]
        assert r["median_days"] == median(ages) and r["oldest_days"] == max(ages) and r["newest_days"] == min(ages)
        assert r["n_stale"] == sum(d["stale"] for d in r["dots"]) and 0 <= r["median_x"] <= 100
    seen.sort()
    assert all(a[1] <= b[1] for a, b in zip(seen, seen[1:]))  # older is never drawn to the left of newer


def test_confidence_is_each_cards_own_and_the_rubric_fills_the_scale(built):
    s, _, lens = built
    fig = lens["figures"]["sure"]
    zones = fig["zones"]
    assert zones[0]["x"] == 0 and abs(zones[-1]["x"] + zones[-1]["w"] - 100) < 1e-6
    assert all(abs(a["x"] + a["w"] - b["x"]) < 1e-6 for a, b in zip(zones, zones[1:]))
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
    return re.findall(r">([^<>{}]+)<", src) + re.findall(r'(?:title|aria-label|label|note)="([^"]+)"', src)


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
