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


def test_artificial_analysis_extracts_three_measures_per_model():
    body = json.dumps(
        {
            "status": 200,
            "data": [
                {
                    "id": "x",
                    "name": "o3-mini",
                    "slug": "o3-mini",
                    "model_creator": {"slug": "openai"},
                    "evaluations": {"artificial_analysis_intelligence_index": 62.9},
                    "pricing": {"price_1m_blended_3_to_1": 1.925},
                    "median_output_tokens_per_second": 153.8,
                }
            ],
        }
    ).encode()
    c = ArtificialAnalysis.__new__(ArtificialAnalysis)
    c.scrubbed, c.errors, c.latest = [], [], {"aa.o3_mini.intelligence_index.pt": ("2026-01-01", 62.9)}
    obs = ArtificialAnalysis.extract(c, [item(body)])
    keys = {o.series_key: o for o in obs}
    assert set(keys) == {
        "aa.o3_mini.intelligence_index.pt",
        "aa.o3_mini.price_blended_usd_per_mtok.pt",
        "aa.o3_mini.output_tokens_per_second.pt",
    }
    assert keys["aa.o3_mini.intelligence_index.pt"].as_of_date == date(
        2026, 1, 1
    )  # unchanged value keeps its as_of
    assert (
        int(keys["aa.o3_mini.intelligence_index.pt"].tier) == 1
        and int(keys["aa.o3_mini.price_blended_usd_per_mtok.pt"].tier) == 3
    )
