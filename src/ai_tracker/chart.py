"""Chart geometry for the web: axes, tick labels and positions, computed here so the web only draws.

Every position is a percentage from the plot's top-left corner (x rightward, y downward), so a page hands it
straight to SVG or CSS. Tick labels are written here too: choosing round numbers is arithmetic."""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Any

from .format import _fixed, fmt

MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
PCT = ("pct", "pct_change_yoy", "pct_change_qoq_saar")
# units whose tick labels already say what they are; any other unit is named above the axis
# units where zero is not a magnitude: a calendar year
NO_ZERO = {"year"}
SELF_LABELLED = {"share", "USD", "usd", "ratio", "minutes", *PCT}
# a task horizon reads best on durations people know, not on powers of ten
DURATIONS = [(1 / 600, "0.1 s"), (1 / 60, "1 s"), (1 / 6, "10 s"), (1.0, "1 min"), (10.0, "10 min"), (60.0, "1 h"),
             (480.0, "8 h"), (1440.0, "1 day"), (10080.0, "1 week"), (43200.0, "1 month"), (525600.0, "1 year")]  # fmt: skip


def _step(span: float, n: int = 5) -> float:
    """The smallest 1-2-5 step that cuts the span into at most n intervals."""
    mag = 10 ** math.floor(math.log10(span / n))
    return next(m * mag for m in (1, 2, 5, 10) if m * mag * n >= span * (1 - 1e-9))


def _num(v: float, step: float) -> str:
    places = max(0, -math.floor(math.log10(step) + 1e-9))
    s = f"{float(_fixed(v, places)):,.{places}f}"
    return "0" if float(s.replace(",", "")) == 0 else s


def tick_label(v: float, unit: str | None, step: float, top: float) -> str:
    """One tick's label: `step` sets the decimals and `top` (the largest tick) the scale, so a column reads alike."""
    if unit == "share":
        return f"{_num(v * 100, step * 100)}%"
    if unit in PCT:
        return f"{_num(v, step)}%"
    if unit in ("USD", "usd"):
        if v == 0:
            return "$0"
        d, s = next(
            ((d, s) for d, s in ((1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "k")) if top >= d), (1.0, "")
        )
        return ("-" if v < 0 else "") + f"${_num(abs(v) / d, step / d)}{s}"
    if unit == "ratio":
        return f"{_num(v, step)}×"
    if unit == "year":
        return _num(v, step).replace(",", "")
    if top >= 1e6 and v:  # ten million reads as 10M on an axis
        d, s = (1e9, "B") if top >= 1e9 else (1e6, "M")
        return f"{_num(v / d, step / d)}{s}"
    return _num(v, step)


def axis(
    values: list[float | None], unit: str | None, *, log: bool = False, zero: bool = False
) -> dict[str, Any]:
    """A value axis over the values with round ends and at most six ticks. `zero` keeps zero on it (for
    magnitudes); a log axis on minutes ticks at durations, any other log axis at powers of ten."""
    vs = [v for v in values if v is not None and math.isfinite(v) and (v > 0 or not log)]
    lo, hi = min(vs), max(vs)
    if log:
        if unit == "minutes":
            ladder = list(DURATIONS)
            while ladder[0][0] > lo:  # below a tenth of a second or past a year, powers of ten carry on
                ladder.insert(0, (ladder[0][0] / 10, f"{_num(ladder[0][0] * 6, ladder[0][0] * 6)} s"))
            while ladder[-1][0] < hi:
                ladder.append((ladder[-1][0] * 10, f"{round(ladder[-1][0] * 10 / 525600):,} years"))
            rungs = [m for m, _ in ladder]
            lo_v = max(m for m in rungs if m <= lo)
            hi_v = min(m for m in rungs if m >= hi and m > lo_v)
            marks = [(m, label) for m, label in ladder if lo_v <= m <= hi_v]
        else:  # ends on the nearest 1, 2 or 5; ticks at each of those when the axis spans two decades or less
            rungs = [
                m * 10.0**k
                for k in range(math.floor(math.log10(lo)) - 1, math.ceil(math.log10(hi)) + 2)
                for m in (1, 2, 5)
            ]
            lo_v = max(r for r in rungs if r <= lo * 1.000001)
            hi_v = min(r for r in rungs if r >= hi / 1.000001 and r > lo_v)
            few = math.log10(hi_v / lo_v) <= 2.0001
            marks = [
                (r, tick_label(r, unit, r, r))
                for r in rungs
                if lo_v <= r <= hi_v
                and (few or r in (lo_v, hi_v) or abs(math.log10(r) - round(math.log10(r))) < 1e-9)
            ]
        ax = {"lo": lo_v, "hi": hi_v, "log": True}
        return {**ax, "ticks": [{"y": y(m, ax), "label": s} for m, s in marks], "unit": _unit_label(unit)}
    if zero and unit not in NO_ZERO:
        lo, hi = min(lo, 0.0), max(hi, 0.0)
    if hi == lo:
        pad = 2.0 if unit in NO_ZERO else abs(hi) * 0.1 or 1.0
        lo, hi = lo - pad, hi + pad
    step = max(_step(hi - lo), 1.0 if unit in NO_ZERO else 0.0)
    lo_v, hi_v = math.floor(lo / step + 1e-9) * step, math.ceil(hi / step - 1e-9) * step
    marks_v = [lo_v + i * step for i in range(round((hi_v - lo_v) / step) + 1)]
    top = max(abs(m) for m in marks_v)
    ax = {"lo": lo_v, "hi": hi_v, "log": False}
    ticks = [{"y": y(m, ax), "label": tick_label(m, unit, step, top)} for m in marks_v]
    return {**ax, "ticks": ticks, "unit": _unit_label(unit)}


