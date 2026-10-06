"""The drawn figures on /argument/migration (Part 45d). Every block is laid out by the export from records the page
already holds: the scorecard, the acquisitions tally's own derived row, the gauges' ages and the seed's chain model.
The web only places what arrives."""

import json
import re
from datetime import date
from pathlib import Path

import pytest
import yaml

from ai_tracker import argument as ar
from ai_tracker import migration_figures as mf
from ai_tracker import store as st
from ai_tracker.analysis.tightness import score_input

from .test_outlook import NUMBER_WORD

WEB = Path("web/src")
TSX = WEB / "components" / "MigrationFigures.tsx"
KIT = WEB / "components" / "diagrams" / "migration.tsx"
PAGE = WEB / "app" / "argument" / "migration" / "page.tsx"
NEW = ("chain", "scale", "deals", "ages", "blind", "calls")
YEAR = re.compile(r"\b(19|20)\d\d\b")
TODAY = date(2026, 10, 6)


@pytest.fixture(scope="module")
def built():
    s = st.Store()
    spec = ar.load()
    return s, spec, ar.migration(s, spec, TODAY)


def test_the_export_adds_one_block_and_changes_no_existing_field(built):
    s, spec, m = built
    assert set(m) == {"as_of", "facts", "scorecard", "strip", "predictions", "tally", "sources", "figures"}
    assert set(m["figures"]) == {"chain", "scale", "deals", "ages", "blind"}
    card = ar.scorecard(s, TODAY)
    assert json.dumps(m["scorecard"], sort_keys=True, default=str) == json.dumps(card, sort_keys=True, default=str)
    assert m["strip"] == ar.strip(spec["migration"], TODAY)
    assert m["tally"] == {k: sum(1 for p in m["predictions"] if p["state"] == k) for k in ar.STATES}


def test_the_chain_is_a_model_drawn_from_seed_words_with_one_shortest_link_that_moves(built):
    _, spec, m = built
    seed, chain = spec["migration"]["chain"], m["figures"]["chain"]
    assert [x["label"] for x in chain["states"][0]["links"]] == [x["label"] for x in seed["links"]]
    assert len(chain["states"]) == 2
    shortest = []
    for state in chain["states"]:
        hs = [x["h"] for x in state["links"]]
        assert all(0 < h <= 100 for h in hs) and state["level"] == min(hs)  # the pace line sits on the shortest link
        tight = [x for x in state["links"] if x["shortest"]]
        assert len(tight) == 1 and tight[0]["h"] == min(hs) and hs.count(min(hs)) == 1
        assert all(x["h"] == chain["drawn"][x["word"]] for x in state["links"])  # a word on a fixed scale, never a figure
        shortest.append(tight[0]["id"])
    assert shortest[0] != shortest[1]  # relieve one and another limits the system
    before = {x["id"]: x["h"] for x in chain["states"][0]["links"]}
    grew = [x for x in chain["states"][1]["links"] if x["h"] != before[x["id"]]]
    assert [x["id"] for x in grew] == [shortest[0]] and grew[0]["was"] == before[shortest[0]] < grew[0]["h"]
    assert chain["states"][1]["level"] > chain["states"][0]["level"]


def test_the_scale_ranks_every_scored_input_and_keeps_the_unscored_off_it(built):
    _, _, m = built
    card, scale = m["scorecard"], m["figures"]["scale"]
    by = {i["id"]: i for i in card["inputs"]}
    rows = scale["rows"]
    assert {r["id"] for r in rows} == {i["id"] for i in card["inputs"] if i["score"] is not None}
    assert [r["score"] for r in rows] == sorted((r["score"] for r in rows), reverse=True)
    for r in rows:
        i = by[r["id"]]
        assert (r["score"], r["word"], r["hatched"], r["name"], r["obs_ids"]) == (i["score"], i["word"], i["hatched"], i["name"], i["obs_ids"])
        assert r["obs_ids"] and 0 <= r["x"] <= 100 and r["x"] == r["score"]
    assert {u["id"] for u in scale["unscored"]} == {i["id"] for i in card["inputs"] if i["score"] is None}
    assert len(rows) == card["scored"]["value"] and len(rows) + len(scale["unscored"]) == card["total"] == scale["total"]
    bands = scale["bands"]
    assert [b["word"] for b in bands] == [w for _, w in sorted(card["method"]["words"])]
    assert bands[0]["x"] == 0 and bands[-1]["x"] + bands[-1]["w"] == 100
    assert all(a["x"] + a["w"] == b["x"] for a, b in zip(bands, bands[1:]))


