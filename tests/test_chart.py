"""The geometry the export writes for every chart: round ticks, labels that say their unit, positions in percent."""

from datetime import date

from ai_tracker.analysis.direction import window
from ai_tracker.chart import axis, change_label, time_axis, x, y
from ai_tracker.schema import Basis, DirectionRule, Tier, stamp


def labels(ax):
    return [t["label"] for t in ax["ticks"]]


def test_a_value_axis_ends_on_round_ticks_and_labels_them_in_the_unit():
    assert labels(axis([0.05, 0.18], "share", zero=True)) == ["0%", "5%", "10%", "15%", "20%"]
    assert labels(axis([2.5e9, 172e9], "USD", zero=True)) == ["$0", "$50B", "$100B", "$150B", "$200B"]
    assert labels(axis([-2.1, 3.4], "pct_change_yoy", zero=True)) == ["-4%", "-2%", "0%", "2%", "4%"]
    assert labels(axis([3e6, 6.1e6], "workers", zero=True)) == ["0", "2M", "4M", "6M", "8M"]
    # a calendar year is not a magnitude: no zero, no thousands comma, whole years
    assert labels(axis([2026, 2028], "year", zero=True)) == ["2026", "2027", "2028"]
    ax = axis([0.605, 0.75], "share")
    assert (ax["ticks"][0]["y"], ax["ticks"][-1]["y"]) == (100.0, 0.0)  # the ends are the axis's own ticks


def test_units_the_ticks_do_not_name_are_printed_above_the_axis():
    assert axis([1, 9], "count")["unit"] == "count"
    assert axis([0.1, 0.9], "share")["unit"] is None


def test_a_task_horizon_ticks_at_durations_people_know():
    ax = axis([0.03, 1045, 2800], "minutes", log=True)
    assert labels(ax) == ["1 s", "10 s", "1 min", "10 min", "1 h", "8 h", "1 day", "1 week"]
    assert y(60, ax) == ax["ticks"][4]["y"]  # an hour sits on the hour line


def test_positions_are_percent_from_the_top_left_and_pin_to_the_edges():
    ax = axis([0, 10], "count", zero=True)
    assert (y(0, ax), y(10, ax), y(5, ax), y(99, ax)) == (100.0, 0.0, 50.0, 0.0)
    assert x(date(2026, 1, 11), date(2026, 1, 1), date(2026, 1, 21)) == 50.0


def test_a_time_axis_ticks_years_or_months_and_the_first_tick_names_its_year():
    long = time_axis([date(2019, 2, 1), date(2026, 8, 1)])
    assert labels(long) == ["2020", "2022", "2024", "2026"]
    short = time_axis([date(2025, 6, 1), date(2026, 8, 1)])
    assert labels(short) == ["Jul 2025", "Oct", "2026", "Apr", "Jul"]
    assert [t["minor"] for t in short["ticks"]] == [
        False,
        True,
        False,
        True,
        False,
    ]  # a phone drops the minor labels
    weeks = time_axis([date(2026, 9, 3), date(2026, 9, 10)])
    assert labels(weeks)[0] == "3 Sep 2026" and len(weeks["ticks"]) >= 2
    one = time_axis([date(2026, 8, 1)])
    assert labels(one) == ["Jul 2026", "Aug", "Sep"]


def test_a_change_moves_in_points_for_shares_and_in_its_unit_otherwise():
    assert change_label(0.021, "share") == "+2.1 pts"
    assert change_label(-0.4, "pct_change_yoy") == "−0.4 pts"
    assert change_label(-1.2e9, "USD") == "−$1.2B"


def test_a_stamp_says_how_firm_a_number_is():
    assert stamp(Tier.BENCHMARK, Basis.reported) == "measured"
    assert stamp(Tier.OFFICIAL_FILING, Basis.company_stated) == "measured"
    assert stamp(Tier.CREDIBLE_REPORTING, Basis.reported) == "reported"
    assert stamp(Tier.OFFICIAL_FILING, Basis.estimated) == "estimate"


def test_the_chart_draws_the_window_the_rule_compares():
    rule = DirectionRule(periods=2, dead_band=0.1, higher_is="concentrating", rationale="test rationale here")
    pts = [(date(2026, m, 1), float(m)) for m in (3, 1, 2, 4)]
    assert window(pts, rule) == [(date(2026, 2, 1), 2.0), (date(2026, 3, 1), 3.0), (date(2026, 4, 1), 4.0)]
