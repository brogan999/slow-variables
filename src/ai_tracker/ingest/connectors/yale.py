"""Yale Budget Lab occupational-mix dissimilarity index: the data workbook behind the monthly labour-market update.

The update pages 403 bots and the workbook URL changes with each release, so the source row carries the current
workbook URL and a human moves it forward; the F2 sheet holds the index (percentage points) by months from each
baseline, of which "Baseline Nov 2022 (AI)" is the AI series and "Baseline Jan 2021" the pre-AI comparison.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import duckdb
import yaml

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

BASELINES = {
    "Baseline Nov 2022 (AI)": (date(2022, 11, 1), "occupation_dissimilarity_pp"),
    "Baseline Jan 2021": (date(2021, 1, 1), "occupation_dissimilarity_pp_jan2021"),
}


def _months_after(start: date, n: int) -> date:
    y, m = divmod(start.month - 1 + n, 12)
    return date(start.year + y, m + 1, 1)


class YaleDissimilarity(Connector):
    source_id = "yale_budget_lab_data"
    kind = "csv"
    optional = True  # a stale workbook is a note for the maintainer, not a PARTIAL night
    expect_series = ["yale_budget_lab_data.us_workers.occupation_dissimilarity_pp.m"]

    def __init__(self, path: Path = Path("seed/sources.yaml")) -> None:
        super().__init__()
        rows = (yaml.safe_load(path.read_text()) or {}).get("sources") or []
        self.urls = [r["url"] for r in rows if r.get("id") == self.source_id]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        p = Path(f"/tmp/{item.content_hash[:12]}.xlsx")
        p.write_bytes(item.body)
        con = duckdb.connect()
        con.execute("INSTALL excel; LOAD excel;")
        rows = con.execute(
            f"SELECT * FROM read_xlsx('{p}', sheet='F2', header=false, stop_at_empty=false, all_varchar=true, range='A1:M200')"
        ).fetchall()
        return self._from_rows(item, rows)

    def _from_rows(self, item: RawItem, rows: list[tuple]) -> list[Observation]:
        header = next((r for r in rows if r and r[0] == "Months from baseline"), None)
        expect(set(header or ()), {"Months from baseline", *BASELINES}, "yale F2 sheet")
        cols = {name: header.index(name) for name in BASELINES}
        out = []
        for r in rows[rows.index(header) + 1 :]:
            if not r[0] or not str(r[0]).isdigit():
                continue
            n = int(r[0])
            for name, (start, measure) in BASELINES.items():
                v = r[cols[name]]
                if v in (None, ""):
                    continue
                when = _months_after(start, n)
                out.append(
                    self.obs(
                        item,
                        series_key=f"{self.source_id}.us_workers.{measure}.m",
                        unit="pp",
                        as_of_date=when,
                        published_date=item.retrieved_at.date(),
                        value_numeric=float(v),
                        tier=Tier.PUBLISHED_ANALYSIS,
                        audited_vs_reported=Basis.estimated,
                        extraction_method=Extraction.api,
                        raw_snippet=f"F2 {name} month {n}: {v}",
                    )
                )
        newest = max((o.as_of_date for o in out), default=None)
        # ponytail: the workbook URL is moved by hand each release; this is the nudge, 184 days = the quarterly allowance
        if newest and (item.retrieved_at.date() - newest).days > 184:
            self.errors.append(f"newest month {newest}; move the workbook URL in seed/sources.yaml")
        return out
