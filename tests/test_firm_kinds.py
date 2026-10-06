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


def test_every_kind_says_what_it_sees_now_what_it_judges_next_and_what_would_prove_it_wrong():
    import yaml

    from ai_tracker.argument import unfetched

    spec = firm_kinds.load()
    sources = {s["id"]: s for s in spec["sources"]}
    needs = {n["id"] for n in spec["needs"]}
    opps = {o["id"] for o in yaml.safe_load((firm_kinds.ROOT / "seed" / "opportunities.yaml").read_text())["opportunities"]}
    assert [s["id"] for s in spec["stages"]] == ["now", "next", "later"]
    assert all(unfetched(s) is None for s in sources.values())  # every link was fetched, and says when
    for k in spec["kinds"]:
        assert k["rung"] in spec["rungs"] and all(k.get(f) for f in ("signs", "now", "next", "later", "wrong")), k["id"]
        assert k["sources"] and set(k["sources"]) <= set(sources), k["id"]  # what it sees now rests on something read
        for stage in ("next", "later"):
            assert len(k["shape"][stage]) == len(TIERS) and set(k["shape"][stage]) <= set(spec["shape_words"]), k["id"]
        assert k["needs"] and set(k["needs"]) <= needs, k["id"]
    used = {n for k in spec["kinds"] for n in k["needs"]}
    for n in spec["needs"]:
        assert n["id"] in used and set(n["opportunities"]) <= opps, n["id"]
    assert {p["id"] for p in spec["anatomy"]["parts"]} == {"top", "check", "base", "rented", "owned"}
    assert "judgement" in spec["anatomy"]["note"] or "model" in spec["anatomy"]["note"]


def test_the_staged_shapes_the_map_and_the_needs_grid_arrive_laid_out():
    doc = _built()
    assert [s["id"] for s in doc["stages"]] == ["now", "next", "later"]
    for k in doc["kinds"]:
        st = k["staged"]
        assert [s["stage"] for s in st] == ["now", "next", "later"] and not st[0]["judged"] and st[1]["judged"] and st[2]["judged"]
        assert [t["w"] for t in st[0]["tiers"]] == [t["w"] for t in k["tiers"]]  # today's shape is the data's
        for s in st:
            assert [t["id"] for t in s["tiers"]] == list(TIERS) and all(0 <= t["w"] <= 100 for t in s["tiers"])
            assert all(t["word"] in doc["shape_words"] for t in s["tiers"]) if s["judged"] else True
        gone = [t for s in st[1:] for t, w in zip(s["tiers"], firm_kinds.load()["kinds"][doc["kinds"].index(k)]["shape"][s["stage"]]) if w == "gone"]
        assert all(t["w"] == 0 for t in gone)
        assert 0 < k["place"]["x"] < 100 and 0 < k["place"]["y"] < 100
    xs = sorted(doc["kinds"], key=lambda k: k["share_checkable"])
    assert xs[0]["place"]["x"] < xs[-1]["place"]["x"]  # further right, more of the office work a check can settle
    assert doc["map"]["x"]["ticks"] and {r["id"] for r in doc["map"]["rungs"]} == set(doc["rungs"])
    grid = doc["needs_grid"]
    assert [r["id"] for r in grid] == [n["id"] for n in doc["needs"]]
    for r in grid:
        assert len(r["cells"]) == len(doc["kinds"]) and any(r["cells"])
    for n in doc["needs"]:  # a need links to the business that would meet it, where one is listed
        assert all(o["href"].startswith("/value-chain/opportunities#") and o["name"] for o in n["opportunities"])


def test_the_page_is_visual_first_and_every_figure_says_what_kind_it_is():
    src = (firm_kinds.ROOT / "web" / "src" / "components" / "FirmKinds.tsx").read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"[^>]*?note=\{?("[^"]+"|KIND_LABEL\.[a-z]+)', src, re.S)
    assert len(figures) >= 6, figures  # five to ten figures on a main page
    assert len(re.findall(r"<Figure\b", src)) == len(figures)  # none without a stated kind
    page = (firm_kinds.ROOT / "web" / "src" / "app" / "firm" / "kinds" / "page.tsx").read_text()
    assert "this site&apos;s judgement" in page and "Reviewed by Alex" not in page  # no review claimed for the owner
