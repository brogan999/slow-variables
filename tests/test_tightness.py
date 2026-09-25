"""The tightness engine is pure, so these tests never build a Store. Golden values are the prototype's own
component scores, so the port is held to the arithmetic it replaces."""

import math

import pytest
import yaml

from ai_tracker.analysis.tightness import half_up, scale, score_input, word

SPEC = yaml.safe_load(open("seed/tightness.yaml"))
RULES = SPEC["rules"]
INPUTS = {i["id"]: i for i in SPEC["inputs"]}
KINDS = {"no_public_series", "not_read_yet", "gauge_unsound"}


def gauge(inp: str, g: str) -> dict:
    return next(x for x in INPUTS[inp]["gauges"] if x["id"] == g)


def test_scales_reproduce_the_prototypes_component_scores():
    for inp, g, x, points in [
        ("data_centres", "planned_vs_built", 4.5357, 78.20),
        ("foundry", "logic_supply_growth", 0.297, 28.44),
        ("packaging", "cowos_supply_growth", 0.6907, 32.37),
        ("packaging", "cowos_buyer_concentration", 0.3929, 51.86),
        ("memory", "hbm_supply_growth", 0.5282, 45.59),
        ("capital", "capex_growth", 0.8247, 17.61),
    ]:
        got, pinned = scale(x, gauge(inp, g)["knots"])
        assert abs(got - points) < 0.01 and pinned is None, (inp, g)


def test_a_reading_beyond_the_scale_is_pinned_flat_and_a_log_scale_reads_in_dollars():
    knots = gauge("inference", "basket_price")["knots"]
    assert scale(0.4, knots, log10=True) == (12, "low") and scale(500, knots, log10=True) == (92, "high")
    mid, _ = scale(4, knots, log10=True)  # halfway between two and eight dollars on a scale that multiplies
    assert abs(mid - (32 + 55) / 2) < 1e-9
    for bad in (math.nan, math.inf):
        with pytest.raises(ValueError):
            scale(bad, knots)
    with pytest.raises(ValueError):
        scale(0, knots, log10=True)


def test_whole_numbers_round_half_up_and_the_word_follows_the_number_shown():
    assert (half_up(52.5), half_up(28.5), half_up(39.49)) == (53, 29, 39)  # round() would give 52 and 28
    assert [word(n, RULES["words"]) for n in (0, 19, 20, 39, 40, 59, 60, 79, 80, 100)] == [
        "slack", "slack", "easing", "easing", "moderate", "moderate", "tight", "tight", "severe", "severe",
    ]  # fmt: skip


def fresh(x: float, age: int = 0, grade: str = "A") -> dict:
    return {"x": x, "age": age, "grade": grade}


def test_packaging_scores_the_weighted_mean_of_its_two_gauges():
    r = score_input(
        INPUTS["packaging"],
        {"cowos_supply_growth": fresh(0.6907), "cowos_buyer_concentration": fresh(0.3929)},
        RULES,
    )
    assert (r["score"], r["word"], r["used"], r["defined"]) == (40, "moderate", 2, 2)  # 40.17 before rounding
    assert r["factors"]["coverage"] == 0.75  # the hand-judged quarter of the evidence counts as missing


def test_no_usable_data_means_no_score_never_fifty():
    inp = INPUTS["packaging"]
    nothing = score_input(inp, {}, RULES)
    assert (nothing["score"], nothing["word"], nothing["confidence"], nothing["withheld"]) == (
        None,
        None,
        None,
        "nothing",
    )
    stale = score_input(inp, {"cowos_supply_growth": fresh(0.5, age=331)}, RULES)
    assert stale["withheld"] == "nothing" and stale["gauges"][0]["unavailable"] == "past its age limit"
    nan = score_input(inp, {"cowos_supply_growth": fresh(math.nan)}, RULES)
    assert nan["withheld"] == "nothing" and nan["gauges"][0]["unavailable"] == "no reading"
    for i in SPEC["inputs"]:  # an empty store withholds all twenty-three and never raises
        assert score_input(i, {}, RULES)["score"] is None


def test_a_missing_required_gauge_or_thin_coverage_withholds_the_input():
    dc = {**INPUTS["data_centres"], "gauges": [{**g, **({"metric": "m", "max_age_days": 300, "knots": [[0, 0], [1, 50], [2, 100]]} if "unfed" in g else {})} for g in INPUTS["data_centres"]["gauges"]]}  # fmt: skip
    dc["gauges"][1].pop("unfed")
    assert score_input(dc, {"built_power_growth": fresh(1.0)}, RULES)["withheld"] == "required"
    thin = {"ceiling": 90, "hand_judged_weight": 0.8, "gauges": [{"id": "g", "weight": 0.2, "max_age_days": 10, "knots": [[0, 0], [1, 50], [2, 100]]}]}  # fmt: skip
    assert score_input(thin, {"g": fresh(1.0)}, RULES)["withheld"] == "coverage"  # a fifth of the evidence


