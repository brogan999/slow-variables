"""What happens to each kind of firm (/firm/kinds): archetypes tied to census industries. The figures are the census
bundle's, summed by the export; everything said about the future is labelled judgement and names what would prove it
wrong."""

import json
import re

from ai_tracker import census, firm_kinds

PARTS = ("passes", "waits_on_check", "needs_body", "held", "outside")
PAGE = firm_kinds.ROOT / "web" / "src" / "app" / "firm" / "kinds" / "page.tsx"
TSX = firm_kinds.ROOT / "web" / "src" / "components" / "FirmKinds.tsx"
YEAR = re.compile(r"\b(19|20)\d\d\b")  # only a year may stand as digits in the page's words
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
        assert abs(k["knowledge_payroll"] - sum(float(r["know"]) for r in rows)) < 1 and "office_payroll" not in k


def test_work_that_needs_a_body_is_split_from_held_by_the_bundles_own_task_flags():
    """Each role's task shares (passes, waits on a check, needs a body: census.shape's order) applied to its payroll in
    an industry. The same sum reproduces the bundle's own industry figures, so the split is the bundle's, not an estimate."""
    cspec = census.load()
    d = census.bundle(cspec)
    split = firm_kinds.by_industry(d)
    for r in census.rows(d / "industries.csv"):
        assert abs(split[r["naics"]]["passes"] - float(r["passes_usd"])) < 1, r["naics"]
        assert abs(split[r["naics"]]["waits_on_check"] - float(r["blocked"])) < 1, r["naics"]
    by = {k["id"]: k for k in _built()["kinds"]}
    for k in by.values():
        assert abs(k["needs_body"] - sum(split[n]["needs_body"] for n in k["naics"])) < 1 and k["needs_body"] > 0
    assert by["hospital"]["share_needs_body"] > by["law"]["share_needs_body"]  # clinicians' hands, against lawyers' desks


def test_all_the_models_pass_travels_with_every_passes_and_lies_inside_it():
    for k in _built()["kinds"]:
        assert 0 < k["share_agreed3"] <= k["share_passes"], k["id"]
        assert k["bar"][0]["part"] == "passes" and 0 < k["agreed_w"] <= k["bar"][0]["w"]  # drawn inside the passes segment
        for t in k["tiers"]:
            assert 0 <= t["share_agreed3"] <= t["share_passes"] and 0 <= t["agreed_w"] <= t["pass_w"], (k["id"], t["id"])
    src = TSX.read_text()
    # wherever the component prints a kind's or a layer's "passes" share, the all-agree share is in the same expression
    for line in src.splitlines():
        if "share_passes" in line and "fmt(" in line:
            assert "share_agreed3" in line, line.strip()[:120]


def test_the_bars_and_the_tiers_arrive_laid_out_so_the_web_computes_nothing():
    for k in _built()["kinds"]:
        segs = k["bar"]
        assert [s["part"] for s in segs] == list(PARTS)
        assert segs[0]["x"] == 0 and abs(segs[-1]["x"] + segs[-1]["w"] - 100) < 1e-6
        assert all(abs(a["x"] + a["w"] - b["x"]) < 1e-6 for a, b in zip(segs, segs[1:]))
        tiers = k["tiers"]
        assert [t["id"] for t in tiers] == list(TIERS)
        assert abs(sum(t["share"] for t in tiers) - 1) < 1e-9  # of the kind's knowledge-work payroll
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
        assert not re.search(r"\d", YEAR.sub("", t)), t


def test_the_pages_words_carry_no_number_word_and_no_count_that_goes_stale():
    from .test_outlook import NUMBER_WORD

    contents = (firm_kinds.ROOT / "web" / "src" / "lib" / "contents.ts").read_text()
    entry = contents[contents.index('"/firm/kinds": {') : contents.index('"/outlook": {')]
    stale = re.compile(r"\b(three|twelve)\b", re.I)
    for t in [*firm_kinds.strings(firm_kinds.load()), PAGE.read_text(), TSX.read_text(), entry]:
        for line in t.splitlines():
            assert not NUMBER_WORD.search(line) and not stale.search(line), line.strip()[:120]


