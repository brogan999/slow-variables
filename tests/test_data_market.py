"""The data market (Part 55): what the firms that sell training data show their buyers asking for, read from the
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
    for s, built in zip(SPEC["signals"], doc["signals"]):
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
        json.dumps(dm.build(SPEC, FETCHES), default=str)
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
        for needle in ("~/", "/Users/", "x.com/", "twitter.com/"):
            assert needle not in text, f"{p.name}: {needle}"
