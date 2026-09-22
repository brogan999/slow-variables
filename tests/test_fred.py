from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.fred import Fred, _url, quarter_end


def test_fred_series_land_on_quarter_ends(raw):
    rows = Fred().extract([raw("fred_RPSGENAIASSISTWRKHRSALL.csv", _url("RPSGENAIASSISTWRKHRSALL"))])
    hours = [r for r in rows if r.series_key == "fred.us_workers.hours_assisted_share.q"]
    assert hours[0].as_of_date == date(2024, 9, 30) and hours[0].period_start == date(2024, 7, 1)
    assert (
        abs(hours[0].value_numeric - 0.041) < 1e-9
        and hours[0].tier == 6
        and hours[0].review_status.value == "approved"
    )
    assert quarter_end(date(2025, 12, 15)) == date(2025, 12, 31)


def test_a_series_is_read_by_its_own_url_when_an_earlier_one_failed_to_download():
    sid = "RPSGENAIUSAGESHARELWWORK"  # the second series; the first is missing from this run
    body = f"observation_date,{sid}\n2025-04-01,36.5\n".encode()
    item = RawItem(_url(sid), body, 200, datetime(2026, 9, 22, tzinfo=timezone.utc), "h", None)
    (row,) = Fred().extract([item])
    assert row.series_key == "fred.us_workers.work_use_weekly_share.q" and abs(row.value_numeric - 0.365) < 1e-9
