"""METR time horizons: per-model 50%/80% horizons with CIs, plus METR's own published doubling time (tier 1)."""

from __future__ import annotations

import json

import yaml

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

SUITE_CEILING_MIN = 16 * 60
CEILING_NOTE = "METR: measurements above 16 hours are unreliable with the current task suite"


class Metr(Connector):
    source_id = "metr"
    urls = ["https://metr.org/assets/benchmark_results_1_1.yaml"]
    expect_series = ["metr.*.horizon_50.pt", "metr.*.horizon_80.pt", "metr.suite.doubling_time_days.pt"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        doc = yaml.safe_load(item.body)
        expect(set(doc), {"results", "doubling_time_in_days"}, "metr yaml")
        common = dict(
            tier=Tier.BENCHMARK, audited_vs_reported=Basis.reported, extraction_method=Extraction.api
        )
        rows: list[Observation] = []
        for model, r in doc["results"].items():
            metrics, rel = r.get("metrics") or {}, r.get("release_date")
            if not rel:
                continue
            for pct, key in (("50", "p50_horizon_length"), ("80", "p80_horizon_length")):
                h = metrics.get(key)
                if not h or h.get("estimate") is None:
                    continue
                est = float(h["estimate"])
                over = est > SUITE_CEILING_MIN
                rows.append(
                    self.obs(
                        item,
                        series_key=f"metr.{model}.horizon_{pct}.pt",
                        unit="minutes",
                        as_of_date=rel,
                        value_numeric=est,
                        value_low=h.get("ci_low"),
                        value_high=h.get("ci_high"),
                        raw_snippet=json.dumps({model: {key: h, "release_date": str(rel)}}, sort_keys=True),
                        disputed=over,
                        dispute_text=CEILING_NOTE if over else None,
                        **common,
                    )
                )
        d = doc["doubling_time_in_days"].get("from_2023_on") or {}
        if d.get("point_estimate") is not None:
            rows.append(
                self.obs(
                    item,
                    series_key="metr.suite.doubling_time_days.pt",
                    unit="days",
                    as_of_date=item.published_date,
                    value_numeric=float(d["point_estimate"]),
                    value_low=d.get("ci_low"),
                    value_high=d.get("ci_high"),
                    raw_snippet=json.dumps(
                        {"doubling_time_in_days": doc["doubling_time_in_days"]}, sort_keys=True
                    ),
                    **common,
                )
            )
        return rows
