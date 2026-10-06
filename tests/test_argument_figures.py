"""The figures added to /argument (Part 45i): the argument as a map, the five slow variables against the ranges and
direction rules that grade them, and the exits condition by condition. Everything is laid out by argument.figures
from the seed, the essay's own headings, tonight's statuses and the thesis monitor's rows; the web only places it."""

import json
import re
from pathlib import Path

from ai_tracker import argument as ar
from ai_tracker import store as st
from ai_tracker.analysis.bands import _band
from ai_tracker.analysis.direction import window
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.value_chain import stray_digits
from tests.test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
FIGS = WEB / "components" / "ArgumentFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "argument.tsx"
PAGE = WEB / "app" / "argument" / "page.tsx"
BEFORE = {"migration", "as_of", "essay", "facts", "slow_variables", "clocks", "phase", "exits", "headlines", "sources", "record"}
SCORED = {"consistent_with_normal": "normal", "faster_than_normal": "fast"}


def _store() -> st.Store:
    s = st.Store()
    s.derived = run_metrics(s.con)  # data/derived.jsonl is git-ignored: a clean checkout has none
    return s


S = _store()
DOC = ar.build(S)
F = DOC.get("figures") or {}
SPEC = ar.load()
IND = {i.id: i for i in S.seed.indicators}
THESIS = {v["id"]: v for v in st.read_jsonl(st.DATA / "thesis.jsonl")}


def test_the_figures_add_one_block_and_change_no_field_the_page_already_reads():
    assert set(DOC) == BEFORE | {"figures"}
    assert set(F) == {"map", "readings", "exits"}
    assert DOC["slow_variables"] == SPEC["slow_variables"]
    assert [(e["monitor"], e["state"]) for e in DOC["exits"]] == [(e["monitor"], THESIS[e["monitor"]]["state"]) for e in SPEC["exits"]]
    assert all(set(e) == {"monitor", "label", "text", "state"} for e in DOC["exits"])


def test_the_new_plates_are_registered_for_the_full_essay_only_and_placed_in_it():
    assert ar.PLATES["full"] == {"clocks", "perez", "stack", "record", "map", "readings", "exits"}
    assert ar.PLATES["home"] == {"clocks", "perez", "stack"}  # the home page reuses plates and gains none
    text = ar.ESSAYS["full"].read_text()
    page = PAGE.read_text()
    for name in ("map", "readings", "exits"):
        assert text.count(f"[plate:{name}]") == 1
        assert re.search(rf"\b{name}: <", page), name
    assert ar.problems(S)[0] == []


def test_the_map_places_every_slow_variable_and_every_exit_once_under_the_essays_own_claims():
    rows = F["map"]
    claims = dict(re.findall(r"^### Folio [IVX]+ · (.+)\n\n## (.+)$", ar.ESSAYS["full"].read_text(), re.M))
    assert all(r["claim"] == claims[r["folio"]] and r["label"].endswith(r["folio"]) for r in rows)
    watched = [w for r in rows for w in r["watches"]]
    assert [w["id"] for w in watched] == [v["id"] for v in SPEC["slow_variables"]]
    labels = {v["id"]: v["label"] for v in SPEC["slow_variables"]}
    assert all(w["label"] == labels[w["id"]] and w["status"] == S.current(w["id"]).new_status for w in watched)
    exits = [e for r in rows for e in r["exits"]]
    assert sorted(e["monitor"] for e in exits) == sorted(e["monitor"] for e in SPEC["exits"])
    by = {e["monitor"]: e for e in DOC["exits"]}
    assert all((e["label"], e["state"]) == (by[e["monitor"]]["label"], by[e["monitor"]]["state"]) for e in exits)
    phased = [r for r in rows if r["phase"]]
    assert len(phased) == 1 and phased[0]["phase"] == DOC["phase"]["state"]
    assert all(r["watches"] or r["phase"] for r in rows)  # no claim stands on nothing


