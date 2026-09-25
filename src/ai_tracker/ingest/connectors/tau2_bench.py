"""Sierra's tau2-bench leaderboard: pass^k per model and domain, the share of tasks an agent solves on every one of k
tries. Reliability, not capability: a model can solve most tasks once and still fail the same task on a retry.
The site reads the bucket the leaderboard page loads: a manifest of submissions, then one file per submission. Each
score is dated by its submission date and keyed by its submission id, since one model can be submitted twice (with and
without reasoning). Tier 1 when Sierra ran it; tier 2 when a vendor reports its own agent. Since March 2026 new models are run on banking_knowledge
only, so each domain is its own series."""

from __future__ import annotations

import json
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, LayoutChanged, RawItem, expect, series_key, slug

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
        if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
            raise LayoutChanged("tau2-bench manifest: no list of submission ids")
        out = [manifest]
        for i in ids:
            try:  # one missing submission must not lose the rest
                out.append(self.fetch_one(f"{BASE}/{i}/submission.json", day, refetch))
            except Exception as e:
                self.errors.append(f"{i}: {type(e).__name__}: {e}")
        return out

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        seen: set[tuple[str, date]] = set()
        for item in items[1:]:
            s = json.loads(item.body)
            expect(set(s), {"model_name", "submitting_organization", "submission_date", "results"}, "tau2-bench submission")
            sub = item.url.rsplit("/", 2)[-2]  # e.g. gpt-5-2-none_sierra_2026-02-26
            model = sub.split("_")[0]
            tier = Tier.BENCHMARK if s["submitting_organization"] == "Sierra" else Tier.MODEL_RELEASE
            for domain, r in (s["results"] or {}).items():
                if not isinstance(r, dict):
                    continue
                for k in KS:
                    v = r.get(f"pass_{k}")
                    if v is None:
                        continue
                    if not 0 <= v <= 100:
                        raise LayoutChanged(f"tau2-bench {s['model_name']} {domain} pass_{k} is {v}, not a percent")
                    key = series_key("tau2_bench", model, f"{slug(domain)}_pass_{k}", "pt")
                    d = date.fromisoformat(s["submission_date"])
                    if (key, d) in seen:
                        self.errors.append(f"two submissions share {key} on {d}")
                        continue
                    seen.add((key, d))
                    out.append(
                        self.obs(
                            item,
                            series_key=key,
                            unit="share",
                            as_of_date=d,
                            value_numeric=v / 100,
                            tier=tier,
                            audited_vs_reported=Basis.reported,
                            extraction_method=Extraction.api,
                            raw_snippet=f"{s['model_name']} ({s['submitting_organization']}) {domain} pass_{k} {v}",
                        )
                    )
        return out
