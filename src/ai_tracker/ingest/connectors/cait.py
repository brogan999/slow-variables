"""California AI-Unemployment Tracker workbook (California Policy Lab with California EDD): monthly initial UI claims
in the top quartile of AI exposure, under both exposure measures. Counts only: the tracker computes its percentages
downstream, and so does semantic/metrics.yaml. Tier 6 (published tabulation of administrative data), reported.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import duckdb

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect
from .census_btos import _xl
from .ramp import month_end

URL = "https://capolicylab.org/data/cait-monthly-claims.xlsx"
MEASURES = {
    "Eloundou": "potential",
    "Anthropic": "observed",
}  # the tracker's names: potential and observed exposure


class Cait(Connector):
    source_id = "cait"
    urls = [URL]
    expect_series = ["cait.ca_top_quartile_potential.claims.m", "cait.ca_top_quartile_observed.claims.m"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(item.body)
            path = Path(f.name)
        try:
            con = duckdb.connect()
            con.execute("INSTALL excel; LOAD excel;")
            cur = con.execute(f"SELECT * FROM read_xlsx('{path}', sheet='monthly_claims', all_varchar=true)")
            cols = [d[0] for d in cur.description]
            return self._from_rows(item, cols, cur.fetchall())
        finally:
            path.unlink(missing_ok=True)

    def _from_rows(self, item: RawItem, cols: list[str], rows: list[tuple]) -> list[Observation]:
        expect(set(cols), {"measure", "month", "q_grp", "claims"}, "cait monthly_claims sheet")
        out: list[Observation] = []
        for r in rows:
            d = dict(zip(cols, r))
            if (
                d["measure"] not in MEASURES
                or not str(d.get("q_grp") or "").startswith("Top 25%")
                or not d.get("claims")
            ):
                continue  # blank = suppressed by the tracker
            first = _xl(d["month"])
            if not first:
                continue
            out.append(
                self.obs(
                    item,
                    series_key=f"cait.ca_top_quartile_{MEASURES[d['measure']]}.claims.m",
                    unit="claims",
                    as_of_date=month_end(first.isoformat()),
                    published_date=item.retrieved_at.date(),
                    value_numeric=float(d["claims"]),
                    tier=Tier.PUBLISHED_ANALYSIS,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.api,
                    raw_snippet=json.dumps(
                        {k: d[k] for k in ("measure", "month", "q_grp", "claims")}, sort_keys=True
                    ),
                )
            )
        return out