def test_a_ranged_reading_sits_inside_a_range_only_when_its_status_says_that_range():
    ranged = F["readings"]["ranged"]
    want = [v["id"] for v in SPEC["slow_variables"] if IND[v["id"]].normal_band]
    assert [r["id"] for r in ranged] == want and want
    for r in ranged:
        ind = IND[r["id"]]
        value, _, ids, _ = S.band_input(ind)
        assert (r["value"], r["obs_ids"], r["status"]) == (value, ids, S.current(ind.id).new_status)
        zones = {z["key"]: z for z in r["zones"]}
        assert list(zones) == ["normal", "between", "fast"]
        assert zones["normal"]["x"] == 0 and abs(zones["fast"]["x"] + zones["fast"]["w"] - 100) < 0.01
        assert abs(zones["normal"]["w"] - zones["between"]["x"]) < 0.01  # the ranges meet with no gap and no overlap
        assert abs(zones["between"]["x"] + zones["between"]["w"] - zones["fast"]["x"]) < 0.01
        assert [e["value"] for e in r["edges"]] == [ind.normal_band.hi, ind.fast_band.lo]
        assert [e["x"] for e in r["edges"]] == [zones["between"]["x"], zones["fast"]["x"]]
        assert 0 <= r["x"] <= 100
        falls = {"consistent_with_normal": "normal", "faster_than_normal": "fast", "emerging": "between"}[
            _band(value, ind.normal_band, ind.fast_band, ind.falsifying_band).value
        ]
        z = zones[falls]
        assert z["x"] - 0.01 <= r["x"] <= z["x"] + z["w"] + 0.01  # drawn to scale, where the number falls
        if r["lane"] == "inside":
            assert SCORED.get(r["status"]) == falls and not r["held"]
        elif r["lane"] == "between":
            assert falls == "between" and r["status"] == "emerging" and not r["held"]
        elif r["lane"] == "line":
            assert r["x"] in [e["x"] for e in r["edges"]] and r["held"]
        else:  # held: the number falls in a range the site does not score it in, so it is set outside with a reason
            assert r["lane"] == "outside" and r["held"] and SCORED.get(r["status"]) != falls
        assert set(r["held"]) <= {"interval", "edge", "tier", "single", "reason"}


def test_tonight_one_reading_is_held_outside_its_range_and_says_why():
    held = [r for r in F["readings"]["ranged"] if r["lane"] == "outside"]
    assert [r["id"] for r in held] == ["bbd_work_hours_assisted"] and held[0]["held"] == ["single"]
    src = PARTS.read_text() + FIGS.read_text()
    assert "HELD_WORDS" in src and all(f"{k}:" in src for k in ("interval", "edge", "tier", "single", "reason"))


def test_a_directed_reading_draws_the_window_its_rule_compares_and_the_dead_band_round_its_start():
    directed = F["readings"]["directed"]
    want = [v["id"] for v in SPEC["slow_variables"] if IND[v["id"]].direction_rule]
    assert [r["id"] for r in directed] == want and want
    assert len(directed) + len(F["readings"]["ranged"]) == len(SPEC["slow_variables"])
    for r in directed:
        ind = IND[r["id"]]
        pts = {p["as_of"]: p for p in S.headline(ind) if p["value"] is not None}
        win = window([(a, p["value"]) for a, p in pts.items()], ind.direction_rule)
        assert (r["start"]["as_of"], r["start"]["value"]) == win[0] and (r["end"]["as_of"], r["end"]["value"]) == win[-1]
        assert r["start"]["obs_ids"] == pts[win[0][0]]["obs_ids"] and r["end"]["obs_ids"] == pts[win[-1][0]]["obs_ids"]
        assert r["status"] == S.current(ind.id).new_status and r["higher_is"] == ind.direction_rule.higher_is
        assert 0 <= r["dead"]["x"] < r["start"]["x"] < r["dead"]["x"] + r["dead"]["w"] <= 100
        assert 0 <= r["end"]["x"] <= 100
        moved = abs(win[-1][1] - win[0][1]) > ind.direction_rule.dead_band
        outside = not (r["dead"]["x"] <= r["end"]["x"] <= r["dead"]["x"] + r["dead"]["w"])
        assert moved == outside  # a move the rule counts leaves the shaded band; one it ignores stays in it
        assert (r["end"]["x"] > r["start"]["x"]) == (win[-1][1] > win[0][1])


def test_every_exit_is_drawn_with_every_condition_its_monitor_tests():
    rows = F["exits"]["rows"]
    assert [r["monitor"] for r in rows] == [e["monitor"] for e in SPEC["exits"]]
    for r, e in zip(rows, DOC["exits"]):
        v = THESIS[r["monitor"]]
        assert (r["label"], r["state"]) == (e["label"], v["state"])
        tested = v["conds"] + v["counter"]
        assert [(c["text"], c["detail"], c["holds"], c["obs_ids"]) for c in r["conds"]] == [
            (c["text"], c["detail"], c["holds"], c["obs_ids"]) for c in tested
        ]
        assert [c["counter"] for c in r["conds"]] == [False] * len(v["conds"]) + [True] * len(v["counter"])
        assert all(c["label"] for c in r["conds"])
        mine = [c for c in r["conds"] if not c["counter"]]
        assert (r["n"], r["met"]) == (len(mine), len([c for c in mine if c["holds"] is True]))
    n = F["exits"]["counts"]
    assert n["exits"] == len(rows) and n["met"] == len([r for r in rows if r["state"] == "supported"])
    assert n["contradicted"] == len([r for r in rows if r["state"] == "contradicted"])
    assert n["untestable"] == len([r for r in rows if r["state"] == "untestable"])


