"""The data market (Part 57): what the firms that sell training data show their buyers asking for, read from the
firms' own pages. seed/data_market.yaml holds the vendors and the signals in a model's words; every page behind them
has a fetch record. A signal's count is the vendors listed under it, and vendors with weak growth evidence are counted
apart."""

import copy
import json
from pathlib import Path

from ai_tracker import data_market as dm

ROOT = Path(__file__).resolve().parents[1]
SPEC, FETCHES = dm.load(), dm.fetches()


def test_the_real_file_names_known_vendors_fetched_pages_and_types_no_figure():
    assert dm.problems(SPEC, FETCHES) == []
    assert SPEC["vendors"] and SPEC["signals"]
    assert {v["evidence"] for v in SPEC["vendors"]} == {"evidenced", "weak"}, "thin vendors stay on, marked"


def test_a_broken_file_names_each_problem():
    doc = copy.deepcopy(SPEC)
    v, s = doc["vendors"][0], doc["signals"][0]
    doc["made_by"].pop("reviewed_by")
    doc["vendors"].append(copy.deepcopy(v))
    v["sells"] = "Sells 40 datasets"
    v["evidence"] = "rumour"
    v["pages"].append("https://example.com/never-fetched")
    doc["vendors"][1]["pages"] = ["https://x.com/someone/status/1"]
    s["theme"] = "astrology"
    s["shown_by"].append("nobody-inc")
    s["headline"] = "Prices doubled"
    doc["signals"][1]["evidence"] = []
    errors = "\n".join(dm.problems(doc, FETCHES))
    for needle in (
        "made_by has no reviewed_by",
        f"vendor {v['id']} is given twice",
        f"vendor {v['id']} types a figure",
        f"vendor {v['id']} has evidence rumour",
        "never-fetched has no fetch record",
        "is a social-media link",
        "astrology is not a theme",
        "nobody-inc, which is not a vendor",
        f"signal {s['id']} types a figure",
        f"signal {doc['signals'][1]['id']} cites no fetched page",
    ):
        assert needle in errors, needle


def test_a_page_that_did_not_answer_or_has_no_hash_is_a_problem():
    url = SPEC["vendors"][0]["pages"][0]
    bad = [{**f, "http_status": 403} if f["url"] == url else f for f in FETCHES]
    assert any("did not answer" in e for e in dm.problems(SPEC, bad))
    bare = [{k: v for k, v in f.items() if k != "content_hash"} if f["url"] == url else f for f in FETCHES]
    assert any("has no content hash" in e for e in dm.problems(SPEC, bare))


def test_a_signal_counts_the_vendors_listed_and_weak_ones_apart():
    doc = dm.build(SPEC, FETCHES)
    weak = {v["id"] for v in SPEC["vendors"] if v["evidence"] == "weak"}
    built_by_id = {s["id"]: s for s in doc["signals"]}
    for s in SPEC["signals"]:
        built = built_by_id[s["id"]]
        assert built["evidenced"] == len(set(s["shown_by"]) - weak)
        assert built["weak"] == len(set(s["shown_by"]) & weak)
    by_id = {v["id"]: v for v in doc["vendors"]}
    for s in SPEC["signals"]:
        for vid in s["shown_by"]:
            assert s["id"] in by_id[vid]["signals"]
    assert [s["id"] for s in doc["signals"]] == [
        s["id"] for s in sorted(doc["signals"], key=lambda s: (-s["evidenced"], s["id"]))
    ], "most-shown first"


def test_every_link_in_the_export_carries_the_day_it_was_read():
    doc = dm.build(SPEC, FETCHES)
    for s in doc["signals"]:
        for e in s["evidence"]:
            assert e["url"].startswith("https://") and e["retrieved_at"], s["id"]
    assert doc["made_by"]["reviewed_by"] and "Anthropic" in doc["disclosure"]


def test_the_committed_export_is_the_build_and_check_reads_the_file():
    assert json.loads((ROOT / "web" / "data" / "data_market.json").read_text()) == json.loads(
        json.dumps(dm.build(SPEC, FETCHES, dm.sources()), default=str)
    )
    assert "data_market.problems(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()
    assert 'out / "data_market.json"' in (ROOT / "src" / "ai_tracker" / "store.py").read_text()


