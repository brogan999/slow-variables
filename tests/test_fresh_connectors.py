import io
import json
import zipfile
from datetime import date, datetime, timezone

import pytest

from ai_tracker.ingest.base import LayoutChanged, RawItem
from ai_tracker.ingest.connectors.cait import Cait
from ai_tracker.ingest.connectors.canaries import MEMBER, Canaries
from ai_tracker.ingest.connectors.ramp import Ramp


def _item(body: bytes, url: str = "https://ex.test") -> RawItem:
    return RawItem(url, body, 200, datetime(2026, 9, 11, tzinfo=timezone.utc), "h", None)


def _esc(key: str, rows: list[dict]) -> str:
    return f'\\"{key}\\":' + json.dumps(rows).replace('"', '\\"')


def test_ramp_reads_the_page_data_as_shares_dated_to_month_end():
    page = "self.__next_f.push([1,\"{" + ",".join(
        [
            _esc("adoptionOverall", [{"date_month": "2026-08-01", "adoption_rate_pct": 56.13, "mom_change_pp": 0.42}]),
            _esc("adoptionVendor", [{"date_month": "2026-07-01", "vendor": "Anthropic", "adoption_rate_pct": 43.45}, {"date_month": "2026-07-01", "vendor": "Cohere", "adoption_rate_pct": 1.0}]),
            _esc("spendPerEmployee", [{"date_month": "2026-08-01", "median_pepm": 12.5, "raw_weighted_pepm": "$undefined"}]),
        ]
    ) + "}\"])"
    rows = {r.series_key: r for r in Ramp().extract([_item(page.encode())])}
    a = rows["ramp.us_businesses.paid_ai_adoption_share.m"]
    assert a.value_numeric == 0.5613 and a.as_of_date == date(2026, 8, 31)
    assert rows["ramp.anthropic.business_paid_share.m"].entity_id == "anthropic"
    assert rows["ramp.us_businesses.ai_spend_per_employee_median_usd.m"].value_numeric == 12.5
    assert not any("cohere" in k for k in rows)  # vendors outside the map are not guessed at
    with pytest.raises(LayoutChanged):
        Ramp().extract([_item(b"<html>redesigned</html>")])


def test_canaries_reads_quintile_yoy_changes_with_the_vintage_as_published_date():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(MEMBER, "observation_date,Quintile 1 (least exposed),Quintile 2,Quintile 3,Quintile 4,Quintile 5 (most exposed),vintage\n2026-07-01,0.01128,0.004638,0.02245,0.007554,0.0009634,2026-08-12\n")
    rows = {r.series_key: r for r in Canaries().extract([_item(buf.getvalue())])}
    q5 = rows["canaries.us_exposure_q5.employment_yoy.m"]
    assert q5.value_numeric == 0.0009634 and q5.as_of_date == date(2026, 7, 31) and q5.published_date == date(2026, 8, 12)
    assert len(rows) == 5


def test_cait_keeps_top_quartile_counts_under_both_measures_and_skips_suppressed_cells():
    serial = str((date(2026, 7, 1) - date(1899, 12, 30)).days)
    cols = ["measure", "year", "month", "q_grp", "claims", "claims_share"]
    rows = [
        ("Eloundou", "2026", serial, "Top 25%", "54473", "0.3"),
        ("Anthropic", "2026", serial, "Top 25%", "72913", "0.4"),
        ("Eloundou", "2026", serial, "Bottom 25%", "20000", "0.1"),
        ("Eloundou", "2026", str(int(serial) - 30), "Top 25%", None, None),
    ]
    out = {r.series_key: r for r in Cait()._from_rows(_item(b""), cols, rows)}
    assert out["cait.ca_top_quartile_potential.claims.m"].value_numeric == 54473 and len(out) == 2
    assert out["cait.ca_top_quartile_observed.claims.m"].as_of_date == date(2026, 7, 31)
    with pytest.raises(LayoutChanged):
        Cait()._from_rows(_item(b""), ["measure", "month"], [])
