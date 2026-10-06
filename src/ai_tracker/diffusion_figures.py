"""The figures on /diffusion, laid out here so the page only draws (Part 45c). Everything is read off the stage's own
indicator cards, the seed's bands and tonight's band inputs: counts list the ids they count, a placed number carries
its observation ids, and the one model is a drawing with labels from the seed and no number of its own."""

from __future__ import annotations

import math
from datetime import date
from statistics import median
from typing import Any

from .analysis.bands import _band
from .schema import CONFIDENCE_RUBRIC

GROUPS = ("fast", "normal", "slow", "unscored", "other")
GROUP = {"faster_than_normal": "fast", "consistent_with_normal": "normal", "slower_than_normal": "slow"}
ZONE = {"consistent_with_normal": "normal", "faster_than_normal": "fast", "emerging": "between", "slower_than_normal": "slow"}
LANE = 18  # pixels a stacked mark takes
GAP = 5.0  # percent of the strip two marks in one lane must be apart
AGES = [(0, "today"), (7, "1 week"), (30, "1 month"), (91, "3 months"), (365, "1 year")]
AGE_ENDS = [(365, "1 year"), (1096, "3 years"), (1826, "5 years"), (3652, "10 years")]
# the lag model's drawing rule: each stage starts a fixed step after the one before and climbs more slowly
MID = (16.0, 36.0, 57.0, 79.0)
SLOPE = (3.2, 4.4, 5.6, 6.8)


def _stack(dots: list[dict[str, Any]]) -> int:
    """Give each mark a `y` so marks closer than GAP sit in separate lanes, stacked up from the strip's foot."""
    last: list[float] = []
    lane: dict[int, int] = {}
    for d in sorted(dots, key=lambda d: (d["x"], d["id"])):
        k = next((i for i, x in enumerate(last) if d["x"] - x >= GAP), len(last))
        if k == len(last):
            last.append(d["x"])
        last[k] = d["x"]
        lane[id(d)] = k
    n = max(len(last), 1)
    for d in dots:
        d["y"] = round(100 - 100 * (lane[id(d)] + 0.5) / n, 2)
    return n * LANE + 6


def _place(value: float, ind: Any, zones: dict[str, tuple[float, float]]) -> tuple[str, float] | None:
    """The zone the band rule reads tonight's number into, and where in it. Between the bands the place is to scale;
    inside a band, which has no far edge, distance is squeezed so every reading fits and their order is kept."""
    n, f = ind.normal_band, ind.fast_band
    above = (f.lo is not None and n.hi is not None and f.lo >= n.hi) or (f.lo is not None and n.lo is not None and f.lo > n.lo)
    near, far, edge = (n.hi, n.lo, f.lo) if above else (n.lo, n.hi, f.hi)
    if near is None or edge is None or near == edge:
        return None
    zone = ZONE[_band(value, n, f, ind.falsifying_band).value]
    x0, w = zones[zone]
    t = (value - near) / (edge - near)  # nought at the normal range's edge, one at the fast range's
    if zone == "between":
        return zone, x0 + w * (0.06 + 0.88 * min(max(t, 0.0), 1.0))
    if zone == "fast":
        e = max(t - 1, 0.0)
        return zone, x0 + w * (0.12 + 0.76 * e / (1 + e))
    d = max(-t, 0.0) if zone == "normal" else abs(value - far) / abs(edge - near)
    return zone, x0 + w - w * (0.12 + 0.76 * d / (1 + d))