def test_nothing_that_scores_or_answers_reads_the_file():
    src = ROOT / "src" / "ai_tracker"
    for p in [*src.glob("query/*.py"), src / "evaluate.py", src / "argument.py", src / "board.py"]:
        assert not p.exists() or "data_market" not in p.read_text(), p.name


def test_no_tracked_file_of_the_section_names_a_home_folder_or_a_social_link():
    for p in (dm.SPEC, dm.FETCHES, ROOT / "scripts" / "data_market_import.py"):
        text = p.read_text()
        for needle in ("~/", "/Users/", "//x.com/", "//twitter.com/"):
            assert needle not in text, f"{p.name}: {needle}"


# Part 57b: the first page

WEB = ROOT / "web" / "src"


def test_the_export_counts_what_the_page_prints_and_sizes_each_bar():
    doc = dm.build(SPEC, FETCHES)
    vendors = SPEC["vendors"]
    assert doc["counts"] == {
        "sellers": sum(v["role"] == "seller" and v["evidence"] == "evidenced" for v in vendors),
        "weak": sum(v["evidence"] == "weak" for v in vendors),
        "builders": sum(v["role"] == "builder" for v in vendors),
        "signals": len(SPEC["signals"]),
        "pages": len({e["url"] for s in SPEC["signals"] for e in s["evidence"]}),
        "prices": len(SPEC["prices"]),
    }
    top = max(s["evidenced"] for s in doc["signals"])
    for s in doc["signals"]:
        assert s["bar"] == round(100 * s["evidenced"] / top), s["id"]
        assert s["theme_name"] == SPEC["themes"][s["theme"]]


def test_the_page_draws_the_export_labels_the_reading_and_computes_nothing():
    page = (WEB / "app" / "data-market" / "page.tsx").read_text()
    assert "dataMarket()" in page and '"use client"' not in page
    assert "d.counts." in page and "d.disclosure" in page and "d.made_by" in page
    assert "A model&apos;s reading of the vendors&apos; own pages" in page
    assert "weak evidence" in page and "<details" in page and "e.retrieved_at" in page
    assert 'rel="nofollow noopener"' in page, "links out to vendors pass no endorsement"
    for banned in (".length", "Math.", ".reduce(", ".filter("):
        assert banned not in page, f"the page computes with {banned}"
    assert "export const dataMarket" in (WEB / "lib" / "data.ts").read_text()


