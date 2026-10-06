"""The figures on /value-chain/opportunities (Part 45e). Every mark is laid out by opportunities.build from the records
the cards already show, the rent rubric, the market map and the needs grid on /firm/kinds; the web only places it."""

import json
import re
from pathlib import Path

from ai_tracker import firm_kinds, futures
from ai_tracker import opportunities as op
from ai_tracker.outlook import load as load_outlook
from tests.test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
FIGS = WEB / "components" / "OpportunityFigures.tsx"
PARTS = WEB / "components" / "diagrams" / "opportunities.tsx"
TOP = {"reviewed_by", "reviewed", "opportunities", "sequence", "powers", "counts"}
RECORD = {"id", *op.TEXT, "primary", "adjacent", "powers", "builds_on", "rent", "examples", "n_more_examples", "unmapped",
          "none_independent", "see_also", "blank"}


def _doc():
    map_doc = json.loads((ROOT / "web" / "data" / "market_map.json").read_text())
    return op.build(op.load(), map_doc, load_outlook(), futures.rubric()), map_doc


DOC, MAP = _doc()
F = DOC.get("figures") or {}
RECS = {o["id"]: o for o in DOC["opportunities"]}


def test_the_figures_add_a_block_and_change_no_field_the_cards_read():
    assert set(DOC) == TOP | {"figures"}
    assert all(set(o) == RECORD for o in DOC["opportunities"])
    want = [o["id"] for o in op.load()["opportunities"] if o.get("published")]
    assert [o["id"] for o in DOC["opportunities"]] == want  # the owner's order
    assert [(m["id"], m["n"]) for m in F["marks"]] == [(i, n + 1) for n, i in enumerate(want)]
    assert all(m["name"] == RECS[m["id"]]["name"] and m["verdict"] == RECS[m["id"]]["rent"]["verdict"] for m in F["marks"])
    assert F["example"] == want[0]


def test_who_keeps_it_follows_the_rubrics_rules_in_order_and_places_every_business_once():
    rules = futures.rubric()["pools"]["rules"]
    assert len(F["keeps"]) == len(rules)
    placed = [(i, g["pools"]) for r in F["keeps"] for g in r["groups"] for i in g["ops"]]
    assert sorted(i for i, _ in placed) == sorted(RECS)
    assert all(RECS[i]["rent"]["pools"] == p for i, p in placed)
    assert F["keeps"][0]["key"] == "appropriability=tight" and F["keeps"][-1]["key"] == "otherwise"
    assert all(g["keeper"] for r in F["keeps"] for g in r["groups"])


def test_how_large_is_the_rubrics_table_with_every_business_in_its_cell():
    rubric = futures.rubric()
    size = F["size"]
    assert size["cols"] == rubric["inputs"]["durability"]
    assert [r["kind"] for r in size["rows"]] == list(rubric["tiers"]["rules"])
    seen = []
    for r in size["rows"]:
        for d, c in zip(size["cols"], r["cells"]):
            assert c["tier"] == rubric["tiers"]["rules"][r["kind"]][d] and c["word"]
            for i in c["ops"]:
                rent = RECS[i]["rent"]
                assert (rent["rent_kind"], rent["durability"]) == (r["kind"], d)
                assert rent["tier"] == (c["tier"] if rent["pools"] != "users" else "none")  # competed away keeps nothing
                seen.append(i)
    assert sorted(seen) == sorted(RECS)


def test_the_chain_strip_holds_every_category_of_the_map_and_each_business_where_its_record_puts_it():
    cats = [c for layer in F["chain"] for c in layer["categories"]]
    assert [c["id"] for c in cats] == [c["id"] for layer in MAP["layers"] for c in layer["categories"]]
    by = {c["id"]: c for c in cats}
    for o in RECS.values():
        assert o["id"] in by[o["primary"]["id"]]["primary"]
        assert all(o["id"] in by[a["id"]]["adjacent"] for a in o["adjacent"])
    assert sum(len(c["primary"]) for c in cats) == len(RECS)
    assert sum(len(c["adjacent"]) for c in cats) == sum(len(o["adjacent"]) for o in RECS.values())
    for layer in F["chain"]:
        assert layer["n_primary"] == sum(len(c["primary"]) for c in layer["categories"])
    assert sum(layer["n_primary"] for layer in F["chain"]) == DOC["counts"]["records"]


def test_every_business_a_need_names_exists():
    known = {o["id"] for o in op.load()["opportunities"]}
    for n in firm_kinds.load()["needs"]:
        assert set(n.get("opportunities") or []) <= known, n["id"]


