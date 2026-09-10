from datetime import date

from ai_tracker.ingest.connectors.fred import Fred, quarter_end


def test_fred_series_land_on_quarter_ends(raw):
    rows = Fred().extract([raw("fred_RPSGENAIASSISTWRKHRSALL.csv")])  # first series only
    hours = [r for r in rows if r.series_key == "fred.us_workers.hours_assisted_share.q"]
    assert hours[0].as_of_date == date(2024, 9, 30) and hours[0].period_start == date(2024, 7, 1)
    assert (
        abs(hours[0].value_numeric - 0.041) < 1e-9
        and hours[0].tier == 6
        and hours[0].review_status.value == "approved"
    )
    assert quarter_end(date(2025, 12, 15)) == date(2025, 12, 31)
