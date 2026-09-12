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
    # one move then a flat tail is no trend, whichever way the move went (flat steps used to count as falling)
    assert direction(list(zip(d, [0.5, 0.5, 0.5, 0.5, 0.6])), rule).value == "unclear"
    assert direction(list(zip(d, [0.6, 0.6, 0.6, 0.6, 0.5])), rule).value == "unclear"


def test_the_surplus_bracket_holds_above_the_ceiling_and_fails_below_the_floor():
    from ai_tracker.thesis import _bracket

    assert _bracket(172, 37, 146) is True
    assert _bracket(30, 37, 146) is False
    assert _bracket(100, 37, 146) is None


def test_a_reading_on_a_band_edge_or_with_a_straddling_interval_reads_emerging():
    from ai_tracker.analysis.bands import flow_status
    from ai_tracker.schema import Band, FlowStatus, Tier

    normal, fast = Band(lo=None, hi=1e9), Band(lo=2e9, hi=None)
    assert flow_status(2.4e9, normal, fast, None, Tier.BENCHMARK) == FlowStatus.faster_than_normal
    assert flow_status(2e9, normal, fast, None, Tier.BENCHMARK) == FlowStatus.emerging  # exactly the edge
    assert flow_status(2.05e9, normal, fast, None, Tier.BENCHMARK) == FlowStatus.emerging  # within 5% of it
    assert flow_status(0.5e9, normal, fast, None, Tier.BENCHMARK) == FlowStatus.consistent_with_normal
    slow, quick = Band(lo=230, hi=None), Band(lo=None, hi=110)
    assert flow_status(67.7, slow, quick, None, Tier.BENCHMARK) == FlowStatus.faster_than_normal
    assert flow_status(67.7, slow, quick, None, Tier.BENCHMARK, 38, 317) == FlowStatus.emerging  # covers both
    assert flow_status(67.7, slow, quick, None, Tier.BENCHMARK, 60, 80) == FlowStatus.faster_than_normal
