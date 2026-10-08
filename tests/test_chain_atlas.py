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


def test_the_real_file_names_only_known_businesses_calls_and_futures_and_types_no_figure():
    assert ca.problems(SPEC, opportunities.load(), OUTLOOK) == []
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
    errors = "\n".join(ca.problems(bad, opportunities.load(), OUTLOOK))
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
    doc = ca.build(SPEC, OPS, OUTLOOK)
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
    doc = ca.build(SPEC, OPS, OUTLOOK)
    for b in (b for g in doc["groups"] for b in g["businesses"]):
        effects = {m["effect"] for m in b["marks"]}
        assert b["holds"] == ("stronger" in effects and not effects & {"weaker", "breaks"}), b["id"]
    spec = copy.deepcopy(SPEC)
    for b in spec["businesses"].values():
        b["futures"] = {}
    assert not any(b["holds"] for g in ca.build(spec, OPS, OUTLOOK)["groups"] for b in g["businesses"]), (
        "unjudged is not robust"
    )


def test_the_committed_export_is_the_build_and_check_reads_the_file():
    assert json.loads((ROOT / "web" / "data" / "chain_atlas.json").read_text()) == json.loads(
        json.dumps(ca.build(SPEC, OPS, OUTLOOK))
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
    for b in (b for g in ca.build(SPEC, OPS, OUTLOOK)["groups"] for b in g["businesses"]):
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
