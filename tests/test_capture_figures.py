"""The figures on /capture (Part 45f). Every number they draw is a record's, summed and laid out by the export; the
model of the page's rule is seed text with no number; the page only places what the export wrote."""

import json
import os
import re
from pathlib import Path

import pytest

from ai_tracker import capture_figures as cf
from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics

REPO = Path(__file__).resolve().parents[1]
TSX = [REPO / "web/src/components/CaptureFigures.tsx", REPO / "web/src/components/diagrams/capture.tsx"]
PAGE = REPO / "web/src/app/capture/page.tsx"
YEAR = re.compile(r"\b(19|20)\d\d\b")
OLD_KEYS = {"as_of", "verdict", "what_would_change", "recent_status_events", "gross_profit_stack", "margin_stack", "layers"}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    cwd = os.getcwd()
    os.chdir(REPO)
    s = st.Store()
    s.derived = run_metrics(s.con)
    out = tmp_path_factory.mktemp("web")
    s.export(out)
    os.chdir(cwd)
    return s, json.loads((out / "lens" / "capture.json").read_text())


def test_the_export_adds_one_block_and_changes_nothing_else(world):
    s, cap = world
    assert set(cap) == OLD_KEYS | {"figures"}
    assert set(cap["figures"]) == {"gauges", "year", "labs", "ties", "concentration", "rule"}
    cards = {i.id: s._card(i) for i in s.seed.indicators}
    assert cap["layers"] == json.loads(json.dumps([s._capture_layer(layer, cards) for layer in s.seed.layers], default=str))


def test_every_capture_gauge_is_one_mark_under_the_word_it_reads_tonight(world):
    s, cap = world
    g = cap["figures"]["gauges"]
    layers = {layer["id"]: layer for layer in cap["layers"]}
    assert [row["id"] for row in g["layers"]] == [layer.id for layer in s.seed.layers]
    for row in g["layers"]:
        want = {i.id for i in s.seed.indicators if i.layer_id == row["id"] and i.published and i.direction_rule}
        marks = [m for grp in row["groups"] for m in grp["marks"]]
        assert {m["id"] for m in marks} == want and len(marks) == len(want) == row["n"]
        assert row["status"] == layers[row["id"]]["status"] and row["href"] == f"/layers/{row['id']}"
        assert [grp["word"] for grp in row["groups"]] == [w["id"] for w in g["words"]]
        cards = {c["id"]: c for c in layers[row["id"]]["indicators"]}
        for grp in row["groups"]:
            assert grp["n"] == len(grp["marks"])
            for m in grp["marks"]:
                assert m["status"] == cards[m["id"]]["status"] and m["href"] == f"/indicators/{m['id']}"
                assert cf.word(m["status"]) == grp["word"]
    assert g["n"] == sum(row["n"] for row in g["layers"]) > 20


def test_the_year_figure_reads_the_stacks_newest_quarter_and_the_one_a_year_before(world):
    _, cap = world
    rows = cap["figures"]["year"]["rows"]
    assert {r["stack"] for r in rows} == {"gross_profit", "operating_income"}
    for key, name in (("gross_profit_stack", "gross_profit"), ("margin_stack", "operating_income")):
        quarters = {q["as_of"]: q for q in cap[key]["quarters"] if q["parts"]}
        newest = quarters[max(quarters)]
        mine = [r for r in rows if r["stack"] == name]
        assert [r["id"] for r in mine] == [p["id"] for p in newest["parts"]]
        for r, p in zip(mine, newest["parts"]):
            assert r["now"]["value"] == p["value"] and r["now"]["obs_ids"] == p["obs_ids"] and r["now"]["href"] == p["href"]
            assert r["estimated"] == p["estimated"] and abs(r["now"]["x"] - 100 * p["value"]) < 0.01
            if r["then"]:
                assert r["then"]["as_of"] == f"{int(r['now']['as_of'][:4]) - 1}{r['now']['as_of'][4:]}"
                old = next(o for o in quarters[r["then"]["as_of"]]["parts"] if o["id"] == r["id"])
                assert r["then"]["value"] == old["value"] and 0 <= r["then"]["x"] <= 100 and r["change"]
        assert abs(sum(r["now"]["value"] for r in mine) - 1) < 1e-6  # the parts of one quarter are the whole of it
    assert any(r["then"] for r in rows)


