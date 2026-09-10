"""Runs semantic/metrics.yaml formulas over the `observations` view. A formula with no inputs is skipped, never faked."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

import duckdb
import yaml

from ..schema import Derived

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
