"""Census Business Trends and Outlook Survey, National.xlsx. Official biweekly firm survey: tier 4, reported.

The AI question was re-instrumented on 17 Nov 2025; the two question wordings are two series (v1, v2).
Cycle ids (e.g. 202617) map to reference periods via the 'Collection and Reference Dates' sheet.
"""

from __future__ import annotations

import tempfile
from datetime import date, timedelta
from pathlib import Path

import duckdb

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

URL = "https://www.census.gov/hfp/btos/downloads/National.xlsx"
EXCEL_EPOCH = date(1899, 12, 30)


def _xl(serial: str | float | None) -> date | None:
    try:
        return EXCEL_EPOCH + timedelta(days=int(float(serial)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


class CensusBtos(Connector):
    source_id = "census_btos"
    urls = [URL]
    expect_series = ["census_btos.us.ai_use_share_v2.2w"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            f.write(item.body)
            path = Path(f.name)
        try:
            return self._extract(item, path)
        finally:
            path.unlink(missing_ok=True)

    def _extract(self, item: RawItem, path: Path) -> list[Observation]:
        con = duckdb.connect()
        con.execute("INSTALL excel; LOAD excel;")

        def sheet(name: str) -> tuple[list[str], list[tuple]]:
            cur = con.execute(f"SELECT * FROM read_xlsx('{path}', sheet='{name}', all_varchar=true)")
            return [d[0] for d in cur.description], cur.fetchall()

        dcols, drows = sheet("Collection and Reference Dates")
        expect(set(dcols), {"Smpdt"}, "btos dates sheet")
        ref_end_col = next((c for c in dcols if c.lower().startswith("ref end")), None) or next(
            c for c in dcols if c.lower().startswith("col end")
        )
        ref_start_col = next((c for c in dcols if c.lower().startswith("ref start")), None) or next(
            c for c in dcols if c.lower().startswith("collection start")
        )
        periods = {}
        for r in drows:
            d = dict(zip(dcols, r))
            if d.get("Smpdt"):
                periods[str(d["Smpdt"]).strip()] = (_xl(d.get(ref_start_col)), _xl(d.get(ref_end_col)))

        ecols, erows = sheet("Response Estimates")
        expect(set(ecols), {"Question ID", "Question", "Answer"}, "btos estimates sheet")
        scols, srows = sheet("Response Standard Errors")
        se_by = {(r[0], r[2]): dict(zip(scols, r)) for r in srows}
        cycles = [c for c in ecols if c.isdigit() and len(c) == 6]
        rows: list[Observation] = []
        for r in erows:
            d = dict(zip(ecols, r))
            q = d.get("Question") or ""
            if "Artificial Intelligence" not in q or (d.get("Answer") or "").strip() != "Yes":
                continue
            if q.startswith("During the next six months"):
                measure = "ai_use_next6m_share"
            elif q.startswith("In the last two weeks"):
                measure = "ai_use_share"
            else:
                continue
            version = "v2" if "business functions" in q else "v1"  # 17 Nov 2025 re-instrumentation
            se_row = se_by.get((d["Question ID"], d["Answer ID"]), {})
            for cyc in cycles:
                raw = (d.get(cyc) or "").strip()
                if not raw.endswith("%"):
                    continue
                start, end = periods.get(cyc, (None, None))
                if not end:
                    continue
                v = float(raw.rstrip("%")) / 100
                se_raw = (se_row.get(cyc) or "").strip().rstrip("%")
                se = float(se_raw) / 100 if se_raw and se_raw != "." else None
                rows.append(
                    self.obs(
                        item,
                        series_key=f"census_btos.us.{measure}_{version}.2w",
                        unit="share",
                        as_of_date=end,
                        period_start=start,
                        value_numeric=v,
                        value_low=v - 1.96 * se if se else None,
                        value_high=v + 1.96 * se if se else None,
                        tier=Tier.OFFICIAL_FILING,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"Q{d['Question ID']} '{q[:70]}' Yes, cycle {cyc}: {raw}",
                    )
                )
        return rows
