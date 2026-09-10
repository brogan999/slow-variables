import json
from datetime import datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.openrouter import OpenRouter

BODY = json.dumps(
    {
        "data": [
            {"id": "openai/gpt-5.4", "pricing": {"prompt": "0.0000025", "completion": "0.000015"}},
            {"id": "openai/gpt-5.4:batch", "pricing": {"prompt": "0.00000125", "completion": "0.0000075"}},
            {"id": "nex-agi/nex-n2.5-mini:free", "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "deepseek/deepseek-v4-pro", "pricing": {"prompt": "0.0000003", "completion": "0.0000012"}},
        ]
    }
).encode()


def _rows(tmp_path, ledger_rows=()):
    p = tmp_path / "openrouter.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in ledger_rows))
    return OpenRouter(p).extract(
        [RawItem("u", BODY, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), "h", None)]
    )


def test_metr_alias_and_vendor_filter(tmp_path):
    rows = _rows(tmp_path)
    keys = {r.series_key: (r.value_numeric, r.entity_id, r.as_of_date.isoformat()) for r in rows}
    assert keys["openrouter.gpt_5_4.price_prompt_usd_per_mtok.pt"] == (2.5, "openai", "2026-09-10")
    assert keys["openrouter.deepseek_deepseek_v4_pro.price_completion_usd_per_mtok.pt"] == (
        1.2,
        None,
        "2026-09-10",
    )
    assert len(rows) == 4 and all(":" not in r.raw_snippet for r in rows)


def test_unchanged_price_reuses_the_ledger_date(tmp_path):
    prior = {
        "series_key": "openrouter.gpt_5_4.price_prompt_usd_per_mtok.pt",
        "as_of_date": "2026-08-01",
        "value_numeric": 2.5,
    }
    rows = _rows(tmp_path, [prior])
    by = {r.series_key: r.as_of_date.isoformat() for r in rows}
    assert by["openrouter.gpt_5_4.price_prompt_usd_per_mtok.pt"] == "2026-08-01"
    assert by["openrouter.gpt_5_4.price_completion_usd_per_mtok.pt"] == "2026-09-10"