def build(store: Any, buckets: list[dict[str, Any]], voters: set[str], today: date) -> dict[str, Any]:
    ind = {i.id: i for i in store.seed.indicators}

    def group(c: dict[str, Any]) -> str:
        return "other" if ind[c["id"]].direction_rule else GROUP.get(c["status"], "unscored")

    def dot(c: dict[str, Any]) -> dict[str, Any]:
        g = group(c)
        return {"id": c["id"], "name": c["name"], "status": c["status"], "group": g, "votes": c["id"] in voters, "href": f"/indicators/{c['id']}"}

    def row(b: dict[str, Any]) -> dict[str, Any]:
        return {"stage": b["id"], "name": b["name"], "order": b["order"]}

    gauges = []
    for b in buckets:
        dots = sorted((dot(c) for c in b["indicators"]), key=lambda d: (GROUPS.index(d["group"]), not d["votes"], d["name"]))
        ids = {g: [d["id"] for d in dots if d["group"] == g] for g in GROUPS}
        gauges.append({**row(b), "status": b["status"], "dots": dots, "ids": ids, "counts": {g: len(v) for g, v in ids.items()},
                       "votes": sum(d["votes"] for d in dots)})  # fmt: skip

    # where tonight's number sits between its own normal and fast ranges
    read = {}
    for b in buckets:
        for c in b["indicators"]:
            i = ind[c["id"]]
            value, as_of, obs, _ = store.band_input(i)
            if i.direction_rule or not (i.normal_band and i.fast_band):
                read[c["id"]] = "read by direction, not by a range" if i.direction_rule else "no fast range is set"
            elif value is None or not obs:
                read[c["id"]] = "no number to place tonight"
            else:
                read[c["id"]] = (value, as_of, obs)
    slow = any(not isinstance(v, str) and ZONE[_band(v[0], ind[k].normal_band, ind[k].fast_band, ind[k].falsifying_band).value] == "slow" for k, v in read.items())
    names = (["slow"] if slow else []) + ["normal", "between", "fast"]
    w = round(100 / len(names), 4)
    zones = [{"id": z, "x": round(k * w, 4), "w": w} for k, z in enumerate(names)]
    spans = {z["id"]: (z["x"], z["w"]) for z in zones}
    bands = []
    for b in buckets:
        dots, left = [], []
        for c in b["indicators"]:
            r = read[c["id"]]
            at = None if isinstance(r, str) else _place(r[0], ind[c["id"]], spans)
            if at is None:
                left.append({"id": c["id"], "name": c["name"], "why": r if isinstance(r, str) else "its ranges do not face each other"})
                continue
            dots.append({**dot(c), "zone": at[0], "x": round(at[1], 2), "value": r[0], "unit": store.band_unit(ind[c["id"]]),
                         "as_of": r[1].isoformat() if r[1] else None, "obs_ids": r[2]})  # fmt: skip
        bands.append({**row(b), "h": _stack(dots), "dots": dots, "left_out": left})

    # how old each stage's newest readings are, on a scale that gives the last weeks as much room as the last years
    ages = [(today - date.fromisoformat(c["latest"]["as_of"][:10])).days for b in buckets for c in b["indicators"] if c["latest"]]
    hi, hi_label = next((e for e in AGE_ENDS if e[0] >= max(ages, default=0)), AGE_ENDS[-1])

    def ax(days: float) -> float:
        return round(100 * math.log1p(min(max(days, 0), hi)) / math.log1p(hi), 2)

    marks = [a for a in AGES if a[0] < hi] + [(hi, hi_label)]
    fresh = []
    for b in buckets:
        dots = []
        for c in b["indicators"]:
            if not c["latest"]:
                continue
            age = max(0, (today - date.fromisoformat(c["latest"]["as_of"][:10])).days)
            dots.append({**dot(c), "as_of": c["latest"]["as_of"], "age_days": age, "x": ax(age), "stale": bool(c["stale_as_of"]),
                         "excused": bool(c["stale_reason"] and not c["stale_as_of"]), "why": c["stale_reason"]})  # fmt: skip
        a = [d["age_days"] for d in dots]
        fresh.append({**row(b), "h": _stack(dots), "dots": dots, "median_days": median(a) if a else None, "median_x": ax(median(a)) if a else None,
                      "newest_days": min(a, default=None), "oldest_days": max(a, default=None), "n_stale": sum(d["stale"] for d in dots),
                      "n_excused": sum(d["excused"] for d in dots)})  # fmt: skip

    # how sure the site says it is of each reading, on its own rubric
    top = CONFIDENCE_RUBRIC[-1]["hi"] + 1
    rubric = [{**z, "x": round(100 * z["lo"] / top, 2), "w": round(100 * (z["hi"] - z["lo"] + 1) / top, 2), "tick": str(z["lo"])} for z in CONFIDENCE_RUBRIC]
    sure = []
    for b in buckets:
        dots = [{**dot(c), "confidence": c["confidence"], "x": round(100 * c["confidence"] / top, 2)} for c in b["indicators"] if c["confidence"] is not None]
        sure.append({**row(b), "h": _stack(dots), "dots": dots})

    # one reading to draw per stage: the one the site is most sure of among those with a line to draw, a reading that
    # counts toward the stage's status where there is one
    headline = []
    for b in buckets:
        drawable = [c for c in b["indicators"] if c["spark"] and group(c) != "other"]
        pool = [c for c in drawable if c["id"] in voters] or drawable
        if pool:
            best = max(pool, key=lambda c: (c["confidence"] or 0, c["n_observations"], c["id"]))
            headline.append({**row(b), "id": best["id"], "counts": best["id"] in voters})

    main = [b for b in buckets if b["id"] != "return_arrow"]
    loop = next((b for b in buckets if b["id"] == "return_arrow"), None)
    curves = []
    for b, mid, s in zip(main, MID, SLOPE):
        pts = [(x, 92 - 84 / (1 + math.exp(-(x - mid) / s))) for x in range(0, 101)]
        curves.append({**row(b), "limit": b["speed_limit"], "stock": b["stock"], "d": "M" + " L".join(f"{x},{y:.2f}" for x, y in pts), "mid": {"x": mid, "y": 50.0}})
    model = {"curves": curves, "lags": [{"x": round((a["mid"]["x"] + b["mid"]["x"]) / 2, 2), "y": 50.0} for a, b in zip(curves, curves[1:])],
             "loop": {**row(loop), "limit": loop["speed_limit"], "stock": loop["stock"]} if loop else None}  # fmt: skip

    return {
        "gauges": {"rows": gauges, "groups": list(GROUPS)},
        "bands": {"rows": bands, "zones": zones},
        "fresh": {"today": today.isoformat(), "rows": fresh, "ticks": [{"x": ax(d), "label": s, "minor": (k % 2 == 1) if d != hi else ax(marks[-2][0]) > 75} for k, (d, s) in enumerate(marks)]},  # a crowded end label gives way on a phone
        "sure": {"rows": sure, "zones": rubric},
        "headline": headline,
        "model": model,
    }