def test_the_page_does_not_say_what_the_review_found_false():
    words = " ".join([*firm_kinds.strings(firm_kinds.load()), PAGE.read_text(), TSX.read_text()])
    for false in (
        "office payroll", "office work", "held by who must sign", "waits on a check or a signature", "cannot see",
        "courts keep finding", "took people back", "rewrote their", "Two American states", "since retired",
        "The largest retailer", "largest American freight broker", "The one careful study", "one shape recurs",
        "nearly every kind of firm", "checked every source and attribution", "most of a hospital", "later still",
        "well into the next", "does not expect to need fewer", "several times the usual", "Four needs", "old rules",
        "for a decade", "Reversals are as well recorded", "estate agent", "Leverage",
    ):
        assert false not in words, false
    page = PAGE.read_text()
    for said in ("knowledge work", "Passing says nothing about whether today", "not an independent review", "Drawing rule", "its own view and not a finding"):
        assert said in page or said in TSX.read_text(), said


def test_the_opportunity_paragraph_says_what_the_grid_and_the_list_show():
    import yaml

    doc = _built()
    grid = {r["id"]: r["cells"] for r in doc["needs_grid"]}
    assert all(grid["check"]) and not any(all(c) for i, c in grid.items() if i != "check")  # "only the check is marked for every kind"
    opps = {o["id"]: o for o in yaml.safe_load((firm_kinds.ROOT / "seed" / "opportunities.yaml").read_text())["opportunities"]}
    hard = {i: opps[i]["rent"]["appropriability"] == "tight" for i in ("regulated_assurance", "ai_warranty", "outcome_verification", "agent_audit_trail")}
    assert hard == {"regulated_assurance": True, "ai_warranty": True, "outcome_verification": False, "agent_audit_trail": False}
    by = {k["id"]: set(k["needs"]) for k in doc["kinds"]}
    for kind, need in (("property", "fleet"), ("hospital", "fleet"), ("freight", "identity"), ("insurer", "fallback")):
        assert need not in by[kind], (kind, need)  # no evidence in the trade points to it
    assert {"outcome", "staged"} <= by["law"]


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
        if k["shape"]["later"] != k["shape"]["next"]:  # a drawing that changes with robots must not sit over "nothing changes"
            assert "do not bear" not in k["later"] and "Little changes" not in k["later"], k["id"]
        for stage in ("next", "later"):
            assert len(k["shape"][stage]) == len(TIERS) and set(k["shape"][stage]) <= set(spec["shape_words"]), k["id"]
        assert k["needs"] and set(k["needs"]) <= needs, k["id"]
    by = {k["id"]: set(k["sources"]) for k in spec["kinds"]}
    relied = {"software": {"metr_dev", "metr_uplift_update"}, "insurer": {"nj_a5494", "fl_hb527", "fl_hb527_status"}, "hospital": {"doctronic_me", "doctronic_tnw"},
              "customer_support": {"bry_li_raymond", "tp_oa", "adecco_hub", "cnxc_pulse", "klarna_entrepreneur"}, "retailer": {"vend1", "vend2", "bossa_cnbc", "jwo_mpr"}}
    for kid, ids in relied.items():  # every source a Now paragraph relies on is listed under it
        assert ids <= by[kid], (kid, ids - by[kid])
    cited = set().union(*by.values()) | {x for s in spec["stages"] for x in s.get("sources") or []}
    assert cited == set(sources)  # and nothing is listed that the page does not cite
    assert "OpenAI" in sources["crete_rebrand"]["ties"] and "OpenAI" in sources["crete_reuters"]["ties"]  # the other lab's tie is disclosed too
    assert all("Anthropic" in sources[i]["ties"] for i in ("vend1", "vend2", "anthropic_work"))
    assert "561300" not in next(k for k in spec["kinds"] if k["id"] == "customer_support")["naics"]  # agencies' placed workers are not a support firm's office
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
            if s["judged"]:  # every judged layer carries its word, and today's width to be outlined behind it
                assert all(t["word"] in doc["shape_words"] and t["was"] == n["w"] for t, n in zip(s["tiers"], st[0]["tiers"]))
        assert 0 < k["place"]["x"] < 100 and "y" not in k["place"]  # one row per kind: height says nothing
    # the key shows each word in use at its drawn width, and no kind draws a layer as gone without arguing it
    used = {w for k in firm_kinds.load()["kinds"] for s in k["shape"].values() for w in s}
    assert {d["word"] for d in doc["drawn"]} == used and "gone" not in used
    assert all(d["w"] == 100 * firm_kinds.DRAWN[d["word"]] and d["label"] == doc["shape_words"][d["word"]] for d in doc["drawn"])
    xs = sorted(doc["kinds"], key=lambda k: k["share_checkable"])
    assert xs[0]["place"]["x"] < xs[-1]["place"]["x"]  # further right, more of the knowledge work a check can settle
    bands = doc["map"]["bands"]
    assert doc["map"]["x"]["ticks"] and [b["id"] for b in bands] == list(doc["rungs"]) and all(b["label"] for b in bands)
    assert sorted(i for b in bands for i in b["kinds"]) == sorted(k["id"] for k in doc["kinds"])
    rung = {k["id"]: k["rung"] for k in doc["kinds"]}
    assert all(rung[i] == b["id"] for b in bands for i in b["kinds"])
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
    assert "not an independent review" in page


