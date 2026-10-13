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
        json.dumps(dm.build(SPEC, FETCHES, dm.sources(), dm.dossiers()), default=str)
    )
    assert "data_market.problems(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()
    assert 'out / "data_market.json"' in (ROOT / "src" / "ai_tracker" / "store.py").read_text()


def test_nothing_that_scores_reads_the_file_and_ask_reads_only_quoted_passages():
    src = ROOT / "src" / "ai_tracker"
    for p in [src / "evaluate.py", src / "argument.py", src / "board.py", src / "query" / "server.py"]:
        assert not p.exists() or "data_market" not in p.read_text(), p.name
    ask = (src / "query" / "ask.py").read_text()
    assert "data_market.create_tables(" in ask and "data_market.quoted(" in ask
    for reading in ("data_market.load(", "data_market.build(", "data_market.sources(", '"signals"', "sells"):
        assert reading not in ask.split("data_market.create_tables(")[1][:400], reading


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
        'out / "data_market.json", data_market.build(data_market.load(), data_market.fetches(), data_market.sources(), data_market.dossiers())'
        in (ROOT / "src" / "ai_tracker" / "store.py").read_text().replace("\n", "").replace("    ", "")
    )


# Part 57f: the dossiers, every figure stated on the page its sentence cites

DOSSIERS = dm.dossiers()


def test_every_dossier_passes_the_figure_rule_and_cites_only_fetched_pages():
    assert len(DOSSIERS) >= 35
    assert dm.dossier_problems(DOSSIERS, FETCHES) == []
    for d in DOSSIERS:
        assert d["text"].count("**A model's judgement, not a reading:**") == 1, d["id"]
        for banned in ("Alex", "~/", "/Users/", "Notes for", "//x.com/", "//twitter.com/"):
            assert banned not in d["text"], f"{d['id']}: {banned}"


def test_a_number_must_be_stated_in_a_snippet_of_a_source_its_sentence_cites():
    d = copy.deepcopy(DOSSIERS[0])
    key = d["sources"][0]["key"]
    d["text"] += f"\n\nThe agency counted 98,765 files [{key}]. A further 43,210 went missing."
    d["text"] += "\n\nAn illustration, not a real file: a shop sells 77,777 jackets."
    d["text"] += "\n\nIt reported nothing more [no-such-source]."
    errors = "\n".join(dm.dossier_problems([d], FETCHES))
    assert f"dossier {d['id']}: 98765 is not stated by a source its sentence cites" in errors
    assert f"dossier {d['id']}: 43210 is not stated by a source its sentence cites" in errors
    assert "77777" not in errors, "a labelled invented example is exempt"
    q = copy.deepcopy(DOSSIERS[0])
    q["text"] += (
        f'\n\nIts terms say the customer "keeps every right to all of its own records for ever" [{key}].'
    )
    assert "a quotation is not recorded as read on a source its sentence cites" in "\n".join(
        dm.dossier_problems([q], FETCHES)
    )
    assert f"dossier {d['id']} cites no-such-source, which is not in its sources" in errors
    e = copy.deepcopy(DOSSIERS[0])
    e["text"] = e["text"].replace("**A model's judgement, not a reading:**", "**Verdict:**")
    e["sources"][0]["url"] = "https://example.com/never-fetched"
    errors = "\n".join(dm.dossier_problems([e], FETCHES))
    assert "has no labelled judgement" in errors and "never-fetched has no fetch record" in errors