def test_the_blind_spots_group_every_unscored_input_by_its_reason(built):
    _, _, m = built
    card, blind = m["scorecard"], m["figures"]["blind"]
    unscored = {i["id"]: i for i in card["inputs"] if i["score"] is None}
    seen = [i["id"] for g in blind["groups"] for i in g["inputs"]]
    assert sorted(seen) == sorted(unscored) and blind["total"] == len(unscored)
    for g in blind["groups"]:
        assert g["n"] == len(g["inputs"]) > 0
        assert all(unscored[i["id"]]["withheld"]["kind"] == g["kind"] for i in g["inputs"])
        assert g["conjecture"] == (g["kind"] == "no_public_series")  # the essay's conjecture is about this group only


def test_the_deals_are_the_tallys_own_records_one_mark_each(built):
    s, _, m = built
    deals, fact = m["figures"]["deals"], m["facts"]["lab_deals_4q"]
    d = s.derived_for("lab_vertical_integration_events_4q")[-1]
    assert deals["total"]["value"] == fact["value"] == d.value and deals["total"]["derived_id"] == d.id
    marks = [x for b in deals["buyers"] for c in b["cells"] for x in c["deals"]]
    assert len(marks) == d.value  # one mark for each deal the metric counted, never a recount by hand
    assert sorted(i for x in marks for i in x["obs_ids"]) == sorted(d.input_observation_ids)
    assert all(x["href"].startswith("/series/acq.") for x in marks)
    assert sum(q["n"] for q in deals["quarters"]) == d.value == sum(k["n"] for k in deals["kinds"])
    assert len(deals["quarters"]) == 4 and [q["id"] for q in deals["quarters"]] == sorted(q["id"] for q in deals["quarters"])
    buyers = {e.id for e in s.seed.entities}
    for b in deals["buyers"]:
        assert b["id"] in buyers and b["kind"] in {k["id"] for k in deals["kinds"]}
        assert [c["quarter"] for c in b["cells"]] == [q["id"] for q in deals["quarters"]]
        assert b["n"] == sum(len(c["deals"]) for c in b["cells"]) > 0
    assert [b["n"] for b in deals["buyers"]] == sorted((b["n"] for b in deals["buyers"]), reverse=True)


def test_each_reading_is_placed_by_its_age_against_its_own_limit(built):
    _, _, m = built
    card, ages = m["scorecard"], m["figures"]["ages"]
    by = {i["id"]: i for i in card["inputs"]}
    assert [r["id"] for r in ages["rows"]] == [i["id"] for i in card["inputs"] if i["score"] is not None]
    for r in ages["rows"]:
        used = [g for g in by[r["id"]]["gauges"] if g["points"] is not None]
        assert [g["id"] for g in r["gauges"]] == [g["id"] for g in used]
        for g, src in zip(r["gauges"], used):
            assert (g["age_days"], g["max_age_days"]) == (src["age_days"], src["max_age_days"])
            assert 0 <= g["x"] <= 100 and abs(g["x"] - 100 * g["age_days"] / g["max_age_days"]) < 0.01
            assert g["near"] == (g["age_days"] > ages["near_share"] * g["max_age_days"])
            assert date.fromisoformat(g["last"]) == TODAY.fromordinal(TODAY.toordinal() + g["max_age_days"] - g["age_days"])
            assert g["obs_ids"] == src["reading"]["obs_ids"]
    assert ages["near_x"] == 100 * ages["near_share"]
    assert ages["scored_now"] == card["scored"]["value"]
    assert ages["scored_after"] == sum(1 for r in ages["rows"] if r["after"] is not None)
    assert ages["near"] == sum(1 for r in ages["rows"] for g in r["gauges"] if g["near"])


