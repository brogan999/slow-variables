"""Runs semantic/metrics.yaml formulas over the `observations` view. A formula with no inputs is skipped, never faked."""

from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

import duckdb
import yaml

from ..schema import Derived
from . import fits

log = logging.getLogger(__name__)


def run_metrics(
    con: duckdb.DuckDBPyConnection, spec_path: Path = Path("semantic/metrics.yaml")
) -> list[Derived]:
    spec = yaml.safe_load(spec_path.read_text())
    keys = {r[0] for r in con.execute("SELECT DISTINCT series_key FROM observations").fetchall()}
    now = datetime.now(timezone.utc)
    out: list[Derived] = []
    for name, m in spec["metrics"].items():
        missing = [p for p in m["inputs"] if not any(fnmatch(k, p) for k in keys)]
        if missing:
            log.warning("%s skipped: no observations for %s", name, missing)
            continue
        if "python" in m:
            out.extend(_python_metric(con, name, m, now))
            continue
        cur = con.execute(m["sql"])
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            d = dict(zip(cols, row))
            ids = d.pop("obs_ids")
            if d.get("value") is None or not ids:
                continue
            out.append(
                Derived(
                    metric=name,
                    value=float(d.pop("value")),
                    as_of_date=d.pop("as_of_date"),
                    dims={k: str(v) for k, v in d.items()},
                    input_observation_ids=sorted(ids),
                    formula_version=str(m["formula_version"]),
                    computed_at=now,
                )
            )
    return out


def _python_metric(con: duckdb.DuckDBPyConnection, name: str, m: dict, now: datetime) -> list[Derived]:
    """`python: fits.<fn>` over the non-disputed numeric points of the input series; returns one row with a CI."""
    fn = getattr(fits, m["python"].split(".", 1)[1])
    pats = " OR ".join("series_key LIKE ?" for _ in m["inputs"])
    rows = con.execute(
        f"SELECT id, as_of_date, value_numeric FROM observations WHERE ({pats}) AND NOT disputed AND value_numeric > 0",
        [p.replace("*", "%") for p in m["inputs"]],
    ).fetchall()
    if not rows:
        return []
    args = {
        k: (date.fromisoformat(v) if isinstance(v, str) and len(v) == 10 and v[4] == "-" else v)
        for k, v in (m.get("args") or {}).items()
    }
    invert = bool(args.pop("invert", False))  # fit 1/y for series that fall (prices): the doubling time becomes a halving time
    fit = fn([(r[1], 1 / r[2] if invert else r[2]) for r in rows], **args)
    if fit is None:
        return []
    return [
        Derived(
            metric=name,
            value=fit.value,
            value_low=fit.low,
            value_high=fit.high,
            as_of_date=max(r[1] for r in rows),
            dims={"n": str(fit.n), "r2": f"{fit.r2:.3f}", "aic": f"{fit.aic:.1f}"},
            input_observation_ids=sorted(r[0] for r in rows),
            formula_version=str(m["formula_version"]),
            computed_at=now,
        )
    ]
