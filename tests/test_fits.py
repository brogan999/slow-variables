import math
from datetime import date, timedelta

from ai_tracker.analysis.fits import annual_rate, hyperbolic, loglinear


def test_loglinear_recovers_doubling_time():
    pts = [(date(2024, 1, 1) + timedelta(days=30 * i), 10 * 2 ** (30 * i / 120)) for i in range(12)]
    f = loglinear(pts)
    assert f and abs(f.value - 120) < 1e-6 and f.low < 120 < (f.high or math.inf) and f.r2 > 0.999


def test_loglinear_since_filters_and_needs_three_points():
    pts = [(date(2023, 1, 1), 1.0), (date(2024, 1, 1), 2.0), (date(2025, 1, 1), 4.0), (date(2026, 1, 1), 8.0)]
    assert loglinear(pts, since=date(2025, 6, 1)) is None
    f = loglinear(pts)
    assert f and abs(f.value - 365.25) < 1


def test_hyperbolic_finds_blow_up_and_aic_prefers_true_form():
    t0 = date(2024, 1, 1)
    hyper = [
        (t0 + timedelta(days=30 * i), 1 / (1000 - 30 * i) * 1000) for i in range(20)
    ]  # blows up at day 1000
    h, lg = hyperbolic(hyper), loglinear(hyper)
    assert h and abs(h.value - (2024 + 1000 / 365.25)) < 0.02 and lg
    assert h.aic < lg.aic


def test_annual_rate_is_signed_and_keeps_a_falling_trend():
    halving = [(date(2020, 1, 1) + timedelta(days=round(365.25 * i)), 100 * 0.5**i) for i in range(5)]
    f = annual_rate(halving)
    assert f and abs(f.value + 0.5) < 1e-3 and f.low <= f.value <= f.high
    assert loglinear(halving) is None  # a doubling time cannot describe it
    doubling = [(d, 1 / y) for d, y in halving]
    assert abs(annual_rate(doubling).value - 1.0) < 5e-3
    assert annual_rate(halving[:2]) is None
