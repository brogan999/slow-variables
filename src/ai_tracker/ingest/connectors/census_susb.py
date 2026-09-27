"""Census Statistics of US Businesses (SUSB): firms and employment by industry and enterprise size, US total.

One annual workbook (all states, every NAICS level). The site reads the national rows for four-digit industries only:
total employment, employment in firms under 500 employees, and the number of firms with 20 to 99 employees (the size
a rollup buys). Tier 4, official. Dated at the end of the reference year.
"""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import duckdb

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, series_key

YEAR = 2022
URL = f"https://www2.census.gov/programs-surveys/susb/tables/{YEAR}/us_state_6digitnaics_{YEAR}.xlsx"
SIZES = {  # enterprise size class -> (measure, column read)
    "01: Total": ("employment", "Employment"),
    "08: <500 employees": ("employment_under_500", "Employment"),
    "06: 20-99 employees": ("firms_20_99", "Firms"),
}


class CensusSusb(Connector):
    source_id = "census_susb"
    urls = [URL]
    expect_series = ["census_susb.naics_5242.employment.a"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(item.body)
            path = Path(f.name)
        try:
            con = duckdb.connect()
            con.execute("INSTALL excel; LOAD excel;")
            cur = con.execute(
                f"SELECT * FROM read_xlsx('{path}', range='A3:M800000', header=true, all_varchar=true) WHERE \"State\" = '00'"
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            path.unlink(missing_ok=True)
        return self._from_rows(item, cols, rows)

    def _from_rows(self, item: RawItem, cols: list[str], rows: list[dict]) -> list[Observation]:
        expect(set(cols), {"State", "NAICS", "NAICS Description", "Enterprise Size", "Firms", "Employment"}, "susb workbook")
        out = []
        for r in rows:
            code, size = (r.get("NAICS") or "").strip(), (r.get("Enterprise Size") or "").strip()
            if len(code) != 4 or not code.isdigit() or size not in SIZES:
                continue
            measure, col = SIZES[size]
            v = r.get(col)
            if v in (None, "", "0"):  # zero or withheld for confidentiality
                continue
            out.append(
                self.obs(
                    item,
                    series_key=series_key("census_susb", f"naics_{code}", measure, "a"),
                    unit="count",
                    as_of_date=date(YEAR, 12, 31),
                    value_numeric=float(v),
                    tier=Tier.OFFICIAL_FILING,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.api,
                    raw_snippet=f"{code} {r.get('NAICS Description')}; {size}; {col} {v}",
                )
            )
        return out
