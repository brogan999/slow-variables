"""Flow-status evaluation: value + bands -> FlowStatus. Pure but for the two helpers that read a store's evidence;
compound thresholds live in thesis.py."""

from __future__ import annotations

from typing import Any

from ..schema import Band, FlowStatus, Tier, cap_status_by_tier

EDGE = 0.05  # within 5% of the edge that decides the status, the reading is at the edge, not past it


def flow_status(
    value: float | None,
    normal: Band | None,
    fast: Band | None,
    falsifying: Band | None,
    best_tier: Tier = Tier.BENCHMARK,
    low: float | None = None,
    high: float | None = None,
) -> FlowStatus:
    """The band the value sits in, capped by tier. A reading whose interval covers two bands, or that sits on
    the edge between them, reads `emerging`: the data cannot tell the two apart."""
    if value is None or normal is None:
        return FlowStatus.not_yet_measurable
    s = _band(value, normal, fast, falsifying)
    if low is not None and high is not None and _band(low, normal, fast, falsifying) != _band(
        high, normal, fast, falsifying
    ):
        s = FlowStatus.emerging
    elif _on_edge(value, normal, fast, falsifying):
        s = FlowStatus.emerging
    return FlowStatus(cap_status_by_tier(s.value, best_tier))


PRIMARY = {Tier.BENCHMARK, Tier.MODEL_RELEASE, Tier.OFFICIAL_FILING}
HELD = ("interval", "edge", "tier", "single")  # the codes `held_reasons` returns, in the order the checks run


def single_non_primary(store: Any, ind: Any) -> bool:
    """A scored status needs two sources, or one primary (benchmark, model release, official filing)."""
    obs = store.evidence_obs(ind)
    return len({o["source_id"] for o in obs}) < 2 and not ({Tier(o["tier"]) for o in obs} & PRIMARY)


def held_reasons(store: Any, ind: Any, value: float) -> list[str]:
    """Why the evaluator holds at emerging a number its range would score, in the order `flow_status` and `evaluate`
    apply their checks: the interval spans two ranges, else the number is on a line; its best evidence is a company
    describing itself; it rests on a single source that is not a primary one. Empty for a number between the
    ranges: nothing holds it, the range itself does not score it. The figures on /argument and /diffusion print
    these, so they cannot drift from the status `evaluate` proposes (tests/test_held.py)."""
    n, f, x = ind.normal_band, ind.fast_band, ind.falsifying_band
    if _band(value, n, f, x) == FlowStatus.emerging:
        return []
    lo, hi = store.band_interval(ind)
    why = []
    if lo is not None and hi is not None and _band(lo, n, f, x) != _band(hi, n, f, x):
        why.append("interval")
    elif _on_edge(value, n, f, x):
        why.append("edge")
    if store.band_input(ind)[3] == Tier.ACTOR_STATEMENT:
        why.append("tier")
    if single_non_primary(store, ind):
        why.append("single")
    return why


def _band(value: float, normal: Band, fast: Band | None, falsifying: Band | None) -> FlowStatus:
    if (falsifying and falsifying.contains(value)) or (fast and fast.contains(value)):
        return FlowStatus.faster_than_normal
    if normal.contains(value):
        return FlowStatus.consistent_with_normal
    if fast is not None and _far_side(value, normal, fast):
        return FlowStatus.slower_than_normal
    return FlowStatus.emerging  # in the gap between bands


def _on_edge(value: float, normal: Band, fast: Band | None, falsifying: Band | None) -> bool:
    """True when the value sits within EDGE of a bound that separates two different bands."""
    bounds = [b for band in (normal, fast, falsifying) if band for b in (band.lo, band.hi) if b is not None]
    for b in bounds:
        d = max(abs(b) * 1e-6, 1e-12)
        if abs(value - b) <= EDGE * abs(b) and _band(b - d, normal, fast, falsifying) != _band(
            b + d, normal, fast, falsifying
        ):
            return True
    return False


def _far_side(v: float, normal: Band, fast: Band) -> bool:
    fast_above = (fast.lo is not None and normal.hi is not None and fast.lo >= normal.hi) or (
        fast.lo is not None and normal.lo is not None and fast.lo > normal.lo
    )
    if fast_above:
        return normal.lo is not None and v < normal.lo
    return normal.hi is not None and v > normal.hi
