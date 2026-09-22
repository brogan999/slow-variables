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
            {"id": "z-ai/glm-5.3", "canonical_slug": "z-ai/glm-5.3-20260816", "created": 1755302400,
             "hugging_face_id": "zai-org/GLM-5.3", "pricing": {"prompt": "0.0000004", "completion": "0.0000016"}},
            {"id": "z-ai/glm-5.3:free", "canonical_slug": "z-ai/glm-5.3-20260816", "created": 1755302400,
             "hugging_face_id": "zai-org/GLM-5.3", "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "openai/gpt-5.4-pro", "canonical_slug": "openai/gpt-5.4-pro-20260801", "created": 1754006400,
             "hugging_face_id": None, "pricing": {"prompt": "0", "completion": "0"}},
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
    assert len([r for r in rows if r.value_numeric]) == 4 and all(":" not in r.raw_snippet for r in rows)


def test_an_open_model_is_named_by_its_repository_under_its_dated_slug(tmp_path):
    rows = [r for r in _rows(tmp_path) if r.series_key.endswith(".hugging_face_id.pt")]
    assert [(r.series_key, r.value_text, r.as_of_date.isoformat()) for r in rows] == [
        ("openrouter.z_ai_glm_5_3_20260816.hugging_face_id.pt", "zai-org/GLM-5.3", "2026-09-10")
    ]  # the key the token rankings use, dated when first seen; its :free variant and a closed model add no row
    prior = {"series_key": "openrouter.z_ai_glm_5_3_20260816.hugging_face_id.pt", "as_of_date": "2026-09-01", "value_numeric": None}
    (again,) = [r for r in _rows(tmp_path, [prior]) if r.series_key.endswith(".hugging_face_id.pt")]
    assert again.as_of_date.isoformat() == "2026-09-01"  # a later night reuses the first sighting, so the row is one row


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
