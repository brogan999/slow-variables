from datetime import date

import pytest

from ai_tracker.analysis.bands import flow_status
from ai_tracker.analysis.direction import direction
from ai_tracker.schema import Band, DirectionRule, Tier

N, F = Band(lo=213), Band(hi=122)  # doubling-time bands: fast is below normal


@pytest.mark.parametrize(
    "value,expected",
    [
        (300, "consistent_with_normal"),
        (100, "faster_than_normal"),
        (150, "emerging"),
        (None, "not_yet_measurable"),
    ],
)
def test_flow_status(value, expected):
    assert flow_status(value, N, F, None).value == expected


def test_flow_status_far_side_and_tier_cap():
    assert flow_status(1, Band(lo=5, hi=10), Band(lo=20), None).value == "slower_than_normal"
    assert flow_status(100, N, F, None, best_tier=Tier.ACTOR_STATEMENT).value == "emerging"
    assert flow_status(5, Band(lo=1), Band(hi=0.5), Band(hi=0.2)).value == "consistent_with_normal"


def test_direction():
    rule = DirectionRule(dead_band=0.02, higher_is="concentrating", rationale="share")
    d = [date(2025, m, 1) for m in (1, 4, 7, 10)] + [date(2026, 1, 1)]
    assert direction(list(zip(d, [0.5, 0.52, 0.55, 0.58, 0.6])), rule).value == "concentrating"
    assert direction(list(zip(d, [0.6, 0.58, 0.55, 0.52, 0.5])), rule).value == "dispersing"
    assert direction(list(zip(d, [0.5, 0.51, 0.5, 0.51, 0.51])), rule).value == "stable"
    assert direction(list(zip(d, [0.5, 0.7, 0.4, 0.75, 0.55])), rule).value == "unclear"
    assert direction(list(zip(d[:3], [0.5, 0.6, 0.7])), rule).value == "not_yet_measurable"