def test_the_dossier_export_lays_out_blocks_and_numbers_sources_in_order_of_first_use():
    docs = dm.dossier_docs(DOSSIERS, FETCHES)
    assert [d["id"] for d in docs] == [d["id"] for d in sorted(DOSSIERS, key=lambda d: d["n"])]
    for d in docs:
        kinds = {b["kind"] for b in d["blocks"]}
        assert {"h2", "p", "judgement"} <= kinds, d["id"]
        judged = [b for b in d["blocks"] if b["kind"] == "judgement"]
        assert judged[0]["text"].strip() and "Anthropic" in judged[0]["by"], (
            f"{d['id']}: the judgement is drawn, with who made it"
        )
        used = [k for b in d["blocks"] for k in b.get("keys", [])]
        order = list(dict.fromkeys(used))
        assert [s["key"] for s in d["sources"] if s["n"]] == order, d["id"]
        for s in d["sources"]:
            assert s["retrieved_at"] and s["url"].startswith("http")
    committed = json.loads((ROOT / "web" / "data" / "data_market_dossiers.json").read_text())
    assert committed == json.loads(json.dumps(docs, default=str))
    assert 'out / "data_market_dossiers.json"' in (ROOT / "src" / "ai_tracker" / "store.py").read_text()
    assert "data_market.dossier_problems(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()


def test_the_dossier_pages_draw_the_export_label_the_judgement_and_are_listed():
    page = (WEB / "app" / "data-market" / "dossiers" / "[id]" / "page.tsx").read_text()
    index = (WEB / "app" / "data-market" / "dossiers" / "page.tsx").read_text()
    assert "generateStaticParams" in page and "dataMarketDossiers()" in page and '"use client"' not in page
    assert "A model&apos;s judgement, not a reading" in page and "Claude, a model made by Anthropic" in page
    assert 'rel="nofollow noopener"' in page and "s.retrieved_at" in page
    assert "dataMarketDossiers()" in index and "<DataMarketNav" in index
    assert '"/data-market/dossiers"' in (WEB / "components" / "DataMarketNav.tsx").read_text()
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert '"/data-market/dossiers": {' in contents and '"/data-market/dossiers/"' in contents
    assert "dataMarketDossiers()" in (WEB / "app" / "sitemap.ts").read_text()
    assert "dataMarketDossiers()" in (WEB / "app" / "search.json" / "route.ts").read_text()


# Part 57h: the owner's private page, built locally and never deployed


def _private(tmp_path):
    folder = tmp_path / "private"
    (folder / "dossiers").mkdir(parents=True)
    (folder / "vendors").mkdir()
    (folder / "playbook-private.md").write_text(
        "# Playbook\n\n## 1. What changed\n\nContext.\n\n## 2. Stream A: bring companies to the buyers\n\n"
        "**Who pays:** ZEBRA-BUYER.\n\n| Buyer | Terms |\n|---|---|\n| One | Two |\n\n"
        "## 10. Questions only a buyer can answer\n\n1. To five record buyers: price?\n2. To two vendors: margin?\n"
    )
    (folder / "questions.json").write_text(
        json.dumps([{"n": 1, "status": "asked", "asked_on": "2026-10-14", "answer": "QUOLL-ANSWER"}])
    )
    first = sorted(DOSSIERS, key=lambda d: d["n"])[0]
    (folder / "dossiers" / f"D{first['n']:02d}.md").write_text("# Private\n\nWOMBAT-ROUTE to the records.\n")
    (folder / "vendors" / f"{SPEC['vendors'][0]['id']}.md").write_text("# Notes\n\nNUMBAT-CONTACT.\n")
    return folder


