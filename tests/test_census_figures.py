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
    # the figure's title: for most work that fails, the reason given most often is the missing check
    assert 'title="For most work that fails the screen, the reason given most often is that no existing check settles it"' in FIGURES
    assert qs["check"]["usd"] == max(q["usd"] for q in qs.values())
    assert qs["check"]["usd"] > 0.5 * s["payroll"] and qs["check"]["usd"] > 0.5 * failing
    for m in [*gates.values(), *qs.values(), s["voted"]]:
        assert 0 < m["w"] <= 100 and abs(m["w"] - 100 * m["share"]) < 1e-9
    assert 0 < s["agreed3_x"] < s["passes_w"] <= 100


def test_the_screen_s_middle_bars_are_named_as_the_reason_given_most_often_on_a_stated_base():
    # the bundle writes only the question(s) most often failed among the models voting no, so a bar is not "fails that question"
    assert "fails that question" not in FIGURES and "Fails:" not in FIGURES and "fails each" not in FIGURES
    for words in ("the reason the models that voted no gave most often", "Payroll that fails, by the reason given most often", "Most often given: {QUESTION[q.id]}",
                  "the reason given most often for the payroll that fails, as a share of all knowledge payroll", "so each bar is a floor for that question"):
        assert words in FIGURES, words
    assert "most often failed among the scorers voting no" in (census.reason.__doc__ or "")


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


def test_the_dial_s_title_holds_the_biggest_jump_is_letting_a_person_s_judgement_count():
    assert 'title="Each looser step passes more payroll, and the biggest jump comes from letting a person&apos;s judgement count as the check"' in FIGURES
    val = json.loads((BUNDLE / "validation.json").read_text())["dial"]
    used = next(x for x in val if x["headline"])
    person = next(i for i, x in enumerate(val) if x["g"] < used["g"])  # the first step that loosens who may check
    passes = [x["freed"] for x in val]
    assert passes == sorted(passes) and len(set(passes)) == len(passes)
    steps = range(1, len(val))
    assert max(steps, key=lambda i: passes[i] - passes[i - 1]) == person
    assert max(steps, key=lambda i: passes[i] / passes[i - 1]) == person


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


def test_the_functions_title_holds_in_most_functions_more_waits_on_a_check_than_passes():
    assert 'title="In most functions, more work waits on a check than passes"' in FIGURES
    rows = FIG["functions"]
    assert sum(r["waits_on_check"] > r["passes"] for r in rows) > len(rows) / 2


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


def test_the_scorers_title_holds_most_functions_are_far_apart_and_one_model_is_usually_highest():
    assert 'title="In most functions the three models are far apart, and the same model is usually the highest"' in FIGURES
    rows = FIG["scorers"]["rows"][1:]
    shares = [{k: r["by_scorer"][k]["share"] for k in INDEX["scorers"]} for r in rows]
    assert sum(max(s.values()) > 2 * min(s.values()) for s in shares) > len(rows) / 2  # far apart: the highest more than double the lowest
    tops = [max(s, key=s.get) for s in shares if max(s.values()) > 0]
    assert max(tops.count(k) for k in INDEX["scorers"]) > len(rows) / 2
    assert "Where nothing passes, the marks sit together at zero." in FIGURES


def test_rows_whose_marks_would_stack_print_the_rule_and_all_three_in_type():
    rows = FIG["scorers"]["rows"]
    assert not rows[0]["tight"]  # the whole payroll keeps every mark
    for r in rows:
        assert r["tight"] == (r["hi_x"] - r["agreed3_x"] < census.TIGHT)
        assert (r["hi_x"] < r["note_x"] <= 60) if r["tight"] else r["note_x"] is None  # room left for the type on a phone
        if r["passes"] == 0:
            assert r["tight"]
    assert any(r["tight"] for r in rows) and "r.tight" in FIGURES


def test_the_industries_are_a_table_not_a_second_figure_ranked_by_size():
    assert "industries" not in FIG and "IndustriesFigure" not in FIGURES + PAGE
    assert "<Rows head={industryHead} rows={c.industries.slice(" in PAGE and "Every other industry" in PAGE


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
    assert [pt.get("label") in census.LABEL_SIDES for pt in p["points"]] == [True, True, True, False, False]  # a side for each rank
    assert all(pt.get("label_wide") in census.LABEL_SIDES for pt in p["points"][:3])
    xs = [c["x"] for c in p["cut"]]
    assert xs == sorted(xs)
    assert p["x"]["ticks"] and p["y"]["ticks"] and p["y"]["chars"] >= 2
    assert census.rollup_plot([]) == {}


def test_rank_labels_in_a_crowd_take_a_further_place_before_they_cover_a_dot_or_each_other():
    # five listed industries in a knot (spaced as the knot on the plot when this was written) and a pair side by side
    spots = [(0.64, 0.0541), (0.63, 0.0504), (0.64, 0.0471), (0.668, 0.045), (0.577, 0.0492), (0.30, 0.10), (0.33, 0.10), (0.95, 0.15), (0.05, 0.01)]
    ranked = [
        {"naics": f"5{i:03d}00", "title": f"Industry {i}", "ref": f"r{i}", "rank": i + 1, "share_total": s, "passes": 1e9, "score": s * f,
         "small_share": {"value": f, "derived_id": "d", "obs_ids": ["o"]}, "firms_20_99": {"value": 500.0, "obs_ids": ["f"]}}
        for i, (f, s) in enumerate(spots)
    ]  # fmt: skip
    pts = census.rollup_plot(ranked, shown=len(spots))["points"]
    hit = lambda a, b: a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]  # noqa: E731
    for key in ("label", "label_wide"):  # a pixel is a different share of the plot on a phone and on a desk
        boxes = [census.label_box(p, key) for p in pts]
        dots = [census.dot_box(p, key) for p in pts]
        for i, a in enumerate(boxes):
            assert 0 <= a[0] and a[0] + a[2] <= 100 and 0 <= a[1], pts[i]  # inside the plot
            assert not any(hit(a, b) for b in boxes[i + 1 :]), (key, pts[i])
            assert not any(hit(a, d) for j, d in enumerate(dots) if j != i), (key, pts[i])
    assert {p["label"] for p in pts} - {"r", "l", "t", "b"}  # on a phone the knot needs more than the four nearest places
    assert "p.label_wide" in FIGURES and "md:hidden" in FIGURES
    assert all(f"{k}:" in FIGURES or f'"{k}":' in FIGURES for k in census.LABEL_SIDES)  # the page knows how to draw each place


