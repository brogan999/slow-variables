"""GetDeploying's GPU rental price history (CC BY 4.0): each week, the median on-demand price per GPU-hour across the
cloud providers it tracks, per GPU model. Tier 3: an aggregator of providers' public list prices. The week still in
progress is re-read each night and supersedes in place."""

from __future__ import annotations

import csv
import io
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, series_key

GPUS = ("nvidia-h100", "nvidia-h200", "nvidia-b200")
URL = "https://getdeploying.com/dataset/gpu-prices/{}.csv"


class GpuRents(Connector):
    source_id = "getdeploying"
    urls = [URL.format(g) for g in GPUS]
    expect_series = ["getdeploying.nvidia_h100.on_demand_median_usd_per_gpu_hour.w"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item in items:
            rows = list(csv.DictReader(io.StringIO(item.body.decode())))
            expect(set(rows[0]) if rows else set(), {"gpu_slug", "date", "billing_type", "median_price", "provider_count"}, "getdeploying csv")
            for r in rows:
                if r["billing_type"] != "ON_DEMAND" or not r["median_price"]:
                    continue
                out.append(
                    self.obs(
                        item,
                        series_key=series_key("getdeploying", r["gpu_slug"], "on_demand_median_usd_per_gpu_hour", "w"),
                        unit="USD",
                        as_of_date=date.fromisoformat(r["date"]),
                        value_numeric=float(r["median_price"]),
                        tier=Tier.PRODUCT_BEHAVIOUR,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=",".join(r.values()),
                    )
                )
        return out
