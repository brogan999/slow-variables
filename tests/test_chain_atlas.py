"""The value-chain atlas (Part 48): a call on each business that could be built, and what each future on the outlook's
grid does to it. Every word is a model's judgement kept in seed/chain_atlas.yaml; the export lays out every state and
the page only draws it."""

import copy
import json
from pathlib import Path

from ai_tracker import chain_atlas as ca
from ai_tracker import opportunities
from ai_tracker.outlook import load as load_outlook

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
SPEC, OUTLOOK = ca.load(), load_outlook()
OPS = json.loads((ROOT / "web" / "data" / "opportunities.json").read_text())


# Part 48b: what is scarce on each part of the map, now and later, and what each future does to it

MAP = json.loads((ROOT / "web" / "data" / "market_map.json").read_text())
SCORED = {
    r["id"]: r["word"]
    for r in json.loads((ROOT / "web" / "data" / "argument.json").read_text())["migration"]["figures"][
        "ages"
    ]["rows"]
    if r.get("word")
}
ORDER = ["slack", "easing", "moderate", "tight", "severe"]


def atlas(spec=SPEC, scored=SCORED):
    return ca.build(spec, OPS, OUTLOOK, MAP, scored)


def tiles(doc):
    return {c["id"]: c for layer in doc["map"]["layers"] for c in layer["categories"]}


def test_the_real_file_names_only_known_businesses_calls_and_futures_and_types_no_figure():
    assert ca.problems(SPEC, opportunities.load(), OUTLOOK, MAP) == []
    published = {o["id"] for o in opportunities.load()["opportunities"] if o.get("published")}
    assert set(SPEC["businesses"]) == published, "every published business has a call, and nothing else does"


def test_a_broken_file_names_each_problem():
    bad = copy.deepcopy(SPEC)
    first = next(iter(bad["businesses"]))
    bad["businesses"]["no_such_business"] = bad["businesses"][first]
    b = bad["businesses"][first] = copy.deepcopy(bad["businesses"][first])
    b["call"], b["take"] = "buy", ""
    b["kills"] = "Fewer than 3 buyers appear."
    b["futures"] = {
        "steady/nowhere": {"effect": "stronger", "reason": "x"},
        "steady/priced": {"effect": "booms", "reason": ""},
    }
    bad["not_judged"] = {**bad["not_judged"], "steady/priced": "", "nowhere/at_all": "x"}
    del bad["made_by"]["reviewed_by"]
    errors = "\n".join(ca.problems(bad, opportunities.load(), OUTLOOK, MAP))
    for part in (
        "no_such_business",
        "call buy",
        "no take",
        "types a figure",
        "steady/nowhere",
        "effect booms",
        "gives no reason",
        "reviewed_by",
        "is not judged, yet",
        "nowhere/at_all",
        "says why not",
    ):
        assert part in errors, part


def test_the_export_lays_out_every_future_for_every_business():
    doc = atlas()
    cells = [f"{c['progress']}/{c['rules']}" for c in OUTLOOK["scenarios"]["cells"]]
    assert [f["id"] for f in doc["futures"]] == [c for c in cells if c not in SPEC["not_judged"]], (
        "a future nobody judged is no column"
    )
    assert [n["name"] for n in doc["not_judged"]] == ["Control slips away, the rules stay unsettled"] and doc[
        "not_judged"
    ][0]["why"]
    assert doc["futures"][3]["name"] == "Steady progress, courts and insurers price the risk"
    rows = [b for g in doc["groups"] for b in g["businesses"]]
    assert sorted(b["n"] for b in rows) == sorted(m["n"] for m in OPS["figures"]["marks"])
    assert [g["id"] for g in doc["groups"]] == [c["id"] for c in SPEC["calls"]]
    for b in rows:
        assert [m["future"] for m in b["marks"]] == [f["id"] for f in doc["futures"]]
        assert all(
            m["effect"] in ("stronger", "weaker", "breaks", "unchanged") and m["label"] for m in b["marks"]
        )
        assert (
            b["href"] == f"/value-chain/opportunities#op-{b['id']}"
            and b["profit"]
            and b["take"]
            and b["kills"]
        )
    assert doc["made_by"]["model"]


