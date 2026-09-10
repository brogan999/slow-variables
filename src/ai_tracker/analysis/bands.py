"""Flow-status evaluation: value + bands -> FlowStatus. Pure; compound thresholds live in thesis.py."""

from __future__ import annotations

from ..schema import Band, FlowStatus, Tier, cap_status_by_tier


def flow_status(
    value: float | None,
    normal: Band | None,
    fast: Band | None,
    falsifying: Band | None,
    best_tier: Tier = Tier.BENCHMARK,
) -> FlowStatus:
    if value is None or normal is None:
        return FlowStatus.not_yet_measurable
    if (falsifying and falsifying.contains(value)) or (fast and fast.contains(value)):
        s = FlowStatus.faster_than_normal
    elif normal.contains(value):
        s = FlowStatus.consistent_with_normal
    elif fast is not None and _far_side(value, normal, fast):
        s = FlowStatus.slower_than_normal
    else:
        s = FlowStatus.emerging  # in the gap between bands
    return FlowStatus(cap_status_by_tier(s.value, best_tier))


def _far_side(v: float, normal: Band, fast: Band) -> bool:
    fast_above = (fast.lo is not None and normal.hi is not None and fast.lo >= normal.hi) or (
        fast.lo is not None and normal.lo is not None and fast.lo > normal.lo
    )
    if fast_above:
        return normal.lo is not None and v < normal.lo
    return normal.hi is not None and v > normal.hi
