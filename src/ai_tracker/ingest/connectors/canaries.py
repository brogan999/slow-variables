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
from ..base import Connector, RawItem, expect, series_key
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


AGE_URL = "https://storage.googleapis.com/aviary-del-public/release_memos/latest/downloads/canaries_age_by_exposure_results.zip"
AGE_MEMBER = "canaries_age_by_exposure.csv"
AGES = {
    "Early Career 1 (22-25)": "age_22_25",
    "Early Career 2 (26-30)": "age_26_30",
    "Developing (31-34)": "age_31_34",
    "Mid-Career 1 (35-40)": "age_35_40",
    "Mid-Career 2 (41-49)": "age_41_49",
    "Senior (50+)": "age_50_plus",
}
KEPT = {"Quintile 5 (most exposed)": "q5", "Quintile 1 (least exposed)": "q1"}


class CanariesAge(Connector):
    """The same Lab's age-by-exposure package: an employment index (100 in November 2022) for each age band within
    each AI-exposure quintile, monthly. Stored as published for the most and least exposed quintiles, the pair a
    junior-against-senior comparison reads; the three middle quintiles stay in the package."""

    source_id = "canaries_age"
    urls = [AGE_URL]
    expect_series = [
        "canaries.us_exposure_q5_age_22_25.employment_index.m",
        "canaries.us_exposure_q5_age_50_plus.employment_index.m",
    ]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        zf = zipfile.ZipFile(io.BytesIO(item.body))
        expect(set(zf.namelist()), {AGE_MEMBER}, "canaries age-by-exposure package")
        reader = csv.DictReader(io.StringIO(zf.read(AGE_MEMBER).decode("utf-8")))
        expect(set(reader.fieldnames or []), {"observation_date", "exposure_quintile", "vintage", *AGES}, AGE_MEMBER)
        rows: list[Observation] = []
        for r in reader:
            q = KEPT.get(r["exposure_quintile"])
            if not q:
                continue
            for col, age in AGES.items():
                if not (r.get(col) or "").strip():
                    continue
                rows.append(
                    self.obs(
                        item,
                        series_key=series_key("canaries", f"us_exposure_{q}_{age}", "employment_index", "m"),
                        unit="index",
                        as_of_date=month_end(r["observation_date"]),
                        published_date=date.fromisoformat(r["vintage"]),
                        value_numeric=float(r[col]),
                        tier=Tier.PUBLISHED_ANALYSIS,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=json.dumps(
                            {
                                "file": AGE_MEMBER,
                                "observation_date": r["observation_date"],
                                "exposure_quintile": r["exposure_quintile"],
                                "column": col,
                                "value": r[col],
                                "vintage": r["vintage"],
                            },
                            sort_keys=True,
                        ),
                    )
                )
        return rows