def test_what_would_be_left_is_the_scoring_rule_run_again_without_the_readings_near_their_limit():
    spec = yaml.safe_load(ar.TIGHTNESS.read_text())
    inp = next(i for i in spec["inputs"] if i["id"] == "foundry")
    a, b = (g["id"] for g in inp["gauges"])
    readings = {a: {"x": 0.5, "age": 290, "grade": "C"}, b: {"x": 0.5, "age": 10, "grade": "D"}}
    now = score_input(inp, readings, spec["rules"])
    kept = score_input(inp, {b: readings[b]}, spec["rules"])
    row = mf.after(inp, readings, {a}, spec["rules"])
    assert now["score"] is not None and row == ({"score": kept["score"], "word": kept["word"]} if kept["score"] is not None else None)
    assert mf.after(inp, readings, {a, b}, spec["rules"]) is None  # nothing left to score from
    assert mf.after(inp, readings, set(), spec["rules"]) == {"score": now["score"], "word": now["word"]}


def test_every_new_figure_is_placed_in_the_essay_and_registered():
    essay = ar.ESSAYS["migration"].read_text()
    page = PAGE.read_text()
    for name in NEW:
        assert name in ar.PLATES["migration"] and essay.count(f"[plate:{name}]") == 1, name
        assert re.search(rf"\b{name}: <", page), name
    assert {"strip", "scorecard"} <= ar.PLATES["migration"]  # the two the page already had stay
    assert essay.index("[plate:chain]") < essay.index("### Folio II")  # the summary of the rule sits near the top


def test_every_figure_states_its_kind_and_carries_a_key_and_a_foot():
    src = TSX.read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"\s+title=[^\n]+\s+note=\{(KIND_LABEL\.[a-z]+|`\$\{KIND_LABEL\.[a-z]+\}[^`]+`)\}', src)
    assert sorted(f[0] for f in figures) == sorted(NEW)
    assert len(re.findall(r"<Figure\b", src)) == len(figures) == src.count("keys={") == src.count("foot={")
    assert len(figures) + len(re.findall(r"<Figure\b", (WEB / "components" / "MigrationParts.tsx").read_text())) >= 5
    charts = [n for n, kind in figures if "KIND_LABEL.model}" not in kind and kind != "KIND_LABEL.model"]
    assert src.count("table={") >= len(charts)  # every chart folds its numbers beneath it


def test_hatching_is_kept_for_judgement():
    src = TSX.read_text()
    deals = src[src.index("export function DealsPlate") : src.index("export function AgesPlate")]
    ages = src[src.index("export function AgesPlate") : src.index("export function BlindPlate")]
    assert "hatch" not in deals and "hatch" not in ages  # plain records
    blind = src[src.index("export function BlindPlate") : src.index("export function CallsPlate")]
    assert "hatch" in blind and "conjecture" in blind  # the one judgement drawn is labelled where it is drawn


def test_the_figures_words_type_no_digit_but_a_year_and_no_number_word():
    spec = ar.load()["migration"]["chain"]
    seen = [x["label"] for x in spec["links"]] + [t for s_ in spec["states"] for t in (s_["title"], s_["text"])] + [spec["between"]]
    for text in (TSX.read_text(), KIT.read_text()):
        for line in text.splitlines():
            assert not NUMBER_WORD.search(line), line.strip()[:120]
        # what a reader sees: text between tags, and the worded props
        seen += re.findall(r">([^<>{}=]+)<", text) + re.findall(r'(?:title|tableLabel|label)="([^"]+)"', text)
    for t in seen:
        assert not re.search(r"\d", YEAR.sub("", t)), t
        assert not NUMBER_WORD.search(t), t
