"""Yale Budget Lab occupational-mix dissimilarity index, from the chart data behind its AI labour-market tracker.

The tracker lists each chart's data in its manifest, as a CSV at a stable path under its data folder.
`total-labor-force-recent` holds the whole-workforce index (percentage points, a 12-month moving average) in long
form by months from each baseline, of which "Baseline Nov 2022 (AI)" is the AI series and "Baseline Jan 2021" the
pre-AI comparison; `new-vs-older-grads-recent` holds the index between recent and older graduates (a 3-month
moving average) by month.
"""

from __future__ import annotations

import csv
import io
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, series_key

DATA = "https://interactives.budgetlab.yale.edu/tools/ai-labor-market-tracker/data/occupational-churn/"
WORKFORCE = DATA + "total-labor-force-recent/data.csv"
GRADUATES = DATA + "new-vs-older-grads-recent/data.csv"
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
    optional = True  # a stale tracker is a note for the maintainer, not a PARTIAL night
    urls = [WORKFORCE, GRADUATES]
    expect_series = [
        "yale_budget_lab_data.us_workers.occupation_dissimilarity_pp.m",
        "yale_budget_lab_data.recent_vs_older_grads.occupation_dissimilarity_pp.m",
    ]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        by_url = {i.url: i for i in items}
        return self._from_csv(by_url[WORKFORCE], by_url[GRADUATES])

    def _from_csv(self, workforce: RawItem, graduates: RawItem) -> list[Observation]:
        out = []
        rows = list(csv.DictReader(io.StringIO(workforce.body.decode("utf-8-sig"))))
        expect(set(rows[0]) if rows else set(), {"time", "series", "variant", "value"}, "yale workforce chart")
        expect({r["series"] for r in rows}, set(BASELINES), "yale workforce chart series")
        for r in rows:
            if r["series"] not in BASELINES or r["variant"] != "indexed" or r["value"] in (None, ""):
                continue
            start, measure = BASELINES[r["series"]]
            out.append(self._obs(workforce, "us_workers", measure, _months_after(start, int(r["time"])), r))
        rows = list(csv.DictReader(io.StringIO(graduates.body.decode("utf-8-sig"))))
        expect(set(rows[0]) if rows else set(), {"time", "series", "value"}, "yale graduates chart")
        expect({r["series"] for r in rows}, {"Dissimilarity"}, "yale graduates chart series")
        for r in rows:
            if r["series"] == "Dissimilarity" and r["value"] not in (None, ""):
                month = date.fromisoformat(r["time"]).replace(day=1)
                out.append(self._obs(graduates, "recent_vs_older_grads", "occupation_dissimilarity_pp", month, r))
        newest = max((o.as_of_date for o in out), default=None)
        # rows are dated at the month's start and land about six weeks later, so a quarter means a release was missed
        if newest and (workforce.retrieved_at.date() - newest).days > 92:
            self.errors.append(f"newest month {newest}; the tracker may have moved, so check its manifest")
        return out

    def _obs(self, item: RawItem, subject: str, measure: str, month: date, r: dict[str, str]) -> Observation:
        return self.obs(
            item,
            series_key=series_key(self.source_id, subject, measure, "m"),
            unit="pp",
            as_of_date=month,
            published_date=item.retrieved_at.date(),
            value_numeric=float(r["value"]),
            tier=Tier.PUBLISHED_ANALYSIS,
            audited_vs_reported=Basis.estimated,
            extraction_method=Extraction.api,
            raw_snippet=f"{r['series']} {r['time']}: {r['value']}",
        )
