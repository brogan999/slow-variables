"""Canaries Dashboard data (Stanford Digital Economy Lab and ADP Research): the "latest" by-exposure package.

Year-on-year employment change by AI-exposure quintile, monthly, from ADP payroll records. Stored as published
(signed decimal rates); tier 6, reported. Cited as the Lab asks on the source row.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect
from .ramp import month_end

URL = "https://storage.googleapis.com/aviary-del-public/release_memos/latest/downloads/canaries_by_exposure_results.zip"
MEMBER = "canaries_by_exposure_yoy_change.csv"
QUINTILES = {
    "Quintile 1 (least exposed)": "q1",
    "Quintile 2": "q2",
    "Quintile 3": "q3",
    "Quintile 4": "q4",
    "Quintile 5 (most exposed)": "q5",
}


class Canaries(Connector):
    source_id = "canaries"
    urls = [URL]
    expect_series = ["canaries.us_exposure_q5.employment_yoy.m", "canaries.us_exposure_q1.employment_yoy.m"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        zf = zipfile.ZipFile(io.BytesIO(item.body))
        expect(set(zf.namelist()), {MEMBER}, "canaries by-exposure package")
        reader = csv.DictReader(io.StringIO(zf.read(MEMBER).decode("utf-8")))
        expect(set(reader.fieldnames or []), {"observation_date", "vintage", *QUINTILES}, MEMBER)
        rows: list[Observation] = []
        for r in reader:
            for col, q in QUINTILES.items():
                if not (r.get(col) or "").strip():
                    continue
                rows.append(
                    self.obs(
                        item,
                        series_key=f"canaries.us_exposure_{q}.employment_yoy.m",
                        unit="share",
                        as_of_date=month_end(r["observation_date"]),
                        published_date=date.fromisoformat(r["vintage"]),
                        value_numeric=float(r[col]),
                        tier=Tier.PUBLISHED_ANALYSIS,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=json.dumps(
                            {
                                "file": MEMBER,
                                "observation_date": r["observation_date"],
                                "column": col,
                                "value": r[col],
                                "vintage": r["vintage"],
                            },
                            sort_keys=True,
                        ),
                    )
                )
        return rows
