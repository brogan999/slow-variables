"""BLS public API v2 (no key: 25 queries/day, ample for a nightly run). Government statistics: tier 4, reported."""

from __future__ import annotations

import json
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

SERIES = {  # id -> (grain, unit)
    "PRS85006091": (
        "q",
        "pct_change_yoy",
    ),  # nonfarm business labour productivity, vs same quarter a year ago
    "PRS85006092": ("q", "pct_change_qoq_saar"),  # same, q/q at annual rate
    "PRS85006093": ("q", "index_2017_100"),  # same, index level
    "MPU4910012": ("a", "index_2017_100"),  # private nonfarm business total factor productivity, annual index
    "PRS85006173": ("q", "index_2017_100"),  # nonfarm business labor share, index
}
QUARTER_END = {"Q01": (3, 31), "Q02": (6, 30), "Q03": (9, 30), "Q04": (12, 31)}


class Bls(Connector):
    source_id = "bls"
    urls = ["https://api.bls.gov/publicAPI/v2/timeseries/data/"]
    headers = {"Content-Type": "application/json"}
    expect_series = ["bls.prs85006091.q", "bls.mpu4910012.a"]

    def __init__(self, today: date | None = None) -> None:
        super().__init__()
        y = (today or date.today()).year
        self.post_json = {"seriesid": list(SERIES), "startyear": str(y - 9), "endyear": str(y)}

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        doc = json.loads(item.body)
        expect({doc.get("status")}, {"REQUEST_SUCCEEDED"}, "bls api")
        rows: list[Observation] = []
        for s in doc["Results"]["series"]:
            sid = s["seriesID"]
            if sid not in SERIES:
                continue
            grain, unit = SERIES[sid]
            for x in s["data"]:
                p = x["period"]
                if p in QUARTER_END:
                    end = date(int(x["year"]), *QUARTER_END[p])
                elif p == "A01":
                    end = date(int(x["year"]), 12, 31)
                else:
                    continue
                rows.append(
                    self.obs(
                        item,
                        series_key=f"bls.{sid.lower()}.{grain}",
                        unit=unit,
                        as_of_date=end,
                        value_numeric=float(x["value"]),
                        tier=Tier.OFFICIAL_FILING,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=json.dumps(
                            {
                                "seriesID": sid,
                                **{k: x[k] for k in ("year", "period", "periodName", "value") if k in x},
                            },
                            sort_keys=True,
                        ),
                    )
                )
        return rows