def test_the_seed_names_every_condition_and_its_new_words_type_no_figure():
    for e in SPEC["exits"]:
        v = THESIS[e["monitor"]]
        assert len(e["conditions"]) == len(v["conds"]) + len(v["counter"]), e["monitor"]
        for c in e["conditions"]:
            assert not stray_digits(c["label"]) and not NUMBER_WORD.search(c["label"]), c["label"]
    folios = set(re.findall(r"^### Folio [IVX]+ · (.+)$", ar.ESSAYS["full"].read_text(), re.M))
    assert all(r["folio"] in folios for r in SPEC["map"])


def test_no_title_states_a_finding_the_data_could_overturn_unguarded():
    """Titles describe or ask. The one sentence that states tonight's result is written from the export's counts."""
    src = FIGS.read_text()
    titles = re.findall(r'<Figure\s+id="fig-[a-z]+"\s+title="([^"]+)"', src)
    assert len(titles) == 3
    for t in titles:
        assert not re.search(r"\b(nothing|none|no exit|every|all|still|already|has not|is not)\b", t, re.I), t
    assert "x.counts.met" in src and "x.counts.contradicted" in src


def test_every_figure_states_its_kind_and_has_a_key_and_a_foot_and_the_page_has_at_least_five():
    src = FIGS.read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"\s+title="[^"]+"\s+note=\{?("[^"]+"|`[^`]+`|KIND_LABEL\.[a-z]+)', src)
    assert [f[0] for f in figures] == ["map", "readings", "exits"], figures
    assert len(re.findall(r"<Figure\b", src)) == len(figures)
    assert all("KIND_LABEL." in f[1] for f in figures)
    blocks = re.split(r"(?=<Figure\b)", src)[1:]
    assert all("keys={" in b and "foot={" in b for b in blocks)
    charts = [b for b in blocks if 'id="fig-map"' not in b]
    assert all("table={" in b for b in charts)  # the numbers folded beneath, never hover-only
    page = PAGE.read_text()
    assert all(k in page for k in ("FourClocks", "PerezCurve", "FourPlacesCompact", "StackPlate", "CaseRecord", "SlowVariables", "Exits"))
    assert len(ar.PLATES["full"]) >= 5


def test_figures_that_draw_the_labs_say_a_model_made_by_one_of_them_drafted_the_figure():
    src = FIGS.read_text()
    for fig in ("ReadingsFigure", "ExitsFigure"):
        body = src.split(f"export function {fig}")[1].split("\nexport function")[0]
        assert "<Drafted" in body, fig
    assert "a model made by Anthropic" in src


def test_the_web_keeps_the_estimates_set_apart():
    """The chip makers' share rests partly on an estimate for two labs and the value kept by users on one survey:
    the row says so from the export, and the mark is hatched."""
    by = {r["id"]: r for r in F["readings"]["directed"]}
    assert by["consumer_surplus_wta"]["estimate"] and by["gross_profit_semis_share"]["estimate"]
    assert all(r["grade"] == S._card(IND[r["id"]])["grade"] for r in by.values())
    assert "hatch" in PARTS.read_text() and "r.estimate" in FIGS.read_text()


def test_figure_words_type_no_digit_but_a_year_and_no_number_word():
    for f in (FIGS, PARTS):
        src = re.sub(r"//[^\n]*", "", f.read_text())
        words = re.findall(r'(?:title|note|label|aria-label)="([^"]+)"', src) + re.findall(r">([^<>{}=;]+)<", src)
        words += [q for q in re.findall(r'"([^"\n]+)"', src) if len(q.split()) >= 3 and (q != q.lower() or "-" not in q)]
        for w in words:
            w = w.replace("&apos;", "'")
            assert not stray_digits(w), (f.name, w)
            assert not NUMBER_WORD.search(w), (f.name, w)


def test_the_committed_export_carries_the_figures():
    doc = json.loads((ROOT / "web" / "data" / "argument.json").read_text())
    assert set(doc["figures"]) == {"map", "readings", "exits"}
    assert [r["id"] for r in doc["figures"]["readings"]["ranged"] + doc["figures"]["readings"]["directed"]]
