"""The census page's figures (plan Part 45b). Every block is laid out by the export from the bundle's own tables: it
sums to the manifest headline, its bars end at one hundred percent, its marks lie inside the plot, and "all three models
pass" lies inside "passes" wherever a figure draws one."""

import json
import re
from pathlib import Path

import pytest

from ai_tracker import census

ROOT = Path(__file__).resolve().parents[1]
SPEC = census.load()
BUNDLE = census.bundle(SPEC)
HEAD = json.loads((BUNDLE / "manifest.json").read_text())["headline"]
INDEX, _ = census.build(SPEC, census.fetches())
FIG = INDEX.get("figures", {})


def _ends_at_100(bar):
    x = 0.0
    for s in bar:
        assert abs(s["x"] - x) < 1e-9 and s["w"] >= 0
        x += s["w"]
    assert abs(x - 100) < 1e-9


def _ticks(ticks):
    assert ticks[0]["left"] == 0 and ticks[-1]["left"] == 100 and all(t["label"] for t in ticks)


def test_the_whole_payroll_is_split_four_ways_and_sums_to_the_headline():
    w = FIG["whole"]
    usd = {p["part"]: p["usd"] for p in w["parts"]}
    assert list(usd) == ["passes", "waits_on_check", "physical", "rest"]  # the firm page's cut, in its order
    assert abs(sum(usd.values()) - HEAD["knowledge_payroll_usd"]) < 1 and abs(w["payroll"] - HEAD["knowledge_payroll_usd"]) < 1
    assert abs(usd["passes"] - HEAD["passes_usd"]) < 1 and abs(w["passes"] - HEAD["passes_usd"]) < 1
    assert abs(usd["waits_on_check"] - HEAD["blocked_by_missing_check_usd"]) < 1
    assert abs(w["agreed3"] - HEAD["agreed_all_three_usd"]) < 1
    assert abs(sum(p["share"] for p in w["parts"]) - 1) < 1e-9
    _ends_at_100(w["parts"])
    assert 0 < w["agreed3_x"] < w["parts"][0]["w"]  # all three pass, inside passes
    assert w["ref"].startswith(f"census:{SPEC['version']}/")


def test_the_screen_counts_payroll_by_the_reason_the_bundle_gives_each_task():
    s = FIG["screen"]
    gates = {g["id"]: g for g in s["gates"]}
    qs = {q["id"]: q for q in s["questions"]}
    assert list(gates) == ["physical", "accountable"] and list(qs) == ["hours", "check", "stakes"]
    voted = s["voted"]["usd"]
    assert abs(sum(g["usd"] for g in gates.values()) + voted - HEAD["knowledge_payroll_usd"]) < 1
    assert abs(s["passes"] - HEAD["passes_usd"]) < 1 and abs(s["agreed3"] - HEAD["agreed_all_three_usd"]) < 1
    failing = voted - s["passes"]
    assert all(0 < q["usd"] <= failing + 1 for q in qs.values())
    assert sum(q["usd"] for q in qs.values()) >= failing - 1  # every task that fails names at least one question
    assert qs["check"]["usd"] == max(q["usd"] for q in qs.values())  # the figure's title says so
    for m in [*gates.values(), *qs.values(), s["voted"]]:
        assert 0 < m["w"] <= 100 and abs(m["w"] - 100 * m["share"]) < 1e-9
    assert 0 < s["agreed3_x"] < s["passes_w"] <= 100


def test_a_reason_the_site_has_not_read_is_an_error_not_a_silent_rest():
    assert census.reason("no existing check settles it, and a failure is too expensive") == {"check", "stakes"}
    with pytest.raises(ValueError):
        census.reason("a phrase a later bundle adds")


def test_the_dial_is_drawn_on_one_dollar_axis_with_the_rule_used_marked():
    d = FIG["dial"]
    val = json.loads((BUNDLE / "validation.json").read_text())["dial"]
    assert [(r["passes"], r["agreed3"]) for r in d["rows"]] == [(x["freed"], x["agreed3"]) for x in val]
    used = [r for r in d["rows"] if r["headline"]]
    assert len(used) == 1 and abs(used[0]["passes"] - HEAD["passes_usd"]) < 1 and abs(used[0]["agreed3"] - HEAD["agreed_all_three_usd"]) < 1
    _ticks(d["ticks"])
    for r in d["rows"]:
        assert 0 <= r["agreed3_x"] <= r["w"] <= 100 and r["ref"].startswith(f"census:{SPEC['version']}/validation.json#")
    ws = [r["w"] for r in d["rows"]]
    assert ws == sorted(ws)  # each step looser passes more


def test_the_function_bars_sum_to_the_headline_and_match_the_function_table():
    rows = FIG["functions"]
    table = {f["function"]: f for f in INDEX["functions"]}
    assert {r["function"] for r in rows} == set(table)
    for key, col in (("payroll", "knowledge_payroll_usd"), ("passes", "passes_usd"), ("agreed3", "agreed_all_three_usd"), ("waits_on_check", "blocked_by_missing_check_usd")):
        assert abs(sum(r[key] for r in rows) - HEAD[col]) < 1, key
    for r in rows:
        f = table[r["function"]]
        assert abs(r["passes"] - f["passes"]) < 1 and abs(r["waits_on_check"] - f["blocked_by_missing_check"]) < 1 and abs(r["payroll"] - f["payroll"]) < 1
        assert abs(r["share_passes"] - f["share_passes"]) < 1e-4  # the bundle's own share, to its rounding
        assert abs(r["passes"] + r["waits_on_check"] + r["physical"] + r["rest"] - r["payroll"]) < 1
        _ends_at_100(r["bar"])
        assert 0 <= r["agreed3_x"] <= r["bar"][0]["w"] and r["ref"] == f["ref"]
    shares = [r["share_passes"] for r in rows]
    assert shares == sorted(shares, reverse=True)