def test_a_business_holds_only_when_some_future_lifts_it_and_none_hurts_it():
    doc = atlas()
    for b in (b for g in doc["groups"] for b in g["businesses"]):
        effects = {m["effect"] for m in b["marks"]}
        assert b["holds"] == ("stronger" in effects and not effects & {"weaker", "breaks"}), b["id"]
    spec = copy.deepcopy(SPEC)
    for b in spec["businesses"].values():
        b["futures"] = {}
    assert not any(b["holds"] for g in atlas(spec)["groups"] for b in g["businesses"]), (
        "unjudged is not robust"
    )


def test_the_committed_export_is_the_build_and_check_reads_the_file():
    assert json.loads((ROOT / "web" / "data" / "chain_atlas.json").read_text()) == json.loads(
        json.dumps(atlas())
    )
    assert "chain_atlas.problems(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()
    assert 'out / "chain_atlas.json"' in (ROOT / "src" / "ai_tracker" / "store.py").read_text()


def test_nothing_that_scores_or_answers_reads_the_judgements():
    src = ROOT / "src" / "ai_tracker"
    for p in [*src.glob("query/*.py"), src / "evaluate.py", src / "argument.py", src / "board.py"]:
        assert not p.exists() or "chain_atlas" not in p.read_text(), p.name


def test_the_page_switches_futures_without_script_and_labels_the_judgement():
    page = (WEB / "app" / "value-chain" / "atlas" / "page.tsx").read_text()
    comp = (WEB / "components" / "ChainAtlas.tsx").read_text()
    assert "chainAtlas()" in page and "<IdeaBox" in page
    assert '"use client"' not in comp and 'type="radio"' in comp and "<details" in comp
    assert "A model&apos;s judgement, not a reading" in comp and "Claude, a model made by Anthropic" in comp
    assert '"/value-chain/atlas"' in (WEB / "lib" / "contents.ts").read_text()
    assert (
        'href="/value-chain/atlas"'
        in (WEB / "app" / "value-chain" / "opportunities" / "page.tsx").read_text()
    )
    assert ".chain-atlas:has(" in (WEB / "app" / "globals.css").read_text()


def test_each_business_links_to_its_place_on_the_map():
    for b in (b for g in atlas()["groups"] for b in g["businesses"]):
        assert b["primary"]["href"].startswith("/value-chain#mm-"), b["id"]


def test_the_page_defines_its_terms_names_what_was_not_judged_and_says_whose_words_it_quotes():
    page = (WEB / "app" / "value-chain" / "atlas" / "page.tsx").read_text()
    comp = (WEB / "components" / "ChainAtlas.tsx").read_text()
    assert (
        "<ChainTerms" in page
        and "<ChainTerms" in (WEB / "app" / "value-chain" / "opportunities" / "page.tsx").read_text()
    )
    assert "What would overturn this call" in comp and "What would undo it" not in comp
    assert 'href="/outlook#scenarios"' in comp and "d.not_judged.map" in comp
    assert "a model&apos;s judgement" in comp.split('id="ca-table"')[1].split("</summary>")[0]
    assert "## Part 48" in (ROOT / "docs" / "plan.md").read_text()


def test_no_take_counts_the_file_and_the_power_grid_is_named_as_one():
    for bid, b in SPEC["businesses"].items():
        text = " ".join([b["take"], b["kills"], *(f["reason"] for f in b["futures"].values())])
        assert "any business here" not in text and "only business here" not in text, (
            f"{bid}: a tally of this file goes stale"
        )
        assert "grid" not in text.replace("power grid", "").replace("on the grid", ""), (
            f"{bid}: say power grid; the grid is the outlook's"
        )


def test_every_part_of_the_map_in_scope_has_a_path_and_nothing_else_does():
    in_scope = {
        c["id"]
        for layer in MAP["layers"]
        for c in layer["categories"]
        if not c.get("out_of_scope") and c.get("number") != "8"
    }
    assert set(SPEC["categories"]) == in_scope
    assert ca.problems(SPEC, opportunities.load(), OUTLOOK, MAP) == []
    assert [t["id"] for t in atlas()["times"]] == ["now", "transition", "mature"]


