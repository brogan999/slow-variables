import json
from datetime import date, datetime, timezone
from pathlib import Path

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.artificial_analysis import ArtificialAnalysis
from ai_tracker.ingest.connectors.openrouter_rankings import OpenRouterRankings, parse_payload


def item(body: bytes, url: str = "https://x") -> RawItem:
    return RawItem(url, body, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), "h" * 64)


def test_openrouter_rankings_parses_the_dehydrated_payload():
    html = Path("tests/fixtures/openrouter_rankings_min.html").read_text()
    rows = parse_payload(html)
    assert len(rows) == 3 and rows[0]["model_permaslug"].startswith("meta/")
    c = OpenRouterRankings.__new__(OpenRouterRankings)
    c.scrubbed, c.errors = [], []
    obs = OpenRouterRankings.extract(c, [item(html.encode(), "https://openrouter.ai/rankings")])
    assert obs[0].series_key.startswith("openrouter_rankings.meta_muse_spark") and obs[0].value_numeric > 1e9
    assert int(obs[0].tier) == 3 and obs[0].as_of_date == date(2026, 9, 9)


def test_openrouter_rankings_finds_the_model_table_when_another_query_comes_first():
    # Sep 2026: the page began listing an app-rankings query, and one with dated rows but no model, ahead of it
    html = Path("tests/fixtures/openrouter_rankings_min.html").read_text()
    first = html.index('{\\"dehydratedAt\\"')
    apps = (
        '{\\"dehydratedAt\\":1,\\"state\\":{\\"data\\":{\\"day\\":[{\\"app_id\\":3067167,\\"rank\\":3}]}}},'
    )
    dated = '{\\"dehydratedAt\\":1,\\"state\\":{\\"data\\":[{\\"date\\":\\"2026-09-09\\",\\"app_id\\":1}]}},'
    rows = parse_payload(html[:first] + apps + dated + html[first:])
    assert len(rows) == 3 and rows[0]["model_permaslug"].startswith("meta/")
    assert parse_payload(html[:first] + apps + "]}") == []


def test_artificial_analysis_extracts_three_measures_per_model():
    body = json.dumps(
        {
            "status": 200,
            "data": [
                {
                    "id": "x",
                    "name": "o3-mini",
                    "slug": "o3-mini",
                    "release_date": "2025-01-31",
                    "model_creator": {"slug": "openai"},
                    "evaluations": {"artificial_analysis_intelligence_index": 62.9, "gpqa": 0.748},
                    "pricing": {"price_1m_blended_3_to_1": 1.925},
                    "median_output_tokens_per_second": 153.8,
                },
                {
                    "id": "y",
                    "name": "unpriced",
                    "slug": "unpriced",
                    "release_date": "2026-09-03",
                    "model_creator": {"slug": "openai"},
                    "evaluations": {"artificial_analysis_intelligence_index": 70.1},
                    "pricing": {"price_1m_blended_3_to_1": 0},
                    "median_output_tokens_per_second": 0,
                },
            ],
        }
    ).encode()
    c = ArtificialAnalysis.__new__(ArtificialAnalysis)
    c.scrubbed, c.errors, c.latest = [], [], {"aa.o3_mini.intelligence_index.pt": ("2026-01-01", 62.9)}
    obs = ArtificialAnalysis.extract(c, [item(body)])
    keys = {o.series_key: o for o in obs}
    assert set(keys) == {
        "aa.o3_mini.intelligence_index.pt",
        "aa.o3_mini.gpqa.pt",
        "aa.o3_mini.price_blended_usd_per_mtok.pt",
        "aa.o3_mini.output_tokens_per_second.pt",
        "aa.unpriced.intelligence_index.pt",  # a zero price or speed means unpriced, not free
    }
    assert keys["aa.o3_mini.intelligence_index.pt"].as_of_date == date(2025, 1, 31)  # dated by release
    assert keys["aa.o3_mini.gpqa.pt"].as_of_date == date(2025, 1, 31) and keys["aa.o3_mini.gpqa.pt"].value_numeric == 0.748
    assert keys["aa.o3_mini.intelligence_index.pt"].published_date == date(2026, 1, 1)  # unchanged value
    assert (
        int(keys["aa.o3_mini.intelligence_index.pt"].tier) == 1
        and int(keys["aa.o3_mini.price_blended_usd_per_mtok.pt"].tier) == 3
    )


