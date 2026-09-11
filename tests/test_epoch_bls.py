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


def test_epoch_compute_spend_one_series_per_category_and_excluded_rows_skipped():
    import csv
    import hashlib
    import io
    import zipfile
    from datetime import datetime, timezone
    from pathlib import Path

    from ai_tracker.ingest.base import RawItem

    src = zipfile.ZipFile(Path(__file__).parent / "fixtures" / "epoch_ai_companies.zip")
    header = next(csv.reader(io.StringIO(src.read("ai_companies_compute_spend.csv").decode("utf-8-sig"))))
    rows = [
        {
            "Company": "OpenAI",
            "Period type": "Year",
            "Date": "2024-12-31",
            "Confidence": "Likely",
            "Inference compute spend": "1800000000",
        },
        {
            "Company": "OpenAI",
            "Period type": "Year",
            "Date": "2024-12-31",
            "Confidence": "Likely",
            "R&D compute spend": "4000000000",
        },
        {
            "Company": "OpenAI",
            "Period type": "Year",
            "Date": "2025-12-31",
            "Confidence": "Likely",
            "Total compute spend": "16000000000",
            "Exclude from graph view": "True",
        },
    ]
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=header)
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in header})
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n in src.namelist():
            z.writestr(n, out.getvalue() if n == "ai_companies_compute_spend.csv" else src.read(n))
    body = buf.getvalue()
    item = RawItem(
        "https://epoch.ai/data/ai_companies.zip",
        body,
        200,
        datetime(2026, 9, 11, tzinfo=timezone.utc),
        hashlib.sha256(body).hexdigest(),
        None,
    )
    got = {
        (r.series_key, r.as_of_date.isoformat()): r.value_numeric
        for r in Epoch([Entity(id="openai", name="OpenAI", kind="lab")]).extract([item])
    }
    assert got[("epoch.openai.inference_compute_usd.fy", "2024-12-31")] == 1.8e9
    assert got[("epoch.openai.rd_compute_usd.fy", "2024-12-31")] == 4.0e9  # the same year, a separate series
    assert not any(
        "compute_spend" in k or k[1] == "2025-12-31" and "compute" in k[0] for k in got
    )  # excluded row skipped