def test_each_labs_bars_are_its_own_records_and_the_ratio_is_the_sites_metric(world):
    s, cap = world
    labs = cap["figures"]["labs"]
    ratio = {}
    for d in s.derived_for("lab_recoupment_ratio"):
        ratio[d.dims["entity"]] = d  # sorted by date, so the last one stands
    assert {r["subject"] for r in labs["rows"]} == set(ratio) and len(labs["rows"]) >= 4
    obs = {o["id"]: o for o in s.observations("epoch.*.revenue_run_rate_usd.pt", "epoch.*.round_equity_usd.pt", "circular.*")}
    top = max(b["value"] for r in labs["rows"] for b in (r["run_rate"], r["equity"], r["promised"]) if b)
    for r in labs["rows"]:
        d = ratio[r["subject"]]
        assert r["run_rate"]["obs_ids"] == d.input_observation_ids[:1] and r["run_rate"]["value"] == obs[d.input_observation_ids[0]]["value_numeric"]
        assert abs(r["equity"]["value"] - sum(obs[i]["value_numeric"] for i in r["equity"]["obs_ids"])) < 1
        assert sorted(r["run_rate"]["obs_ids"] + r["equity"]["obs_ids"]) == sorted(d.input_observation_ids)
        assert abs(r["ratio"]["value"] - d.value) < 1e-9 and abs(r["run_rate"]["value"] / r["equity"]["value"] - d.value) < 1e-9
        assert r["equity"]["n"] == len(r["equity"]["obs_ids"]) and r["run_rate"]["stamp"] == s.stamp_of(r["run_rate"]["obs_ids"])
        if r["promised"]:
            rows = [obs[i] for i in r["promised"]["obs_ids"]]
            assert abs(r["promised"]["value"] - sum(o["value_numeric"] for o in rows)) < 1 and r["promised"]["n"] == len(rows)
            assert all(cf.KIND[o["series_key"].split(".")[2].removesuffix("_usd")] == "buy" for o in rows)
        for b in (r["run_rate"], r["equity"], r["promised"]):
            assert b is None or (abs(b["w"] - 100 * b["value"] / top) < 0.01 and 0 <= b["w"] <= 100)
    # even-handed: the labs are in one order by one rule, and a frontier lab with no run-rate on record is named
    assert [r["equity"]["value"] for r in labs["rows"]] == sorted((r["equity"]["value"] for r in labs["rows"]), reverse=True)
    frontier = {e.id: e for e in s.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)}
    drawn = {r["id"] for r in labs["rows"]}
    assert {"openai", "anthropic"} <= drawn and len(labs["absent"]) == len(set(frontier) - drawn) > 0


