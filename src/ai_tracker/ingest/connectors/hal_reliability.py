"""HAL's AI Agent Reliability Tracker (Princeton): an independent evaluator's scores for the agents it runs on its own
benchmarks, embedded in the page as its chart data. Tier 1: HAL runs the evaluations itself. Each agent is dated by
its model's release, as HAL plots it; the row is published when fetched, since the page dates no score. Overall
reliability is HAL's index from 0 to 1 of how consistently, predictably and robustly an agent behaves (safety is scored
apart), stored as an index as HAL prints it; accuracy, from the same runs, is a share of tasks solved."""

from __future__ import annotations

import json
import re

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, LayoutChanged, RawItem, expect, series_key

URL = "https://hal.cs.princeton.edu/reliability/"
DIMENSIONS = {
    "Overall Reliability": "reliability",
    "Consistency": "consistency",
    "Predictability": "predictability",
    "Robustness": "robustness",
    "Safety": "safety",
}
VIEW = "All Benchmarks"  # the page's per-benchmark views, read by name: whichever the page shows first may change


def parse_object(html: str, name: str) -> dict:
    """The object assigned to `window.<name>`, read by matching its braces; {} when absent or broken."""
    m = re.search(r"window\." + re.escape(name) + r"\s*=\s*", html)
    if not m:
        return {}
    depth = 0
    for k in range(m.end(), len(html)):
        depth += html[k] == "{"
        depth -= html[k] == "}"
        if depth == 0:
            try:
                return json.loads(html[m.end() : k + 1])
            except ValueError:
                return {}
    return {}


class HalReliability(Connector):
    source_id = "hal_reliability"
    kind = "html"
    urls = [URL]
    headers = {"Accept": "text/html"}
    expect_series = ["hal_reliability.*.reliability.pt", "hal_reliability.*.accuracy.pt"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        views = parse_object(item.body.decode("utf-8", "ignore"), "_trendByBench")
        expect(set(views), {VIEW}, "HAL reliability views")
        data = views[VIEW]
        expect(set(data), set(DIMENSIONS), "HAL reliability dimensions")
        for d in DIMENSIONS:
            expect(set(data[d]), {"vs_date", "acc_over_time"}, f"HAL {d} charts")
        # accuracy is plotted against release date under every dimension; the overall chart's copy is the one read
        charts = [(DIMENSIONS[d], data[d]["vs_date"].get("points")) for d in DIMENSIONS]
        charts.append(("accuracy", data["Overall Reliability"]["acc_over_time"].get("points")))
        out = []
        for measure, points in charts:
            if not isinstance(points, list):
                raise LayoutChanged(f"HAL {measure}: no list of points")
            for p in points:
                expect(set(p), {"x", "y", "slug", "label"}, f"HAL {measure} point")
                if not isinstance(p["y"], (int, float)):
                    raise LayoutChanged(f"HAL {measure} point {p.get('slug')}: score is not a number")
                out.append(
                    self.obs(
                        item,
                        series_key=series_key("hal_reliability", p["slug"], measure, "pt"),
                        unit="share" if measure == "accuracy" else "index",
                        as_of_date=p["x"],
                        value_numeric=float(p["y"]),
                        tier=Tier.BENCHMARK,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.scrape,
                        raw_snippet=json.dumps({"measure": measure, **p}, sort_keys=True),
                    )
                )
        return out
