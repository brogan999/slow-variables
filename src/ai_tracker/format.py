"""How a number reads on the site. The web's copy is `web/src/lib/format.ts`; the two must agree, which is
what `tests/test_format.py` checks. Anything that prints a value for a human goes through here."""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Context, Decimal

_TWO = Context(prec=2, rounding=ROUND_HALF_UP)


def _fixed(v: float, places: int) -> str:
    """JavaScript's toFixed: a tie rounds away from zero (112.5 reads 113), where Python's format rounds it to even."""
    if (
        abs(v) >= 2**53
    ):  # whole numbers at this size, so no tie exists, and quantize would overflow its context
        return f"{v:.{places}f}"
    return str(Decimal(v).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP))


def _sig(v: float) -> str:
    """Significant digits the way the site rounds: $0.0057 must not read $0.01."""
    a = abs(v)
    if a >= 100:
        return _fixed(v, 0)
    if a >= 10:
        return _fixed(v, 1)
    if a >= 0.1 or v == 0:
        return _fixed(v, 2)
    return format(_TWO.create_decimal_from_float(v), "f")  # toPrecision(2): 0.0625 reads 0.063


def fmt(v: float | None, unit: str | None = None) -> str:
    if v is None or not math.isfinite(v):  # the web prints a dash for NaN too
        return "—"
    if unit in ("share",):
        return f"{_fixed(v * 100, 1)}%"
    if unit == "pts_a_year":  # a share's slope per year, in points: never a percentage rise
        return f"{_fixed(v * 100, 1)} pts a year"
    if unit in ("pct", "pct_change_yoy", "pct_change_qoq_saar"):
        return f"{_fixed(v, 1)}%"
    if unit in ("USD", "usd"):
        a = abs(v)
        d, s = (
            (v / 1e12, "T")
            if a >= 1e12
            else (v / 1e9, "B")
            if a >= 1e9
            else (v / 1e6, "M")
            if a >= 1e6
            else (v / 1e3, "k")
            if a >= 1e3
            else (v, "")
        )
        body = (_fixed(d, 0) if abs(d) >= 100 else _fixed(d, 1)) if s else _sig(d)
        return f"${body}{s}"
    if unit == "ratio":
        return f"{_sig(v)}×"
    if unit == "minutes":
        return f"{_fixed(v / 60, 1)} h" if v >= 60 else f"{_sig(v)} min"
    if unit == "days":
        return f"{_fixed(v, 0)} days"
    if unit == "year":  # a whole year reads whole; a fitted one keeps its tenth
        return _fixed(v, 0) if v == int(v) else _fixed(v, 1)
    if unit == "count":
        return f"{int(_fixed(v, 0)):,}" if abs(v) >= 1e4 else _fixed(v, 0)
    n = f"{int(_fixed(v, 0)):,}" if abs(v) >= 1e4 else _sig(v)
    return f"{n} {unit.replace('_', ' ')}" if unit else n
