"""FRED CSV series (no key needed). Today: the Bick-Blandin-Deming Real-Time Population Survey genAI series."""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

# id -> (series suffix, unit, divisor, tier). RPS = survey run by Fed economists, hosted on FRED: tier 6, reported.
SERIES = {
    "RPSGENAIASSISTWRKHRSALL": ("us_workers.hours_assisted_share", "share", 100, Tier.PUBLISHED_ANALYSIS),
    "RPSGENAIUSAGESHARELWWORK": ("us_workers.work_use_weekly_share", "share", 100, Tier.PUBLISHED_ANALYSIS),
    "RPSGENAIUSAGESHAREALL": ("us_adults.any_use_share", "share", 100, Tier.PUBLISHED_ANALYSIS),
    "RPSGENAIUSAGESHARELWALL": ("us_adults.use_last_week_share", "share", 100, Tier.PUBLISHED_ANALYSIS),
}


def quarter_end(d: date) -> date:
    m = ((d.month - 1) // 3 + 1) * 3
    first_next = date(d.year + (m == 12), 1 if m == 12 else m + 1, 1)
    return first_next - timedelta(days=1)


class Fred(Connector):
    source_id = "fred"
    urls = [f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}" for sid in SERIES]
    expect_series = ["fred.us_workers.hours_assisted_share.q", "fred.us_adults.any_use_share.q"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: list[Observation] = []
        for sid, item in zip(SERIES, items):
            suffix, unit, div, tier = SERIES[sid]
            recs = list(csv.DictReader(io.StringIO(item.body.decode("utf-8", "ignore"))))
            expect(set(recs[0]) if recs else set(), {"observation_date", sid}, f"fred {sid}")
            for r in recs:
                if r[sid] in (".", "", None):
                    continue
                start = date.fromisoformat(r["observation_date"])
                rows.append(
                    self.obs(
                        item,
                        series_key=f"fred.{suffix}.q",
                        unit=unit,
                        as_of_date=quarter_end(start),
                        period_start=start,
                        value_numeric=float(r[sid]) / div,
                        tier=tier,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{sid} {r['observation_date']},{r[sid]}",
                    )
                )
        return rows
