"""Direction evaluation for capture indicators: trend over N periods with a dead-band."""

from __future__ import annotations

from datetime import date

from ..schema import Direction, DirectionRule, Tier, cap_status_by_tier


def direction(
    points: list[tuple[date, float]], rule: DirectionRule, best_tier: Tier = Tier.OFFICIAL_FILING
) -> Direction:
    pts = sorted(points)[-(rule.periods + 1) :]
    if len(pts) < rule.periods + 1:
        return Direction.not_yet_measurable
    delta = pts[-1][1] - pts[0][1]
    if abs(delta) <= rule.dead_band:
        return Direction.stable
    steps = [b[1] - a[1] for a, b in zip(pts, pts[1:])]
    agree = sum(1 for s in steps if s * delta > 0)  # a flat step agrees with neither a rise nor a fall
    if agree <= len(steps) / 2:  # half the steps agreeing is no trend
        return Direction.unclear
    up = rule.higher_is
    down = "dispersing" if up == "concentrating" else "concentrating"
    return Direction(cap_status_by_tier(up if delta > 0 else down, best_tier))