def test_a_layer_drawn_as_gone_keeps_its_outline():
    spec = firm_kinds.load()
    spec["kinds"][0]["shape"]["later"] = ["gone", "same", "same", "same"]
    k = firm_kinds.build(spec, census.load(), firm_kinds.trades())["kinds"][0]
    t = k["staged"][2]["tiers"][0]
    assert t["w"] == 0 and t["was"] == k["tiers"][0]["w"] > 0 and t["word"] == "gone"
    assert "t.was" in TSX.read_text()  # the component outlines today's width behind every judged layer


def test_hatching_is_kept_for_judgement_and_every_judged_layer_shows_its_word():
    src = TSX.read_text()
    bars = src[src.index("export function KindBars") : src.index("export function KindShapes")]
    shapes = src[src.index("export function KindShapes") : src.index("const JUDGED")]
    assert "hatch" not in bars and "hatch" not in shapes  # data is never hatched, the part outside the census included
    staged = src[src.index("function Staged") : src.index("export function KindPanels")]
    assert "hatch" in staged and "doc.shape_words[t.word]" in staged and "title=" not in staged  # the word is printed, not a hover tip
    assert "doc.drawn.map" in src  # the key that states the drawing rule


def test_the_page_keeps_its_figures_and_adds_pictures_that_say_what_they_are():
    src = TSX.read_text()
    for fig in ("bars", "shapes", "stages", "map", "anatomy", "rollups", "needs"):
        assert f'id="fig-{fig}"' in src, fig
    assert re.search(r'<Figure\s+id="fig-picture"[^>]*?note=\{KIND_LABEL\.illustration\}', src, re.S)
    anatomy = src[src.index("export function Anatomy") : src.index("function Staged")]
    assert anatomy.index("fig-picture") < anatomy.index("fig-anatomy")  # the picture opens the section, the diagram stays
    panels = src[src.index("export function KindPanels") : src.index("export function RollupBars")]
    assert "<Illustration " in panels and "<Staged " in panels and panels.index("<h3") < panels.index("<Illustration ")
    page = PAGE.read_text()
    assert "<em>illustration</em>" in page and "AI image generation" in page  # the page says what the pictures are
    doc = _built()
    assert all(k["illustration"]["alt"] and k["illustration"]["stage"] in ("next", "later") for k in doc["kinds"])