def _unit_label(unit: str | None) -> str | None:
    return None if not unit or unit in SELF_LABELLED else unit.replace("_", " ")


def y(v: float, ax: dict[str, Any]) -> float:
    """Distance from the top of the plot, in percent. Nothing is pinned: every chart builds its axis from all it
    draws, so a value off the axis is a bug for `tests/test_store.py` to catch, not a dot to hide on the edge."""
    lo, hi = ax["lo"], ax["hi"]
    if ax["log"]:
        v, lo, hi = math.log10(v), math.log10(lo), math.log10(hi)
    return round(100 * (hi - v) / (hi - lo), 2)


def time_axis(dates: list[date]) -> dict[str, Any]:
    """A date axis with a little room at each end, ticked at month starts: the year at January and the month
    otherwise (2025 · Apr · Jul · Oct · 2026). Alternate ticks are `minor`, so a phone can drop their labels."""
    lo, hi = min(dates), max(dates)
    if hi == lo:
        lo, hi = lo - timedelta(days=45), hi + timedelta(days=45)
    pad = timedelta(days=max(1, round((hi - lo).days * 0.03)))
    lo, hi = lo - pad, hi + pad
    months = (hi - lo).days / 30.44
    if months < 2:  # a few weeks: tick every one, two or four weeks, labelled by day
        days = next(n for n in (1, 2, 7, 14, 28) if (hi - lo).days / n <= 6)
        first = lo + timedelta(days=(-lo.toordinal()) % days)
        keep = [first + timedelta(days=days * i) for i in range((hi - first).days // days + 1)]
        return {
            "lo": lo,
            "hi": hi,
            "ticks": _ticks(
                keep, lo, hi, lambda d, f: f"{d.day} {MONTHS[d.month - 1]}" + (f" {d.year}" if f else "")
            ),
        }
    step = next((s for s in (1, 3, 6, 12, 24, 60, 120) if months / s <= 6), 240)
    starts = [
        date(lo.year + (lo.month - 1 + k) // 12, (lo.month - 1 + k) % 12 + 1, 1)
        for k in range(int(months) + 2)
    ]
    keep = [
        d for d in starts
        if lo <= d <= hi and ((d.month - 1) % step == 0 if step < 12 else d.month == 1 and d.year % (step // 12) == 0)
    ]  # fmt: skip
    return {
        "lo": lo,
        "hi": hi,
        "ticks": _ticks(
            keep,
            lo,
            hi,
            lambda d, first: (
                str(d.year) if d.month == 1 else MONTHS[d.month - 1] + (f" {d.year}" if first else "")
            ),
        ),
    }


def _ticks(days: list[date], lo: date, hi: date, label: Any) -> list[dict[str, Any]]:
    """Ticks away from the plot's edges (a label centred there would run off the card). The first says which year;
    on a phone every other label drops, but never the first or a year's."""
    days = [d for d in days if 3 <= x(d, lo, hi) <= 96]
    out, alt = [], False
    for i, d in enumerate(days):
        yearly = i == 0 or (d.month == 1 and d.day == 1)
        alt = False if yearly else not alt
        out.append(
            {"x": x(d, lo, hi), "label": label(d, i == 0), "minor": len(days) > 4 and not yearly and alt}
        )
    return out


def x(d: date, lo: date, hi: date) -> float:
    return round(100 * (d - lo).days / (hi - lo).days, 2)


def change_label(v: float, unit: str | None) -> str:
    """A signed change: shares and percentages move in points, anything else in its own unit."""
    sign = "+" if v > 0 else "−" if v < 0 else "±"
    if unit == "share":
        return f"{sign}{_fixed(abs(v) * 100, 1)} pts"
    if unit in PCT:
        return f"{sign}{_fixed(abs(v), 1)} pts"
    if unit == "ratio":
        return sign + fmt(abs(v))
    return sign + fmt(abs(v), unit)


def spread(ys: list[float], gap: float) -> list[float]:
    """Label places as close to `ys` (sorted, percent of the plot) as they can be while `gap` apart and inside it:
    push down, pull back from the bottom, then keep the top on the plot."""
    out = list(ys)
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1] + gap)
    out[-1] = min(out[-1], 100.0)
    for i in range(len(out) - 2, -1, -1):
        out[i] = min(out[i], out[i + 1] - gap)
    out[0] = max(out[0], 0.0)
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1] + gap)
    return [round(y, 2) for y in out]