SRC = ROOT / "web" / "src"
FIGURES = (SRC / "components" / "CensusFigures.tsx").read_text()
PAGE = (SRC / "app" / "census" / "page.tsx").read_text()
FOOT = "a screen scored by three AI models, not a claim about what AI can do and not a forecast"


def test_the_strip_leads_and_its_last_part_says_what_it_holds():
    assert PAGE.index("<WholeFigure") < PAGE.index("<ScreenFigure")  # the two-second figure before the fifteen-second one
    assert "work whose most-given reason is a missing check but on which the models split over whether anything else holds it" in FIGURES


def test_the_page_prints_the_payroll_left_out_beside_the_part_the_vote_would_have_passed():
    # the manifest's "removed" figures count only verdicts the filter changed; the payroll flagged is several times larger
    assert "Removed as" not in PAGE and "was removed before the vote" not in PAGE and "Waiting on a check" not in PAGE
    for words in ("c.figures.screen.gates.map(", '"Left out as physical work", usd(gate.physical)', '"Left out as an accountable sign-off, and not physical", usd(gate.accountable)',
                  '"Of that, payroll the vote would otherwise have passed", usd(h.physical_removed)', '"Of that, payroll the vote would otherwise have passed", usd(h.accountable_removed)',
                  "is left out whatever the vote says: {usd(gate.physical)} of payroll", "the filter changed the verdict on {usd(m.physical_gate.removed_usd)}",
                  "tasks drawn from that part found", "Waits only on a check: at least two of the three models find it quick to judge and cheap to get wrong, with no existing check"):
        assert words in PAGE, words
    gates = {g["id"]: g["usd"] for g in FIG["screen"]["gates"]}
    assert gates["physical"] > INDEX["headline"]["physical_removed"] > 0 and gates["accountable"] > INDEX["headline"]["accountable_removed"] > 0
    assert "margin&apos;s smaller figures" not in FIGURES  # the foot no longer has to explain the margin


def test_waiting_only_on_a_check_is_said_as_the_census_counts_it():
    lede = " ".join(SPEC["sections"]["functions"]["lede"].split())
    assert "at least two of the three models each find quick to judge and cheap to get wrong, with no existing check to settle it" in lede
    assert "More work than this has a missing check as the reason given most often" in lede
    assert "Work waiting only on a check is work at least two of the three models find quick to judge and cheap to get wrong, with no existing check to settle it." in FIGURES
    assert abs(FIG["whole"]["parts"][1]["usd"] - HEAD["blocked_by_missing_check_usd"]) < 1 < FIG["screen"]["questions"][1]["usd"] - HEAD["blocked_by_missing_check_usd"]


def test_the_remaining_feet_say_what_the_review_asked():
    for words in ("rule counts a task when at least two of the three models pass it", 'title="The list is the industries where work that passes and small firms to buy multiply highest"',
                  "Industries just either side of the line are not meaningfully apart.", "is in the table beneath"):
        assert words in FIGURES, words
    role = (SRC / "app" / "census" / "roles" / "[occ]" / "page.tsx").read_text()
    assert "reason given most often" in role


def test_the_page_draws_its_figures_and_each_says_its_kind_and_carries_its_table():
    src = FIGURES
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"[^>]*?note=\{?(`[^`]+`|"[^"]+"|KIND_LABEL\.[a-z]+)', src, re.S)
    n = len(re.findall(r"<Figure\b", src))
    assert len(figures) >= 5 and len(figures) == n, figures  # none without a stated kind
    for prop in ("keys=", "foot=", "table="):
        assert src.count(prop) >= n, prop  # a key for every mark, a foot, and the numbers folded beneath
    assert FOOT in src and src.count("{SCREEN}") >= n  # the caveat rides in every foot
    assert src.count("all three") >= n  # beside every "passes"
    assert "title={r.ref}" in src or "title={row.ref}" in src  # the numbers carry the census reference
    page = PAGE
    for name in re.findall(r"export function (\w+Figure)\b", src):
        assert f"<{name}" in page, name
    assert (SRC / "components" / "diagrams" / "census.tsx").exists()
    for kept in ("c.prose.caveats", "Businesses with no card", "Every other industry", "industryHead", "Industries ranked for a rollup"):
        assert kept in page, kept  # no table or caveat left the page


def test_the_figures_type_no_figure_and_claim_no_capability():
    from .test_atlas import NUMBER_WORD

    src = (SRC / "components" / "CensusFigures.tsx").read_text()
    words = re.findall(r'(?:title|label|tableLabel|first)="([^"]+)"|[>}]\s*([A-Za-z][^<>{}=;()]{11,})[<{]', src)
    assert len(words) > 40
    for s in (a or b for a, b in words):
        assert not re.search(r"\d", s) and not NUMBER_WORD.search(s), s
        assert not re.search(r"\bcan go\b|\btoday\b|\ba range\b", s, re.I), s