def test_confidence_falls_with_age_and_grade_and_is_capped_by_the_ceiling():
    inp = INPUTS["capital"]
    new = score_input(inp, {"capex_growth": fresh(0.8)}, RULES)
    old = score_input(inp, {"capex_growth": fresh(0.8, age=190)}, RULES)
    weak = score_input(inp, {"capex_growth": fresh(0.8, grade="D")}, RULES)
    assert new["score"] == old["score"] == weak["score"]  # age and source never move the score
    assert new["confidence"] > old["confidence"] and new["confidence"] > weak["confidence"]
    capped = score_input({**inp, "ceiling": 30}, {"capex_growth": fresh(0.8)}, RULES)
    assert (capped["confidence"], capped["at_ceiling"], capped["hatched"]) == (30, True, True)
    assert new["at_ceiling"] and not old["at_ceiling"]  # a fresh grade-A reading reaches this input's ceiling


def test_the_hatch_is_strictly_under_the_threshold_and_the_floor_applies_after_the_ceiling():
    inp = INPUTS["capital"]
    at = {
        c: score_input({**inp, "ceiling": c}, {"capex_growth": fresh(0.8)}, RULES) for c in (15, 44, 45, 46)
    }
    assert [at[c]["hatched"] for c in (44, 45, 46)] == [True, False, False]
    assert (at[15]["score"], at[15]["withheld"]) == (
        None,
        "confidence",
    )  # a ceiling under the floor can never score


def test_the_seed_is_whole():
    metrics = yaml.safe_load(open("semantic/metrics.yaml"))["metrics"]
    assert len(SPEC["inputs"]) == 23 and [i["n"] for i in SPEC["inputs"]] == list(range(1, 24))
    assert len(INPUTS) == 23 and {i["kind"] for i in SPEC["inputs"]} <= {k["id"] for k in SPEC["kinds"]}
    assert abs(sum(RULES["weights"].values()) - 0.77) < 1e-9 and RULES["words"][-1][0] == 0
    assert INPUTS["energy"]["reads"].startswith("Demand only:")  # the page keeps this caveat open on a phone by its lead
    for i in SPEC["inputs"]:
        gs = i.get("gauges") or []
        assert gs or len(i["withheld"]["because"]) >= 40, i["id"]
        total = sum(g["weight"] for g in gs) + i["hand_judged_weight"]
        want = {"pretraining": 0.75, "capital": 0.85}.get(
            i["id"], 1.0
        )  # under one only where the prototype left a gap
        assert not gs or abs(total - want) < 1e-4, i[
            "id"
        ]  # an input with no gauges keeps the prototype's share alone
        assert "withheld" not in i or i["withheld"]["kind"] in KINDS, i[
            "id"
        ]  # stale_or_thin is the engine's alone
        for g in gs:
            if "unfed" in g:
                assert g["unfed"]["kind"] in KINDS
                continue
            assert g["metric"] in metrics and len(g["scale_rationale"]) >= 40, (i["id"], g["id"])


def test_an_input_whose_metric_gives_nothing_is_the_engines_to_explain_not_the_seeds():
    from datetime import date
    from types import SimpleNamespace

    from ai_tracker import argument as ar

    empty = SimpleNamespace(
        derived_for=lambda m, dims=None: [],
        metric_spec=lambda m: {"unit": "ratio"} if m else {},
        fetchlog=[],
        _chart_sources=lambda ids: {"metric": None, "sources": []},
    )
    card = {i["id"]: i for i in ar.scorecard(empty, date(2026, 9, 21))["inputs"]}
    dc = card["data_centres"]  # one fed gauge with no rows tonight, one unfed gauge with a seeded reason
    assert dc["score"] is None and dc["withheld"]["kind"] == "stale_or_thin"
    assert dc["withheld"]["because"] == RULES["reasons"]["nothing"]
    assert (
        card["routing"]["withheld"]["kind"] == "gauge_unsound"
    )  # every gauge unfed: the seed's own reason stands
    assert card["minerals"]["withheld"]["kind"] == "not_read_yet"
    errors, notes = ar.tightness_problems(empty, date(2026, 9, 21))
    assert errors == [] and len(notes) == 1 and "data_centres (planned_vs_built no reading)" in notes[0]