def test_the_page_is_in_the_contents_the_menu_the_sitemap_and_the_search():
    contents = (WEB / "lib" / "contents.ts").read_text()
    nav = (WEB / "lib" / "nav.ts").read_text()
    assert '"/data-market": {' in contents and '"dm-signals"' in contents and '"dm-limits"' in contents
    assert '"/data-market"' in contents.split("export const UNDER")[1].split('"/capture":')[1].split("\n")[0]
    assert '["/data-market", "4"]' in nav and '["/data-market", "The data market"]' in nav
    search = (WEB / "app" / "search.json" / "route.ts").read_text()
    assert "dataMarket().signals" in search and '"/data-market#' in search.replace("`", '"')
    method = (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert 'id="company-claims"' in method and "/data-market" in method


# Part 57c: the vendor board


def test_the_board_groups_vendors_and_marks_a_theme_only_where_a_signal_of_theirs_sits():
    doc = dm.build(SPEC, FETCHES)
    cols = [c["theme"] for c in doc["board"]["columns"]]
    assert cols and set(cols) <= set(SPEC["themes"]), "every column is a theme of the seed"
    assert [g["id"] for g in doc["board"]["groups"]] == ["evidenced", "weak", "builders"]
    theme_of = {s["id"]: s["theme"] for s in SPEC["signals"]}
    seen = []
    for g in doc["board"]["groups"]:
        counts = [len(v["signals"]) for v in g["vendors"]]
        assert counts == sorted(counts, reverse=True), "most signals first within a group"
        for v in g["vendors"]:
            seen.append(v["id"])
            shows = {theme_of[s] for s in v["signals"]}
            assert v["cells"] == [c in shows for c in cols], v["id"]
            assert v["n_signals"] == len(v["signals"]) and v["shown"][0]["headline"]
    assert sorted(seen) == sorted(v["id"] for v in SPEC["vendors"]), "every vendor is on the board once"


def test_a_board_column_that_is_not_a_theme_is_a_problem():
    doc = copy.deepcopy(SPEC)
    doc["board"].append({"theme": "astrology", "label": "Stars"})
    assert any("board column astrology is not a theme" in e for e in dm.problems(doc, FETCHES))


def test_the_board_page_draws_the_export_marks_weak_evidence_and_the_section_has_its_own_menu():
    page = (WEB / "app" / "data-market" / "vendors" / "page.tsx").read_text()
    nav = (WEB / "components" / "DataMarketNav.tsx").read_text()
    assert "dataMarket()" in page and '"use client"' not in page and "<DataMarketNav" in page
    assert "d.board.groups.map" in page and "weak evidence" in page and "A model&apos;s reading" in page
    assert 'rel="nofollow noopener"' in page and "/data-market#" in page.replace("`", '"').replace("${", "")
    for banned in (".length", "Math.", ".reduce(", ".filter("):
        assert banned not in page, f"the page computes with {banned}"
    assert 'href="/data-market"' in nav.replace("{", "").replace("}", "") or '"/data-market"' in nav
    assert '"/data-market/vendors"' in nav and "overflow-x-auto" in nav, (
        "the menu scrolls on a phone, it does not wrap"
    )
    assert "<DataMarketNav" in (WEB / "app" / "data-market" / "page.tsx").read_text()
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert (
        '"/data-market/vendors": {' in contents
        and '"/data-market/vendors"' in contents.split("export const UNDER")[1]
    )
    assert "dataMarket().vendors" in (WEB / "app" / "search.json" / "route.ts").read_text()
    assert '"/data-market/vendors"' in (WEB / "app" / "sitemap.ts").read_text()


# Part 57d: prices and pay, each quoted from its page


def test_every_price_states_its_figures_in_a_snippet_from_a_fetched_page():
    assert SPEC["prices"], "the seed carries prices"
    fetched = {f["url"] for f in FETCHES if f.get("http_status") == 200}
    vendors = {v["id"] for v in SPEC["vendors"]}
    for p in SPEC["prices"]:
        assert p["vendor"] in vendors and p["url"] in fetched, p["id"]
        assert dm.figures(p["amount"]) and set(dm.figures(p["amount"])) <= set(dm.figures(p["snippet"])), p[
            "id"
        ]


def test_a_broken_price_names_each_problem():
    doc = copy.deepcopy(SPEC)
    a, b, c = doc["prices"][0], doc["prices"][1], doc["prices"][2]
    a["amount"] = "$987,654 a year"
    b["what"] = "Pay for 40 experts"
    c["unit"], c["whose"], c["vendor"] = "per fortnight", "rumour", "nobody-inc"
    doc["prices"].append(copy.deepcopy(doc["prices"][3]))
    errors = "\n".join(dm.problems(doc, FETCHES))
    for needle in (
        f"price {a['id']} gives a figure its snippet does not state",
        f"price {b['id']} types a figure in its description",
        f"price {c['id']} has unit per fortnight",
        f"price {c['id']} has source kind rumour",
        f"price {c['id']} names nobody-inc, which is not a vendor",
        f"price {doc['prices'][3]['id']} is given twice",
    ):
        assert needle in errors, needle


def test_the_export_groups_prices_by_unit_and_the_page_quotes_each():
    doc = dm.build(SPEC, FETCHES)
    rows = [r for g in doc["prices"]["groups"] for r in g["rows"]]
    assert len(rows) == len(SPEC["prices"]) == doc["counts"]["prices"]
    for g in doc["prices"]["groups"]:
        assert g["n"] == len(g["rows"]) and g["name"]
        for r in g["rows"]:
            assert r["snippet"] and r["retrieved_at"] and r["name"] and r["whose_name"]
    page = (WEB / "app" / "data-market" / "prices" / "page.tsx").read_text()
    assert "dataMarket()" in page and '"use client"' not in page and "<DataMarketNav" in page
    assert "d.prices.groups.map" in page and "r.snippet" in page and 'rel="nofollow noopener"' in page
    assert "quoted from the page" in page and "a model&apos;s" in page
    for banned in (".length", "Math.", ".reduce(", ".filter("):
        assert banned not in page, f"the page computes with {banned}"
    assert '"/data-market/prices"' in (WEB / "components" / "DataMarketNav.tsx").read_text()
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert (
        '"/data-market/prices": {' in contents
        and '"/data-market/prices"' in contents.split("export const UNDER")[1]
    )
    assert '"/data-market/prices"' in (WEB / "app" / "sitemap.ts").read_text()
    assert 'href="/data-market/prices"' in (WEB / "app" / "data-market" / "page.tsx").read_text()


# Part 57e: every kind of record that could be training data, and who is already there

SOURCES = dm.sources()


def test_every_source_has_a_family_a_level_and_only_fetched_links():
    assert dm.source_problems(SOURCES, FETCHES) == []
    assert len(SOURCES) > 700 and {s["taken"] for s in SOURCES} >= {0, 1, 2, 3}
    fetched = {f["url"] for f in FETCHES if f.get("http_status") == 200}
    for s in SOURCES:
        assert set(s["there"]) <= fetched, s["id"]


def test_a_broken_source_names_each_problem():
    rows = copy.deepcopy(SOURCES)
    rows[0]["name"] = "Top 40 ledgers"
    rows[1]["taken"] = 7
    rows[2]["there"] = ["https://example.com/never-fetched"]
    rows[3]["family"] = ""
    rows.append(copy.deepcopy(rows[4]))
    errors = "\n".join(dm.source_problems(rows, FETCHES))
    for needle in (
        f"source {rows[0]['id']} types a figure",
        f"source {rows[1]['id']} has level 7",
        "never-fetched has no fetch record",
        f"source {rows[3]['id']} has no family",
        f"source {rows[4]['id']} is given twice",
    ):
        assert needle in errors, needle


def test_the_field_lays_out_one_mark_a_source_by_family_and_counts_each_level():
    doc = dm.build(SPEC, FETCHES, SOURCES)["sources"]
    marks = [m for f in doc["families"] for m in f["marks"]]
    assert len(marks) == len(SOURCES) == doc["n"] and len({m["id"] for m in marks}) == len(marks)
    by_id = {s["id"]: s for s in SOURCES}
    for f in doc["families"]:
        assert f["n"] == len(f["marks"]) == len(f["rows"])
        levels = [m["level"] for m in f["marks"]]
        assert levels == sorted(levels, key=lambda v: -1 if v is None else v, reverse=True), (
            "most taken first"
        )
        for r in f["rows"]:
            assert r["level_name"] and (r["there"] or not by_id[r["id"]]["there"])
            assert r["unlinked"] == (by_id[r["id"]]["taken"] in (1, 2, 3) and not by_id[r["id"]]["there"])
    for k in doc["key"]:
        assert k["n"] == sum(m["level"] == k["level"] for m in marks)


def test_the_sources_page_draws_the_field_and_says_what_a_mark_rests_on():
    page = (WEB / "app" / "data-market" / "sources" / "page.tsx").read_text()
    assert "dataMarket()" in page and '"use client"' not in page and "<DataMarketNav" in page
    assert "d.sources.families.map" in page and "d.sources.key.map" in page and "hatch" in page
    assert "A model&apos;s reading of a search" in page and "no link that could be read" in page
    assert 'rel="nofollow noopener"' in page
    for banned in (".length", "Math.", ".reduce(", ".filter("):
        assert banned not in page, f"the page computes with {banned}"
    assert '"/data-market/sources"' in (WEB / "components" / "DataMarketNav.tsx").read_text()
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert '"/data-market/sources": {' in contents and '"dm-field"' in contents
    assert '"/data-market/sources"' in contents.split("export const UNDER")[1]
    assert '"/data-market/sources"' in (WEB / "app" / "sitemap.ts").read_text()
    assert (
        'out / "data_market.json", data_market.build(data_market.load(), data_market.fetches(), data_market.sources())'
        in (ROOT / "src" / "ai_tracker" / "store.py").read_text().replace("\n", "").replace("    ", "")
    )
