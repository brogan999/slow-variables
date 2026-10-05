from ai_tracker import futures
from ai_tracker import market_map as mm
from ai_tracker import opportunities as op
from ai_tracker.outlook import load as load_outlook

RENT = {"rent_kind": "scarcity", "appropriability": "tight", "complementary_assets": "specialised",
        "asset_owner": "innovator", "durability": "long"}


def _rec(**kw):
    base = {"id": "a", "name": "A business", "published": True, "primary": "cat_a", "adjacent": ["cat_b"],
            "bottleneck": "Something is scarce", "wedge": "Sell one thing", "durable_asset": "A record rivals lack",
            "falsifier": "The scarce thing stops being scarce", "rent": dict(RENT), "rent_reason": "Hard to copy",
            "builds_on": ["pos:p1"], "powers": ["switching_costs"]}
    return {**base, **kw}


MAP = {"categories": [{"id": "cat_a"}, {"id": "cat_b"}]}
OUTLOOK = {"positions": [{"id": "p1", "title": "A reading", "layer": "l1"}], "claims": [{"id": "c1", "text": "A claim"}]}


# value-chain units cited by the records that land with #125 to #127; delete this set once they are on main
PENDING = {"vc_evals", "vc_post_training", "vc_agent_infra", "vc_human_data", "vc_routing_gateways",
           "vc_deployment_services", "vc_vertical_ai", "vc_ai_rollups", "vc_open_weight_labs"}


def test_the_real_records_have_only_known_categories_rubric_words_and_powers():
    errs = op.problems(op.load(), mm.load(), load_outlook(), futures.rubric())
    assert [e for e in errs if not any(e.endswith(f"unknown position {p}") for p in PENDING)] == []


def test_the_committed_export_holds_exactly_the_published_records_in_order():
    import json
    from pathlib import Path

    doc = json.loads((Path(__file__).resolve().parents[1] / "web" / "data" / "opportunities.json").read_text())
    want = [o["id"] for o in op.load()["opportunities"] if o.get("published")]
    assert [o["id"] for o in doc["opportunities"]] == want


def test_a_broken_record_names_each_problem():
    spec = {"opportunities": [
        _rec(),
        _rec(id="a"),
        _rec(id="b", primary="nowhere", adjacent=["cat_a", "cat_a"], builds_on=["pos:ghost", "claim:ghost", "web:x"],
             powers=["luck"], rent={**RENT, "durability": "forever"}, see_also="missing", falsifier="",
             bottleneck="Costs fall by 40% a year"),
        _rec(id="c", adjacent=["cat_a"], builds_on=[]),
        _rec(id="d", published=False),
        _rec(id="e", see_also="d"),
    ], "sequence": [{"stage": "someday", "opportunity": "zzz", "gate": "Ten customers, then 12 more"},
                    {"stage": "now", "opportunity": "d", "gate": "x"}, {"stage": "now", "opportunity": "a", "gate": "y"}]}
    errs = op.problems(spec, MAP, OUTLOOK, futures.rubric())
    for want in ["id a is used twice", "unknown category nowhere", "unknown position ghost", "unknown claim ghost",
                 "neither pos: nor claim:", "unknown power luck", "durability=forever", "unknown record missing",
                 "b has no falsifier", "types a figure: 40%", "lists its primary category as adjacent",
                 "c builds on none", "stage someday", "unknown record zzz", "gate types a figure: 12",
                 "e points to unpublished record d", "unpublished record d", "each appear once, in the order"]:
        assert any(want in e for e in errs), want


def test_build_takes_tiers_from_the_rubric_and_companies_from_the_map():
    doc_map = {"layers": [{"categories": [
        {"id": "cat_a", "number": "1.1", "name": "Cat A", "n_entities": 2, "entities": [
            {"name": "Verified Co", "ownership": None}, {"name": "Sold Co", "ownership": "acquired"}, {"name": "Other Co", "ownership": None}]},
        {"id": "cat_b", "number": "1.2", "name": "Cat B", "n_entities": 0, "entities": []},
        {"id": "cat_c", "number": "1.3", "name": "Cat C", "n_entities": 1, "entities": [{"name": "Gone Co", "ownership": "defunct"}]},
    ]}]}
    free = {**RENT, "appropriability": "weak", "complementary_assets": "generic"}
    held = {**RENT, "rent_kind": "none", "asset_owner": "incumbents", "appropriability": "weak"}
    spec = {"opportunities": [_rec(), _rec(id="b", primary="cat_b", adjacent=[], rent=free, see_also="a"),
                              _rec(id="hidden", published=False), _rec(id="c", primary="cat_c", adjacent=[], rent=held)],
            "sequence": [{"stage": "now", "opportunity": "a", "gate": "One buyer"}, {"stage": "next", "opportunity": "hidden", "gate": "x"}]}
    doc = op.build(spec, doc_map, OUTLOOK, futures.rubric())
    a, b, c = doc["opportunities"]
    assert [o["id"] for o in doc["opportunities"]] == ["a", "b", "c"]  # unpublished records never reach the page
    assert a["rent"]["reads"] == "a fat profit, kept by the maker" and a["rent"]["verdict"] == "A fat profit, kept by the maker"
    assert b["rent"]["reads"] == "competed away to users"
    assert c["rent"]["reads"] == "no lasting profit"  # kept by nobody, which is not the same as competed away
    assert c["none_independent"] and not c["unmapped"]  # a category of closed companies is mapped
    assert a["examples"] == ["Verified Co", "Other Co"]  # acquired companies are not offered as live examples
    assert b["unmapped"] and b["see_also"] == {"id": "a", "name": "A business"}
    assert a["builds_on"][0]["href"] == "/layers/l1#assessment-p1"
    assert [s["opportunity"] for s in doc["sequence"]] == ["a"]
    assert doc["counts"]["records"] == 3 and doc["counts"]["unmapped"] == 1
    assert doc["sequence"][0]["label"] == "Needs"  # the last stage opens nothing
    assert doc["powers"] == {"switching costs": op.POWER_GLOSS["switching costs"]}


def test_every_published_opportunity_says_what_it_needs_first_who_would_buy_it_and_the_next_step():
    import yaml

    from ai_tracker import opportunities as op

    spec = yaml.safe_load(op.SPEC.read_text())
    for o in spec["opportunities"]:
        if o.get("published"):
            for k in ("prerequisites", "acquirers", "next_action"):
                assert (o.get(k) or "").strip(), f"{o['id']}: {k} is not written"
    page = (op.SPEC.parents[1] / "web/src/app/value-chain/opportunities/page.tsx").read_text()
    assert "blank on purpose" not in page