def test_artificial_analysis_gpqa_outside_zero_to_one_is_an_error_and_the_rest_survives():
    m = {"slug": "m", "release_date": "2025-01-31", "model_creator": {"slug": "x"}, "pricing": {"price_1m_blended_3_to_1": 1.0}}
    ev = {"gpqa": 74.8, "artificial_analysis_intelligence_index": 50.0}  # a percent, not a share
    body = json.dumps({"data": [{**m, "evaluations": ev}]}).encode()
    c = ArtificialAnalysis.__new__(ArtificialAnalysis)
    c.scrubbed, c.errors, c.latest = [], [], {}
    keys = {o.series_key for o in ArtificialAnalysis.extract(c, [item(body)])}
    assert keys == {"aa.m.intelligence_index.pt", "aa.m.price_blended_usd_per_mtok.pt"}
    assert c.errors == ["gpqa for m is 74.8, not a share"]


def test_hal_reads_every_reliability_dimension_and_accuracy_per_agent():
    from ai_tracker.ingest.connectors.hal_reliability import HalReliability

    body = Path("tests/fixtures/hal_reliability_min.html").read_bytes()
    rows = HalReliability().extract([item(body, "https://hal.cs.princeton.edu/reliability/")])
    keys = {(r.series_key, str(r.as_of_date), r.value_numeric) for r in rows}
    assert ("hal_reliability.claude_opus_4_5.reliability.pt", "2025-11-24", 0.86) in keys
    assert ("hal_reliability.gpt_5_5.accuracy.pt", "2026-04-23", 0.79) in keys
    assert len(rows) == 12 and all(r.tier == 1 for r in rows)  # five dimensions and accuracy, two agents
    assert not {v for *_, v in keys} & {0.11, 0.12}  # the all-benchmarks view, read by name, not the first one listed
    assert all(r.published_date == r.retrieved_at.date() for r in rows)  # published when fetched, not at release


def test_hal_without_its_chart_data_is_a_layout_change():
    import pytest

    from ai_tracker.ingest.base import LayoutChanged
    from ai_tracker.ingest.connectors.hal_reliability import HalReliability

    with pytest.raises(LayoutChanged):
        HalReliability().extract([item(b"<html>redesigned</html>", "https://hal.cs.princeton.edu/reliability/")])


def test_tau2_bench_reads_pass_1_and_pass_4_per_domain_as_shares():
    from ai_tracker.ingest.connectors.tau2_bench import Tau2Bench

    body = Path("tests/fixtures/tau2_submission_min.json").read_bytes()
    c = Tau2Bench.__new__(Tau2Bench)
    c.scrubbed, c.errors = [], []
    rows = Tau2Bench.extract(c, [item(b"{}"), item(body)])  # the first item is the manifest
    keys = {r.series_key: r for r in rows}
    assert len(rows) == 8 and keys["tau2_bench.claude_opus_4_5.telecom_pass_4.pt"].value_numeric == 0.7807
    assert keys["tau2_bench.claude_opus_4_5.airline_pass_1.pt"].as_of_date == date(2026, 2, 26)
    assert "(Sierra)" in keys["tau2_bench.claude_opus_4_5.retail_pass_4.pt"].raw_snippet


def test_getdeploying_keeps_only_the_on_demand_median():
    from ai_tracker.ingest.connectors.gpu_rents import GpuRents

    body = Path("tests/fixtures/getdeploying_h100_min.csv").read_bytes()
    c = GpuRents.__new__(GpuRents)
    c.scrubbed, c.errors = [], []
    rows = GpuRents.extract(c, [item(body)])
    assert [(r.series_key, str(r.as_of_date), r.value_numeric) for r in rows] == [
        ("getdeploying.nvidia_h100.on_demand_median_usd_per_gpu_hour.w", "2025-09-22", 2.9533)
    ]
