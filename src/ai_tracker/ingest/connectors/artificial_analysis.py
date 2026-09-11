"""Artificial Analysis API v2 (needs ARTIFICIAL_ANALYSIS_API_KEY; optional so the nightly stays green without it).

`GET /api/v2/data/llms/models` with `x-api-key`. Per model: the Intelligence Index (tier 1, independent evals),
the blended price per million tokens (tier 3) and median output speed. Index rows are dated by the model's release
date (like METR), so a re-score supersedes in place. Price and speed are a change-point ledger like the OpenRouter
price connector: an unchanged value reuses its existing as_of. AA reports an unpriced model as 0; those are skipped.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect
from .openrouter import _latest

URL = "https://artificialanalysis.ai/api/v2/data/llms/models"
FIELDS = {
    "intelligence_index": (
        ("evaluations", "artificial_analysis_intelligence_index"),
        "index",
        Tier.BENCHMARK,
    ),
    "price_blended_usd_per_mtok": (("pricing", "price_1m_blended_3_to_1"), "USD", Tier.PRODUCT_BEHAVIOUR),
    "output_tokens_per_second": (
        ("median_output_tokens_per_second",),
        "tokens_per_second",
        Tier.PRODUCT_BEHAVIOUR,
    ),
}


class ArtificialAnalysis(Connector):
    source_id = "artificial_analysis"
    urls = [URL]
    optional = True
    expect_series = ["aa.*.intelligence_index.pt"]

    def __init__(self, ledger: Path = Path("data/observations/artificial_analysis.jsonl")) -> None:
        super().__init__()
        self.latest = _latest(ledger)

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        key = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
        if not key:
            raise RuntimeError("ARTIFICIAL_ANALYSIS_API_KEY is not set")
        self.headers = {"x-api-key": key}
        return super().fetch(day, refetch)

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        models = json.loads(item.body).get("data") or []
        expect(
            set(models[0]) if models else set(),
            {"slug", "evaluations", "pricing", "model_creator", "release_date"},
            "artificial analysis models",
        )
        today = item.retrieved_at.date()
        out = []
        for m in models:
            subject = re.sub(r"[^a-z0-9]+", "_", m["slug"].lower()).strip("_")
            creator = re.sub(
                r"[^a-z0-9]+", "_", (m.get("model_creator") or {}).get("slug", "").lower()
            ).strip("_")
            for measure, (path, unit, tier) in FIELDS.items():
                v = m
                for k in path:
                    v = (v or {}).get(k) if isinstance(v, dict) else None
                if v is None or (measure != "intelligence_index" and v <= 0):
                    continue
                key = f"aa.{subject}.{measure}.pt"
                prev = self.latest.get(key)
                published = (
                    today if prev is None or abs(prev[1] - float(v)) > 1e-9 else date.fromisoformat(prev[0])
                )
                as_of = (
                    date.fromisoformat(m["release_date"])
                    if measure == "intelligence_index" and m.get("release_date")
                    else published
                )
                out.append(
                    self.obs(
                        item,
                        series_key=key,
                        unit=unit,
                        as_of_date=as_of,
                        published_date=published,
                        value_numeric=float(v),
                        tier=tier,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{m['slug']} ({creator}) {'.'.join(path)} {v}",
                    )
                )
        return out