def test_each_model_alone_is_drawn_by_function_and_sums_to_its_own_headline():
    s = FIG["scorers"]
    _ticks(s["ticks"])
    whole, rows = s["rows"][0], s["rows"][1:]
    assert whole["function"] is None and len(rows) == len(INDEX["functions"])
    for k in INDEX["scorers"]:
        assert abs(whole["by_scorer"][k]["usd"] - HEAD["by_scorer_passes_usd"][k]) < 1
        assert abs(sum(r["by_scorer"][k]["usd"] for r in rows) - HEAD["by_scorer_passes_usd"][k]) < 1
    assert abs(whole["passes"] - HEAD["passes_usd"]) < 1 and abs(whole["agreed3"] - HEAD["agreed_all_three_usd"]) < 1
    for r in s["rows"]:
        xs = [r["by_scorer"][k]["x"] for k in INDEX["scorers"]]
        assert all(0 <= x <= 100 for x in [*xs, r["vote_x"], r["agreed3_x"]])
        assert r["agreed3_x"] <= min(xs) + 1e-9  # what all three pass, none alone can fall below
        assert min(xs) - 1e-9 <= r["vote_x"] <= max(xs) + 1e-9  # two of three lies between the lowest and the highest
        assert (r["lo_x"], r["hi_x"]) == (min(xs), max(xs))


def test_the_industry_bars_are_the_table_s_first_rows_on_one_dollar_axis():
    f = FIG["industries"]
    _ticks(f["ticks"])
    top = INDEX["industries"][: len(f["rows"])]
    assert len(f["rows"]) == 15 and [r["naics"] for r in f["rows"]] == [i["naics"] for i in top]
    for r, i in zip(f["rows"], top):
        assert (r["passes"], r["agreed3"], r["share_total"], r["ref"]) == (i["passes"], i["agreed3"], i["share_total"], i["ref"])
        assert 0 <= r["agreed3_x"] <= r["w"] <= 100


def test_the_cut_by_kind_of_job_is_the_one_the_firm_page_draws():
    assert INDEX["kinds"] == census.shape(SPEC)


def test_the_rollup_plot_places_every_industry_inside_the_plot_and_draws_the_cut():
    ranked = [
        {"naics": f"5{i:03d}00", "title": f"Industry {i}", "ref": f"r{i}", "rank": i + 1, "share_total": s, "passes": 1e9, "score": s * f,
         "small_share": {"value": f, "derived_id": "d", "obs_ids": ["o"]}, "firms_20_99": {"value": 500.0, "obs_ids": ["f"]}}
        for i, (s, f) in enumerate([(0.14, 0.6), (0.11, 0.5), (0.05, 0.9), (0.03, 0.4), (0.02, 0.2)])
    ]  # fmt: skip
    p = census.rollup_plot(ranked, shown=3)
    assert [pt["listed"] for pt in p["points"]] == [True, True, True, False, False]
    assert all(0 <= pt["x"] <= 100 and 0 <= pt["y"] <= 100 for pt in [*p["points"], *p["cut"]])
    assert p["points"][0]["y"] < p["points"][3]["y"] and p["points"][2]["x"] > p["points"][4]["x"]  # up is more passing, right is more small firms
    assert len(p["cut"]) > 10 and p["cut_points"] == " ".join(f"{c['x']},{c['y']}" for c in p["cut"])
    xs = [c["x"] for c in p["cut"]]
    assert xs == sorted(xs)
    assert p["x"]["ticks"] and p["y"]["ticks"] and p["y"]["chars"] >= 2
    assert census.rollup_plot([]) == {}


SRC = ROOT / "web" / "src"
FOOT = "a screen scored by three AI models, not a record of what has been automated and not a forecast"


def test_the_page_draws_its_figures_and_each_says_its_kind_and_carries_its_table():
    src = (SRC / "components" / "CensusFigures.tsx").read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"[^>]*?note=\{?(`[^`]+`|"[^"]+"|KIND_LABEL\.[a-z]+)', src, re.S)
    n = len(re.findall(r"<Figure\b", src))
    assert len(figures) >= 5 and len(figures) == n, figures  # none without a stated kind
    for prop in ("keys=", "foot=", "table="):
        assert src.count(prop) >= n, prop  # a key for every mark, a foot, and the numbers folded beneath
    assert FOOT in src and src.count("{SCREEN}") >= n  # the caveat rides in every foot
    assert src.count("all three") >= n  # beside every "passes"
    assert "title={r.ref}" in src or "title={row.ref}" in src  # the numbers carry the census reference
    page = (SRC / "app" / "census" / "page.tsx").read_text()
    for name in re.findall(r"export function (\w+Figure)\b", src):
        assert f"<{name}" in page, name
    assert (SRC / "components" / "diagrams" / "census.tsx").exists()
    for kept in ("c.prose.caveats", "Businesses with no card", "Every other industry", "industryHead", "Industries ranked for a rollup"):
        assert kept in page, kept  # no table or caveat left the page


def test_the_figures_type_no_figure_and_claim_no_capability():
    from .test_atlas import NUMBER_WORD

    src = (SRC / "components" / "CensusFigures.tsx").read_text()
    words = re.findall(r'(?:title|label|tableLabel)="([^"]+)"|>([^<>{}]{12,})<', src)
    for s in (a or b for a, b in words):
        assert not re.search(r"\d", s) and not NUMBER_WORD.search(s), s
        assert not re.search(r"\bcan go\b|\btoday\b|\ba range\b", s, re.I), s