def test_the_ties_add_up_to_the_ledgers_counted_total_and_every_band_sits_inside_its_ends(world):
    s, cap = world
    t = cap["figures"]["ties"]
    total = s.derived_for("circular_commitments_total")[-1]
    assert t["total"]["value"] == total.value and sorted(t["total"]["obs_ids"]) == sorted(total.input_observation_ids)
    assert abs(sum(p["value"] for p in t["pairs"]) - total.value) < 1
    assert sorted(i for p in t["pairs"] for i in p["obs_ids"]) == sorted(total.input_observation_ids)
    assert all(p["kind"] in ("buy", "stake") and p["n"] == len(p["obs_ids"]) for p in t["pairs"])
    for side in ("left", "right"):
        nodes = t[side]
        assert abs(sum(n["value"] for n in nodes) - total.value) < 1
        for a, b in zip(nodes, nodes[1:]):
            assert a["y"] + a["h"] <= b["y"] + 1e-6  # nodes never overlap
        assert nodes[0]["y"] >= 0 and nodes[-1]["y"] + nodes[-1]["h"] <= 100.001
        for n in nodes:
            mine = [b for b in t["bands"] if b[side] == n["id"]]
            assert abs(sum(b["value"] for b in mine) - n["value"]) < 1 and abs(sum(b[f"{side}_h"] for b in mine) - n["h"]) < 0.05
            assert all(n["y"] - 0.01 <= b[f"{side}_y"] and b[f"{side}_y"] + b[f"{side}_h"] <= n["y"] + n["h"] + 0.05 for b in mine)
    assert abs(sum(b["value"] for b in t["bands"]) - total.value) < 1 and all(b["d"].startswith("M") for b in t["bands"])
    labs = {e.id for e in s.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)}
    assert {n["id"] for n in t["right"]} - {"none"} <= labs
    # the foot says a few very large deals make up most of it: the three largest pairings are more than half
    by_pair: dict[tuple[str, str], float] = {}
    for p in t["pairs"]:
        by_pair[(p["a"], p["b"])] = by_pair.get((p["a"], p["b"]), 0) + p["value"]
    assert sum(sorted(by_pair.values(), reverse=True)[:3]) > total.value / 2


def test_the_concentration_strip_places_each_index_at_its_latest_reading(world):
    _, cap = world
    cards = {c["id"]: c for layer in cap["layers"] for c in layer["indicators"]}
    rows = cap["figures"]["concentration"]["rows"]
    assert len(rows) >= 3 and [r["id"] for r in rows] == [i for i in cf.CONCENTRATION if i in cards]
    for r in rows:
        latest = cards[r["id"]]["latest"]
        assert cards[r["id"]]["unit"] == "index" and r["value"] == latest["value"] and r["obs_ids"] == latest["obs_ids"]
        assert abs(r["x"] - 100 * r["value"]) < 0.01 and 0 <= r["x"] <= 100 and r["as_of"] == latest["as_of"]


def test_the_rule_is_seed_text_and_no_word_on_the_page_types_a_number(world):
    from .test_outlook import NUMBER_WORD

    _, cap = world
    spec = cf.load()
    assert cap["figures"]["rule"] == spec["rule"] and len(spec["rule"]["steps"]) >= 3
    for t in cf.strings(spec):
        assert not re.search(r"\d", t) and not NUMBER_WORD.search(t), t
    for f in TSX:
        src = f.read_text()
        for text in re.findall(r">([^<>{}=;]+)<", src):  # the words between tags: what a reader sees
            assert not re.search(r"\d", YEAR.sub("", text)), text.strip()[:140]
        for line in src.splitlines():
            assert not NUMBER_WORD.search(line), line.strip()[:140]


def test_every_figure_says_what_kind_it_is_and_carries_a_key_a_foot_and_its_numbers():
    src = TSX[0].read_text()
    figures = re.findall(r"<Figure\b(.*?)\n    >", src, re.S)
    assert 4 <= len(figures) <= 7
    for f in figures:
        assert "note={KIND_LABEL." in f or "note={`${KIND_LABEL." in f, f[:80]
        assert "keys={" in f and "foot={" in f, f[:80]
        assert "KIND_LABEL.model" in f or "table={" in f, f[:80]  # a chart folds its numbers beneath
    page = PAGE.read_text()
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name
    for kept in ("<FourPlaces ", "<StackPlate ", "<StackChart ", "c.what_would_change", "ChangelogList"):
        assert kept in page, kept
    assert len(re.findall(r"<(FourPlaces|StackPlate|StackChart|\w+Plate|Capture\w+) ", page)) >= 7
    parts = TSX[1].read_text()
    assert "Math." not in src + parts and "hatch" in src  # hatching is kept for an estimate, and says so in the key
    assert "estimate" in src


def test_the_labs_figure_says_what_each_number_rests_on_and_who_drafted_it():
    src = TSX[0].read_text()
    for said in ("not booked revenue", "at face", "Anthropic", "floor"):
        assert said in src, said
