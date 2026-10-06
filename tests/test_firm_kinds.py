"""What happens to each kind of firm (/firm/kinds): archetypes tied to census industries. The figures are the census
bundle's, summed by the export; everything said about the future is labelled judgement and names what would prove it
wrong."""

import json
import re

from ai_tracker import census, firm_kinds

PARTS = ("passes", "waits_on_check", "held", "outside")
TIERS = ("managers", "professionals", "sales", "support")


def _built():
    return firm_kinds.build(firm_kinds.load(), census.load(), firm_kinds.trades())


def test_every_kind_maps_to_census_industries_and_its_figures_are_the_bundles():
    spec, cspec = firm_kinds.load(), census.load()
    assert firm_kinds.problems(spec, cspec, firm_kinds.trades()) == []
    industries = {r["naics"]: r for r in census.rows(census.bundle(cspec) / "industries.csv")}
    doc = _built()
    assert len(doc["kinds"]) >= 9
    for k in doc["kinds"]:
        assert k["naics"] and set(k["naics"]) <= set(industries), k["id"]
        rows = [industries[n] for n in k["naics"]]
        assert abs(k["payroll"] - sum(float(r["total"]) for r in rows)) < 1
        assert abs(k["passes"] - sum(float(r["passes_usd"]) for r in rows)) < 1
        assert abs(k["agreed3"] - sum(float(r["agreed3_usd"]) for r in rows)) < 1
        assert abs(k["waits_on_check"] - sum(float(r["blocked"]) for r in rows)) < 1
        assert abs(sum(k[p] for p in PARTS) - k["payroll"]) < 1 and all(k[p] >= 0 for p in PARTS)
        assert abs(sum(k[f"share_{p}"] for p in PARTS) - 1) < 1e-9 and 0 <= k["share_agreed3"] <= k["share_passes"]
        assert all(r.startswith(f"census:{cspec['version']}/industries.csv#") for r in k["refs"]) and len(k["refs"]) == len(k["naics"])
        assert not re.search(r"\d", k["name"])


def test_the_bars_and_the_tiers_arrive_laid_out_so_the_web_computes_nothing():
    for k in _built()["kinds"]:
        segs = k["bar"]
        assert [s["part"] for s in segs] == list(PARTS)
        assert segs[0]["x"] == 0 and abs(segs[-1]["x"] + segs[-1]["w"] - 100) < 1e-6
        assert all(abs(a["x"] + a["w"] - b["x"]) < 1e-6 for a, b in zip(segs, segs[1:]))
        tiers = k["tiers"]
        assert [t["id"] for t in tiers] == list(TIERS)
        assert abs(sum(t["share"] for t in tiers) - 1) < 1e-9  # of the kind's office payroll
        assert max(t["w"] for t in tiers) == 100 and all(0 <= t["w"] <= 100 and 0 <= t["share_passes"] <= 1 for t in tiers)


def test_roll_up_counts_come_from_the_trades_list_with_their_records():
    doc = _built()
    by = {k["id"]: k for k in doc["kinds"]}
    trades = {t["key"]: t for t in firm_kinds.trades()["trades"]}
    spec = {k["id"]: k for k in firm_kinds.load()["kinds"]}
    assert any(k["rollups"] for k in doc["kinds"])
    for kid, k in by.items():
        if not spec[kid].get("trade"):
            assert k["rollups"] is None  # no trade on the roll-up list: say nothing, not zero
            continue
        t = trades[spec[kid]["trade"]]
        assert k["rollups"]["buyers"] == t["rollups"]["n"] and k["rollups"]["deals"] == len(t["deals"])
        assert k["rollups"]["obs_ids"] == [d["obs_id"] for d in t["deals"]]


def test_the_export_is_json_and_types_no_figure_in_its_words():
    doc = _built()
    json.dumps(doc)
    for t in firm_kinds.strings(firm_kinds.load()):
        assert not re.search(r"\d", t), t
