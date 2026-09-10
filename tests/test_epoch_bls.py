from datetime import date

from ai_tracker.ingest.connectors.bls import Bls
from ai_tracker.ingest.connectors.epoch import Epoch
from ai_tracker.schema import Basis, Entity


def test_epoch_extract(raw):
    ents = [
        Entity(id="openai", name="OpenAI", kind="lab"),
        Entity(id="anthropic", name="Anthropic", kind="lab"),
    ]
    rows = Epoch(ents).extract([raw("epoch_ai_companies.zip")])
    keys = {r.series_key for r in rows}
    assert any(k.startswith("epoch.anthropic.round_equity_usd") for k in keys)
    assert any(k.endswith(".revenue_run_rate_usd.pt") for k in keys)
    assert all(r.tier == 5 and r.entity_id in ("openai", "anthropic") for r in rows)
    assert all(r.run_rate_vs_booked == "run_rate" for r in rows if "revenue_run_rate" in r.series_key)
    assert {r.audited_vs_reported for r in rows} <= {Basis.reported, Basis.estimated}
    assert all(r.value_numeric and r.value_numeric > 0 for r in rows)


def test_bls_extract(raw):
    rows = Bls(date(2026, 9, 10)).extract([raw("bls_response.json")])
    by = {(r.series_key, r.as_of_date): r.value_numeric for r in rows}
    assert by[("bls.prs85006091.q", date(2026, 6, 30))] == 2.2
    assert by[("bls.mpu4910012.a", date(2025, 12, 31))] == 108.441
    assert all(r.tier == 4 and r.grade == "A" for r in rows)