def test_demand_breadth_counts_the_kinds_of_firm_on_the_needs_grid():
    spec = firm_kinds.load()
    d = F["demand"]
    assert d["kinds"] == len(spec["kinds"])
    assert sorted(r["id"] for r in d["rows"]) == sorted(RECS)
    for r in d["rows"]:
        needs = {n["id"] for n in spec["needs"] if r["id"] in (n.get("opportunities") or [])}
        kinds = [k["name"] for k in spec["kinds"] if needs & set(k.get("needs") or [])]
        assert [n["id"] for n in r["needs"]] == [n["id"] for n in spec["needs"] if n["id"] in needs]
        assert r["kinds"] == kinds and r["count"] == len(kinds)
        assert r["w"] == 100 * len(kinds) / len(spec["kinds"]) and 0 <= r["w"] <= 100
        assert all(n["href"] == f"/firm/kinds#need-{n['id']}" for n in r["needs"])
    counts = [r["count"] for r in d["rows"]]
    assert counts == sorted(counts, reverse=True)  # widest first; the cards keep the owner's order
    unmet = [n for n in spec["needs"] if not n.get("opportunities")]
    assert [u["id"] for u in d["unmet"]] == [n["id"] for n in unmet]
    for u in d["unmet"]:
        assert u["count"] == sum(1 for k in spec["kinds"] if u["id"] in (k.get("needs") or []))
        assert u["w"] == 100 * u["count"] / d["kinds"]


def test_coverage_is_the_maps_own_count_of_each_business_category():
    rows = F["coverage"]["rows"]
    assert sorted(r["id"] for r in rows) == sorted(RECS)
    for r in rows:
        o = RECS[r["id"]]
        assert r["n"] == o["primary"]["n_entities"] == r["live"] + r["other"]
        assert r["live"] == len(o["examples"]) + o["n_more_examples"] and r["other"] >= 0
        assert 0 <= r["w_live"] and 0 <= r["w_other"] and r["w_live"] + r["w_other"] <= 100 + 1e-9
        assert r["href"] == f"/value-chain#mm-{o['primary']['id']}"
    assert max(r["w_live"] + r["w_other"] for r in rows) == 100  # the fullest category is the full width
    assert [r["n"] for r in rows] == sorted((r["n"] for r in rows), reverse=True)


def test_the_powers_grid_is_each_records_own_list():
    p = F["powers"]
    assert p["cols"] == list(DOC["powers"])
    for r in p["rows"]:
        assert [c for c, on in zip(p["cols"], r["cells"]) if on] == sorted(RECS[r["id"]]["powers"], key=p["cols"].index)
    assert [r["id"] for r in p["rows"]] == list(RECS)
    assert p["totals"] == [sum(1 for r in p["rows"] if r["cells"][i]) for i in range(len(p["cols"]))]
    assert set(p["unused"]) == set(op.POWERS.values()) - set(p["cols"])


def test_the_committed_export_carries_the_figures():
    doc = json.loads((ROOT / "web" / "data" / "opportunities.json").read_text())
    assert doc["figures"]["marks"] and {o["id"] for o in doc["opportunities"]} == {m["id"] for m in doc["figures"]["marks"]}


def test_every_figure_states_its_kind_and_has_a_key_and_a_foot():
    src = FIGS.read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"\s+title=(?:"[^"]+"|\{[^\n]+\})\s+note=\{?("[^"]+"|KIND_LABEL\.[a-z]+|[A-Z_]+)', src)
    assert len(figures) >= 5, figures
    assert len(re.findall(r"<Figure\b", src)) == len(figures)  # none without a stated kind
    blocks = re.split(r"(?=<Figure\b)", src)[1:]
    assert all("keys={" in b and "foot={" in b for b in blocks)
    charts = [b for b in blocks if "KIND_LABEL.model" not in b.split("foot={")[0]]
    assert len(charts) >= 4 and all("table={" in b for b in charts)  # the numbers folded beneath, never hover-only
    assert "judgement" in src and "hatch" in src + PARTS.read_text()


def test_figure_words_type_no_digit_but_a_year_and_no_number_word():
    for f in (FIGS, PARTS):
        src = re.sub(r"//[^\n]*", "", f.read_text())
        words = re.findall(r'(?:title|note|label|aria-label)="([^"]+)"', src) + re.findall(r">([^<>{}=;]+)<", src)
        for w in words:
            w = w.replace("&apos;", "'")
            assert not op.stray_digits(w), (f.name, w)
            assert not NUMBER_WORD.search(w), (f.name, w)


def test_the_page_keeps_every_card_and_claims_no_new_review():
    cards = (WEB / "components" / "Opportunities.tsx").read_text()
    for label in ("The problem", "Sold to", "First step", "Charges for", "Why a lab would not just bundle it", "What it builds up",
                  "Why that profit", "Wrong if", "Already on the map", "Builds on the site's reading", "Needs first"):
        assert f'label="{label}"' in cards, label
    assert "d.opportunities.map" in cards and "A sequence of bets" in cards
    page = (WEB / "app" / "value-chain" / "opportunities" / "page.tsx").read_text()
    assert "reviewed by {d.reviewed_by}" in page and "figures" in page.lower()
    spec = op.load()
    assert str(spec["reviewed"]) == "2026-09-29" and len([o for o in spec["opportunities"] if o.get("published")]) == 20