def test_the_private_page_opens_on_the_streams_tracks_the_questions_and_joins_private_notes(tmp_path):
    import subprocess
    import sys

    out = tmp_path / "playbook.html"
    script = ROOT / "scripts" / "data_market_private.py"
    done = subprocess.run(
        [sys.executable, str(script), str(_private(tmp_path)), str(out)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert done.returncode == 0, done.stderr
    html = out.read_text()
    assert "Private · local file · never deployed" in html and '<meta name="robots" content="noindex' in html
    assert html.index("Stream A: bring companies to the buyers") < html.index("What changed"), (
        "the streams come first"
    )
    assert "ZEBRA-BUYER" in html and "<table" in html
    assert "QUOLL-ANSWER" in html and "not asked yet" in html, "one question answered, one waiting"
    assert "WOMBAT-ROUTE" in html and "NUMBAT-CONTACT" in html
    assert dm.build(SPEC, FETCHES)["signals"][0]["headline"] in html, "the market view sits underneath"


def test_the_private_page_cannot_be_written_into_the_repository_and_names_no_private_path(tmp_path):
    import subprocess
    import sys

    script = ROOT / "scripts" / "data_market_private.py"
    inside = ROOT / "web" / "public" / "playbook.html"
    done = subprocess.run(
        [sys.executable, str(script), str(_private(tmp_path)), str(inside)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert done.returncode != 0 and not inside.exists()
    assert "outside the repository" in done.stderr + done.stdout
    text = script.read_text()
    for banned in ("~/", "/Users/", "docs/private"):
        assert banned not in text, banned


# Part 57i: how it was made, who pays whom, and a mark that leads to its dossier


def test_a_source_examined_in_a_dossier_links_to_it_and_only_to_a_real_one():
    ids = {d["id"] for d in DOSSIERS}
    linked = [s for s in SOURCES if s.get("dossier")]
    assert len(linked) >= 30 and {s["dossier"] for s in linked} <= ids
    bad = copy.deepcopy(SOURCES)
    bad[0]["dossier"] = "no-such-dossier"
    assert any(
        "names dossier no-such-dossier, which does not exist" in e
        for e in dm.source_problems(bad, FETCHES, ids)
    )
    doc = dm.build(SPEC, FETCHES, SOURCES, DOSSIERS)["sources"]
    rows = {r["id"]: r for f in doc["families"] for r in f["rows"]}
    marks = {m["id"]: m for f in doc["families"] for m in f["marks"]}
    for s in linked:
        assert (
            rows[s["id"]]["dossier"]["href"] == f"/data-market/dossiers/{s['dossier']}"
            and rows[s["id"]]["dossier"]["title"]
        )
        assert marks[s["id"]]["dossier"] is True
    assert doc["examined"] == len(linked)
    page = (WEB / "app" / "data-market" / "sources" / "page.tsx").read_text()
    assert "r.dossier" in page and "m.dossier" in page and "d.sources.examined" in page


def test_the_method_counts_are_in_the_seed_and_each_review_says_what_it_changed():
    m = SPEC["method"]
    assert [s["id"] for s in m["narrowing"]] == ["candidates", "kinds", "dossiers"]
    doc = dm.build(SPEC, FETCHES, SOURCES, DOSSIERS)["method"]
    assert doc["narrowing"][2]["n"] == len(DOSSIERS), "the last step is counted, not typed"
    assert doc["narrowing"][0]["n"] > doc["narrowing"][1]["n"] > doc["narrowing"][2]["n"]
    for r in doc["reviews"]:
        assert r["what"] and r["checked"] > 0 and 0 <= r["changed"] <= r["checked"], r["id"]
    for text in (
        [s["says"] for s in m["narrowing"]]
        + [r["what"] for r in m["reviews"]]
        + m["left_out"]
        + m["found_wrong"]
    ):
        assert not dm._figure(text), text
    broken = copy.deepcopy(SPEC)
    broken["method"]["reviews"][0]["changed"] = broken["method"]["reviews"][0]["checked"] + 1
    assert any("changed more than it checked" in e for e in dm.problems(broken, FETCHES))


def test_who_pays_whom_counts_the_published_figures_on_each_side():
    doc = dm.build(SPEC, FETCHES, SOURCES, DOSSIERS)
    flow = doc["flow"]
    assert [s["id"] for s in flow] == ["people", "companies", "builders"]
    units = {g["unit"]: g["n"] for g in doc["prices"]["groups"]}
    assert flow[0]["n"] == sum(units.get(u, 0) for u in ("per hour", "salary", "per task"))
    assert flow[1]["n"] == units.get("per company", 0)
    for s in flow:
        assert s["from"] and s["to"] and s["says"]


def test_the_method_page_and_the_landing_draw_them():
    page = (WEB / "app" / "data-market" / "method" / "page.tsx").read_text()
    assert "dataMarket()" in page and '"use client"' not in page and "<DataMarketNav" in page
    for needle in (
        "d.method.narrowing.map",
        "d.method.reviews.map",
        "d.method.left_out.map",
        "d.method.found_wrong.map",
    ):
        assert needle in page, needle
    for banned in (".length", "Math.", ".reduce(", ".filter("):
        assert banned not in page, f"the page computes with {banned}"
    landing = (WEB / "app" / "data-market" / "page.tsx").read_text()
    assert "d.flow.map" in landing and 'href="/data-market/method"' in landing
    assert '"/data-market/method"' in (WEB / "components" / "DataMarketNav.tsx").read_text()
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert '"/data-market/method": {' in contents and '"dm-flow"' in contents
    assert '"/data-market/method"' in (WEB / "app" / "sitemap.ts").read_text()


# Part 57j: Ask may cite a price or a dossier passage, and nothing a model wrote


def test_the_query_tables_hold_only_passages_quoted_from_fetched_pages():
    import duckdb

    con = duckdb.connect()
    dm.create_tables(con)
    assert con.execute("SELECT count(*) FROM data_market_prices").fetchone()[0] == len(SPEC["prices"])
    cols = {r[0] for r in con.execute("DESCRIBE data_market_prices").fetchall()}
    assert {
        "id",
        "vendor",
        "amount",
        "unit",
        "passage",
        "url",
        "retrieved_at",
    } <= cols and "sells" not in cols
    n = sum(len(d.get("figures") or []) + len(d.get("quotes") or []) for d in DOSSIERS)
    assert con.execute("SELECT count(*) FROM data_market_passages").fetchone()[0] == n
    everything = " ".join(
        str(v)
        for t in ("data_market_prices", "data_market_passages")
        for row in con.execute(f"SELECT * FROM {t}").fetchall()
        for v in row
    )
    for s in SPEC["signals"][:40]:
        assert s["headline"] not in everything and s["implies"] not in everything, (
            "a model's reading is not in the tables"
        )
    judged = [
        b["text"] for d in dm.dossier_docs(DOSSIERS, FETCHES) for b in d["blocks"] if b["kind"] == "judgement"
    ]
    assert judged and not any(j[:60] in everything for j in judged)


def test_a_citation_to_a_price_or_a_passage_resolves_to_the_quoted_words():
    p = SPEC["prices"][0]
    rec = dm.quoted(f"price.{p['id']}")
    assert rec and p["snippet"] in rec["snippet"] and rec["href"] == "/data-market/prices"
    d = next(d for d in DOSSIERS if d.get("figures"))
    key = d["figures"][0]["key"]
    rec = dm.quoted(f"dossier.{d['id']}.{key}")
    assert rec and d["figures"][0]["snippet"] in rec["snippet"]
    assert rec["href"] == f"/data-market/dossiers/{d['id']}#source-{key}"
    assert dm.quoted("price.no-such") is None and dm.quoted("signal.anything") is None


def test_ask_knows_the_citation_kind_the_tables_and_a_golden_question():
    from ai_tracker.query import ask, citecheck

    assert citecheck.CITE.search("[dm:price.mercor-12]") and "dm" in citecheck.PROSE_KINDS
    assert {"data_market_prices", "data_market_passages"} <= set(ask.DATA_MARKET_TABLES)
    text = (ROOT / "src" / "ai_tracker" / "query" / "ask.py").read_text()
    assert "[dm:<id>]" in text and "data_market_prices (" in text and "a model's reading" in text
    assert int(ask.PROMPT_VERSION) >= 16
    golden = (ROOT / "seed" / "golden.yaml").read_text()
    assert '"dm:*"' in golden
    rec = citecheck.Record("price.x", "dm", [], "", "$28 – $36 per hour • Offers Equity")
    assert citecheck.check("The listing offers $28 to $36 per hour [dm:price.x].", {"dm:price.x": rec}).ok
    assert not citecheck.check("The listing offers $99 per hour [dm:price.x].", {"dm:price.x": rec}).ok
