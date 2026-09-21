"""Tightness: a 0-100 reading of how hard one input to AI is to get, built from a few gauges, with a confidence
beside it. Scoped to the migrating-bottleneck page; it never moves an indicator's status. Pure: no store, no clock.

A gauge turns one metric reading into points on a hand-set scale (piecewise-linear between knots, flat beyond the
ends). An input's tightness is the weighted mean of its available gauges. Confidence is a weighted geometric mean of
three factors (how much of the intended evidence is fed, how fresh it is, how good its sources are), capped at an
editorial ceiling. No usable data means no score: an input is withheld, never shown at fifty.
"""

from __future__ import annotations

import math
from typing import Any


def half_up(x: float) -> int:
    """Round half up, as the page's readers expect; Python's round() sends 52.5 to 52."""
    return math.floor(x + 0.5)


def scale(x: float, knots: list[list[float]], log10: bool = False) -> tuple[float, str | None]:
    """Points for a reading, and "low" or "high" when it sits at or beyond an end of the scale."""
    if not math.isfinite(x) or (log10 and x <= 0):
        raise ValueError(f"no points for {x}")
    f = math.log10 if log10 else float
    x, ks = f(x), [(f(k), p) for k, p in knots]
    if x <= ks[0][0]:
        return ks[0][1], "low"
    if x >= ks[-1][0]:
        return ks[-1][1], "high"
    for (x0, y0), (x1, y1) in zip(ks, ks[1:]):
        if x <= x1:
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0), None
    raise AssertionError("unreachable")


def word(n: int, words: list[list[Any]]) -> str:
    return next(w for floor, w in words if n >= floor)


def score_input(
    inp: dict[str, Any], readings: dict[str, dict[str, Any]], rules: dict[str, Any]
) -> dict[str, Any]:
    """`readings[gauge_id]` is {"x": value, "age": days, "grade": "A".."D"} for each gauge that has a reading."""
    gauges = inp.get("gauges") or []
    out_gauges, avail = [], []
    for g in gauges:
        r = readings.get(g["id"])
        row: dict[str, Any] = {"id": g["id"], "points": None, "pinned": None, "unavailable": None}
        if "unfed" in g:
            row["unavailable"] = "unfed"
        elif r is None:
            row["unavailable"] = "no reading"
        elif r["age"] > g["max_age_days"]:
            row["unavailable"] = "past its age limit"
        else:
            try:
                row["points"], row["pinned"] = scale(r["x"], g["knots"], bool(g.get("log10")))
                avail.append((g, r, row["points"]))
            except ValueError:
                row["unavailable"] = "no reading"
        out_gauges.append(row)

    total_w = sum(g["weight"] for g in gauges) + inp.get("hand_judged_weight", 0.0)
    avail_w = sum(g["weight"] for g, _, _ in avail)
    coverage = avail_w / total_w if total_w > 0 else 0.0
    out: dict[str, Any] = {
        "score": None,
        "word": None,
        "confidence": None,
        "at_ceiling": False,
        "hatched": False,
        "used": len(avail),
        "defined": len(gauges),
        "factors": None,
        "withheld": None,
        "gauges": out_gauges,
    }
    missing = [g["id"] for g in gauges if g.get("required") and g["id"] not in {a["id"] for a, _, _ in avail}]
    if avail_w <= 0:
        out["withheld"] = "nothing"
        return out
    if missing:
        out["withheld"] = "required"
        return out
    if coverage < rules["min_coverage"]:
        out["withheld"] = "coverage"
        return out

    def mean(f: Any) -> float:
        return sum(g["weight"] / avail_w * f(g, r) for g, r, _ in avail)

    factors = {
        "coverage": coverage,
        "freshness": mean(lambda g, r: 0.5 ** (r["age"] / (rules["half_life_ratio"] * g["max_age_days"]))),
        "source": mean(lambda g, r: rules["grade_quality"][r["grade"]]),
    }
    w_sum = sum(rules["weights"].values())
    raw = 100 * math.exp(
        sum(w / w_sum * math.log(max(factors[k], rules["factor_floor"])) for k, w in rules["weights"].items())
    )
    confidence = half_up(min(raw, inp["ceiling"]))
    out["factors"] = {k: round(v, 2) for k, v in factors.items()}
    if confidence < rules["confidence_floor"]:
        out["withheld"] = "confidence"
        return out
    score = half_up(min(100.0, max(0.0, sum(g["weight"] * p for g, _, p in avail) / avail_w)))
    out.update(
        score=score,
        word=word(score, rules["words"]),
        confidence=confidence,
        at_ceiling=raw >= inp["ceiling"],
        hatched=confidence < rules["hatch_under"],
    )
    return out
