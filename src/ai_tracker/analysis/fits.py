"""Trend fits with confidence intervals, stdlib only. Log-linear (doubling time) and hyperbolic (finite-time blow-up)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from statistics import NormalDist

# t quantiles (two-sided 95%) for small samples; normal beyond 30.
_T95 = {
    1: 12.706,
    2: 4.303,
    3: 3.182,
    4: 2.776,
    5: 2.571,
    6: 2.447,
    7: 2.365,
    8: 2.306,
    9: 2.262,
    10: 2.228,
    12: 2.179,
    15: 2.131,
    20: 2.086,
    25: 2.060,
    30: 2.042,
}


def t95(df: int) -> float:
    if df <= 0:
        return math.inf
    if df in _T95:
        return _T95[df]
    if df > 30:
        return NormalDist().inv_cdf(0.975)
    lo = max(k for k in _T95 if k < df)
    hi = min(k for k in _T95 if k > df)
    return _T95[lo] + (_T95[hi] - _T95[lo]) * (df - lo) / (hi - lo)


@dataclass(frozen=True)
class Fit:
    value: float  # doubling days (log-linear) or blow-up date as decimal year (hyperbolic)
    low: float | None
    high: float | None
    n: int
    r2: float
    aic: float  # on ln(y) residuals so the two forms are comparable


def _ols(xs: list[float], ys: list[float]) -> tuple[float, float, float, float]:
    """Returns slope, intercept, slope standard error, r2."""
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    b = sxy / sxx
    a = my - b * mx
    rss = sum((y - (a + b * x)) ** 2 for x, y in zip(xs, ys))
    tss = sum((y - my) ** 2 for y in ys)
    se = math.sqrt(rss / (n - 2) / sxx) if n > 2 else math.inf
    return b, a, se, (1 - rss / tss if tss else 0.0)


def _aic(resid: list[float], k: int) -> float:
    n = len(resid)
    rss = sum(r * r for r in resid)
    return n * math.log(max(rss, 1e-300) / n) + 2 * k


def loglinear(points: list[tuple[date, float]], since: date | None = None) -> Fit | None:
    pts = sorted((d, y) for d, y in points if y > 0 and (since is None or d >= since))
    if len(pts) < 3:
        return None
    t0 = pts[0][0]
    xs = [float((d - t0).days) for d, _ in pts]
    ys = [math.log(y) for _, y in pts]
    b, a, se, r2 = _ols(xs, ys)
    if b <= 0:
        return None
    dd = math.log(2) / b
    t = t95(len(pts) - 2)
    lo = math.log(2) / (b + t * se)
    hi = math.log(2) / (b - t * se) if b - t * se > 0 else math.inf
    resid = [y - (a + b * x) for x, y in zip(xs, ys)]
    return Fit(dd, lo, hi if math.isfinite(hi) else None, len(pts), r2, _aic(resid, 2))


def hyperbolic(points: list[tuple[date, float]], since: date | None = None) -> Fit | None:
    """y = 1 / (a - b t): the horizon diverges at t* = a / b. Fit OLS on 1/y; report t* as a decimal year."""
    pts = sorted((d, y) for d, y in points if y > 0 and (since is None or d >= since))
    if len(pts) < 3:
        return None
    t0 = pts[0][0]
    xs = [float((d - t0).days) for d, _ in pts]
    inv = [1.0 / y for _, y in pts]
    b_neg, a, se, _ = _ols(xs, inv)  # slope of 1/y on t is -b
    b = -b_neg
    if b <= 0 or a <= 0:
        return None
    t_star = a / b
    resid = []
    for x, (_, y) in zip(xs, pts):
        pred = a - b * x
        resid.append(math.log(y) - math.log(1 / pred) if pred > 0 else 10.0)
    t = t95(len(pts) - 2)
    lo_days = a / (b + t * se)
    hi_days = a / (b - t * se) if b - t * se > 0 else None
    to_year = lambda days: t0.year + ((t0 - date(t0.year, 1, 1)).days + days) / 365.25  # noqa: E731
    ss_tot = sum((v - sum(inv) / len(inv)) ** 2 for v in inv)
    ss_res = sum((v - (a - b * x)) ** 2 for x, v in zip(xs, inv))
    return Fit(
        to_year(t_star),
        to_year(lo_days),
        to_year(hi_days) if hi_days else None,
        len(pts),
        1 - ss_res / ss_tot if ss_tot else 0.0,
        _aic(resid, 2),
    )
