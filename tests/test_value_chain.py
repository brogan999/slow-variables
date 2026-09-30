from datetime import date

import yaml

from ai_tracker import futures
from ai_tracker import value_chain as vc
from ai_tracker.outlook import load as load_outlook
from ai_tracker.store import Seed


def _ids():
    s = Seed.load()
    inputs = {i["id"] for i in yaml.safe_load(open("seed/tightness.yaml"))["inputs"]}
    return {x.id for x in s.layers}, {x.id for x in s.sublayers}, inputs, {e.id for e in s.entities}


def test_the_seed_resolves():
    layers, subs, inputs, ents = _ids()
    assert vc.units(load_outlook()) and vc.load()["companies"]
    assert vc.problems(vc.load(), load_outlook(), layers, subs, inputs, ents, futures.rubric()) == []


def test_a_broken_seed_names_each_problem():
    layers, subs, inputs, ents = _ids()
    unit = {"id": "u1", "folio": "capability", "layer": "nowhere", "sublayer": "ghost", "direction": "sideways",
            "powers": ["charm"], "bottlenecks": ["unobtanium"], "title": "t", "mechanism": "m", "kill_shot": "k",
            "commoditising": "It costs 40 dollars", "stays_scarce": "s", "converts_if": "c", "sources": ["nope"], "rival": "none_found"}
    company = {"entity": "acme", "role": "king", "units": ["u9"], "concentration": "lumpy", "powers": [{"power": "magic"}],
               "depends_on": ["vibes"], "rent_kind": "rent", "appropriability": "tight", "complementary_assets": "generic",
               "asset_owner": "innovator", "durability": "long", "must_be_true": ["Sales reach 3 trillion"], "would_disprove": ["x"],
               "sources": {"market": ["missing"]}, "market": "m", "customers": "c"}
    spec = {"companies": [company], "sources": [{"id": "s1", "url": "https://example.com"}]}
    errs = vc.problems(spec, {"positions": [unit]}, layers, subs, inputs, ents, futures.rubric())
    for needle in ("not in the value folio", "unknown layer nowhere", "unknown sublayer ghost", "needs a direction",
                   "unknown power charm", "unknown bottleneck unobtanium", "commoditising types 40", "cites unknown source nope",
                   "source s1 has no fetch record", "source s1 names no known filer", "acme is not an entity", "role of club or candidate", "unknown unit u9",
                   "customer concentration", "unknown power magic", "unknown input vibes", "rent_kind is not one of",
                   "types 3", "cites unknown source missing", "does not say who judged it"):
        assert any(needle in e for e in errs), needle


def test_product_and_filing_names_are_not_figures_but_amounts_are():
    assert vc.stray_digits("the 10-K and 20-F name the H100, GB200, HBM3E and HBM4 in the 2030s and mid-2040s") == []
    assert vc.stray_digits("about 40% of sales and 3 customers") == ["40%", "3"]


def test_where_a_profiles_rent_pools_follows_the_rubric():
    r = futures.rubric()
    doc = vc.build(vc.load(), load_outlook(), r, {})
    for c in doc["companies"]:
        answers = {k: c["rent"][k] for k in vc.RUBRIC}
        assert (c["rent"]["pools"], c["rent"]["tier"]) == (futures.pools(answers, r), futures.tier(answers, r))
        assert c["rent"]["reads"] and "innovator" not in c["rent"]["reads"]
    raw = {u["id"]: u for u in vc.units(load_outlook())}
    assert all(u["rival"] or raw[u["id"]]["rival"] == "none_found" for u in doc["units"])


def test_a_profile_asks_for_review_when_unread_stale_or_older_than_its_filing():
    spec = {"companies": [{"entity": "a"}, {"entity": "b", "reviewed": date(2026, 1, 1)}, {"entity": "c", "reviewed": date(2024, 1, 1)}]}
    out = vc.notes(spec, {"positions": [{"id": "u", "layer": "x", "rival": "none_found"}]}, {"b": date(2026, 2, 25)}, date(2026, 9, 28))
    assert any("a has not been reviewed" in n for n in out)
    assert any("b predates its annual filing" in n for n in out)
    assert any("c was last reviewed" in n for n in out)
    assert any("unit u has no named rival" in n for n in out)


def test_a_review_names_both_who_and_when_and_a_reviewed_disclosure_does_not_promise_a_review():
    # the page keys "reviewed" on reviewed_by and notes() on the date, so the two must travel together
    layers, subs, inputs, ents = _ids()
    base = {k: v for k, v in vc.load()["companies"][0].items()}
    who_only = {**base, "entity": base["entity"], "reviewed": None}
    when_only = {**base, "reviewed_by": None}
    promise = {**base, "disclosure": "This site's builder works with Anthropic; Alex Brogan reviews this profile before it is relied on."}
    for c, needle in ((who_only, "names who reviewed it but not when"), (when_only, "dates a review but not who made it"),
                      (promise, "disclosure still promises a review")):
        errs = vc.problems({**vc.load(), "companies": [c]}, load_outlook(), layers, subs, inputs, ents, futures.rubric())
        assert any(needle in e for e in errs), needle
