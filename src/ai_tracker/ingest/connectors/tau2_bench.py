"""Sierra's tau2-bench leaderboard: pass^k per model and domain, the share of tasks an agent solves on every one of k
tries. Reliability, not capability: a model can solve most tasks once and still fail the same task on a retry.
The site reads the bucket the leaderboard page loads: a manifest of submissions, then one file per submission. Each
score is dated by its submission date. Tier 1: Sierra runs most submissions itself, and a labelled submitter runs the
rest; the submitting organisation is kept in the snippet. Since March 2026 new models are run on banking_knowledge
only, so each domain is its own series."""

from __future__ import annotations

import json
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, LayoutChanged, RawItem, expect, series_key

BASE = "https://sierra-tau-bench-public.s3.us-west-2.amazonaws.com/submissions"
MANIFEST = f"{BASE}/manifest.json"
KS = (1, 4)


class Tau2Bench(Connector):
    source_id = "tau2_bench"
    urls = [MANIFEST]
    expect_series = ["tau2_bench.*.*_pass_4.pt"]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        manifest = self.fetch_one(MANIFEST, day, refetch)
        ids = json.loads(manifest.body).get("submissions")
        if not isinstance(ids, list) or not ids:
            raise LayoutChanged("tau2-bench manifest: no submissions list")
        return [manifest] + [self.fetch_one(f"{BASE}/{i}/submission.json", day, refetch) for i in ids]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item in items[1:]:
            s = json.loads(item.body)
            expect(set(s), {"model_name", "submitting_organization", "submission_date", "results"}, "tau2-bench submission")
            for domain, r in (s["results"] or {}).items():
                if not isinstance(r, dict):
                    continue
                for k in KS:
                    v = r.get(f"pass_{k}")
                    if v is None:
                        continue
                    if not 0 <= v <= 100:
                        raise LayoutChanged(f"tau2-bench {s['model_name']} {domain} pass_{k} is {v}, not a percent")
                    out.append(
                        self.obs(
                            item,
                            series_key=series_key("tau2_bench", s["model_name"], f"{domain}_pass_{k}", "pt"),
                            unit="share",
                            as_of_date=date.fromisoformat(s["submission_date"]),
                            value_numeric=v / 100,
                            tier=Tier.BENCHMARK,
                            audited_vs_reported=Basis.reported,
                            extraction_method=Extraction.api,
                            raw_snippet=f"{s['model_name']} ({s['submitting_organization']}) {domain} pass_{k} {v}",
                        )
                    )
        return out
