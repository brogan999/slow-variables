"""How a number reads on the site. The web's copy is `web/src/lib/format.ts`; the two must agree, which is
what `tests/test_format.py` checks. Anything that prints a value for a human goes through here."""

from __future__ import annotations


def _sig(v: float) -> str:
    """Significant digits the way the site rounds: $0.0057 must not read $0.01."""
    a = abs(v)
    if a >= 100:
        return f"{v:.0f}"
    if a >= 10:
        return f"{v:.1f}"
    if a >= 0.1 or v == 0:
        return f"{v:.2f}"
    return f"{v:.2g}"


def fmt(v: float | None, unit: str | None = None) -> str:
    if v is None:
        return "—"
    if unit in ("share",):
        return f"{v * 100:.1f}%"
    if unit in ("pct", "pct_change_yoy", "pct_change_qoq_saar"):
        return f"{v:.1f}%"
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
        body = (f"{d:.0f}" if abs(d) >= 100 else f"{d:.1f}") if s else _sig(d)
        return f"${body}{s}"
    if unit == "ratio":
        return f"{_sig(v)}×"
    if unit == "minutes":
        return f"{v / 60:.1f} h" if v >= 60 else f"{_sig(v)} min"
    if unit == "days":
        return f"{v:.0f} days"
    if unit == "count":
        return f"{v:.0f}"
    n = f"{round(v):,}" if abs(v) >= 1e4 else _sig(v)
    return f"{n} {unit.replace('_', ' ')}" if unit else n