def test_now_is_the_reading_where_one_is_scored_and_a_labelled_judgement_where_not():
    t = tiles(atlas())
    power = t["power_and_sites"]["states"]["none"]["now"]
    assert power == {
        "word": SCORED["energy"],
        "level": ORDER.index(SCORED["energy"]) + 1,
        "measured": True,
        "label": power["label"],
    }
    assert "probably" not in power["label"]
    proof = t["outcome_verification"]["states"]["none"]["now"]
    assert proof["measured"] is False and proof["word"].startswith("probably ")
    lapsed = tiles(atlas(scored={}))["power_and_sites"]["states"]["none"]["now"]
    assert (
        lapsed["measured"] is False
        and lapsed["word"] == "probably " + SPEC["categories"]["power_and_sites"]["now"]
    ), "a lapsed reading falls back to the judgement"


def test_a_future_never_moves_now_and_moves_later_one_step_clamped():
    doc = atlas()
    t, keys = tiles(doc), [f["key"] for f in doc["futures"]]
    for c in t.values():
        assert set(c["states"]) == {"none", *keys}
        for k in keys:
            assert c["states"][k]["now"] == c["states"]["none"]["now"], (c["id"], k)
            for when in ("transition", "mature"):
                step = c["states"][k][when]["level"] - c["states"]["none"][when]["level"]
                move = next((m["move"] for m in c["moved"] if m["key"] == k), None)
                assert step in ({"tightens": (0, 1), "eases": (0, -1), None: (0,)}[move]), (c["id"], k, when)
                assert 1 <= c["states"][k][when]["level"] <= 5 and c["states"][k][when]["measured"] is False
    proof = t["outcome_verification"]
    assert (
        proof["states"]["steady-priced"]["mature"]["level"] == 5 == proof["states"]["none"]["mature"]["level"]
    ), "severe cannot tighten further"


def test_the_ground_sorts_each_part_by_where_its_shortage_is_heading():
    doc = atlas()
    t = tiles(doc)
    assert [g["id"] for g in doc["ground"]] == ["scarcer", "holds", "eases"]
    assert sorted(i for g in doc["ground"] for i in g["categories"]) == sorted(t)
    for g in doc["ground"]:
        for cid in g["categories"]:
            base = t[cid]["states"]["none"]
            diff = base["mature"]["level"] - base["now"]["level"]
            assert (diff > 0, diff == 0, diff < 0) == (
                g["id"] == "scarcer",
                g["id"] == "holds",
                g["id"] == "eases",
            ), cid


def test_a_broken_path_or_shift_names_each_problem():
    bad = copy.deepcopy(SPEC)
    bad["categories"]["power_and_sites"].update(
        now="scarce", reason="Up 40% since 2024.", reading="no_such_gauge"
    )
    del bad["categories"]["outcome_verification"]
    bad["categories"]["nowhere"] = bad["categories"]["security"]
    bad["shifts"]["steady/priced"]["security"] = {"move": "explodes", "reason": ""}
    bad["shifts"]["loss_of_control/unclear"] = {"security": {"move": "tightens", "reason": "x"}}
    errors = "\n".join(ca.problems(bad, opportunities.load(), OUTLOOK, MAP))
    for part in (
        "word scarce",
        "types a figure",
        "no_such_gauge",
        "outcome_verification has no path",
        "nowhere is not",
        "move explodes",
        "gives no reason",
        "loss_of_control/unclear",
    ):
        assert part in errors, part


def test_the_map_is_the_one_island_and_looks_up_every_state():
    island = (WEB / "components" / "ChainAtlasMap.tsx").read_text()
    comp = (WEB / "components" / "ChainAtlas.tsx").read_text()
    assert '"use client"' in island and '"use client"' not in comp and "<ChainAtlasMap" in comp
    assert "c.states[future]" in island and 'name="ca-time"' in comp
    assert "measured" in island and "a model&apos;s judgement" in island
    assert 'id="ca-ground"' in comp and '"ca-map"' in (WEB / "lib" / "contents.ts").read_text()
