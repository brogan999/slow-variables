from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.fred import Fred, FredOfficial, _url, quarter_end


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


def test_monthly_official_series_land_on_their_own_month_ends_as_tier_4():
    sid = "PAYEMS"  # thousands of jobs, monthly: three months must be three rows, not one quarter's
    body = f"observation_date,{sid}\n2026-06-01,158900\n2026-07-01,159010\n2026-08-01,159075\n".encode()
    item = RawItem(_url(sid), body, 200, datetime(2026, 9, 22, tzinfo=timezone.utc), "h", None)
    rows = FredOfficial().extract([item])
    assert [(r.series_key, r.as_of_date, r.period_start) for r in rows] == [
        ("fred.us.jobs_nonfarm.m", date(2026, 6, 30), date(2026, 6, 1)),
        ("fred.us.jobs_nonfarm.m", date(2026, 7, 31), date(2026, 7, 1)),
        ("fred.us.jobs_nonfarm.m", date(2026, 8, 31), date(2026, 8, 1)),
    ]
    assert rows[-1].value_numeric == 159_075_000 and rows[-1].tier == 4 and rows[-1].source_id == "fred_official"
    assert "cosd=2015-01-01" in _url(sid) and "cosd" not in _url("RPSGENAIUSAGESHAREALL")
    assert _url(sid) in FredOfficial.urls and _url(sid) not in Fred.urls  # each source reads only its own series


def test_a_constant_dollar_series_carries_its_price_base():
    sid = "GDPC1"  # billions of chained 2017 dollars at an annual rate
    item = RawItem(_url(sid), f"observation_date,{sid}\n2026-04-01,24269.613\n".encode(), 200, datetime(2026, 9, 22, tzinfo=timezone.utc), "h", None)
    (row,) = FredOfficial().extract([item])
    assert row.value_numeric == 24_269_613_000_000 and row.note == "In chained 2017 dollars, at an annual rate"
