"""Jamin Ball's weekly cloud-software multiples, from the Substack feed (full post bodies ship in content:encoded)."""

from __future__ import annotations

import re

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem
from ..scrub import html_to_text, normalise
from .feeds import parse_feed

FEED = "https://cloudedjudgement.substack.com/feed"
PATTERNS = {
    "saas_public": r"Overall Median:\s*([\d.]+)x",
    "saas_public_top5": r"Top 5 Median:\s*([\d.]+)x",
}


class CloudedJudgment(Connector):
    source_id = "clouded_judgment"
    kind = "api"
    urls = [FEED]
    expect_series = ["clouded_judgment.saas_public.ev_ntm_revenue_median.w"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out: list[Observation] = []
        for title, link, body, published in parse_feed(items[0].body):
            text = normalise(html_to_text(body))
            for subject, pat in PATTERNS.items():
                m = re.search(pat, text)
                if not m or not published:
                    continue
                out.append(
                    self.obs(
                        RawItem(
                            link or FEED,
                            items[0].body,
                            items[0].http_status,
                            items[0].retrieved_at,
                            items[0].content_hash,
                        ),
                        series_key=f"clouded_judgment.{subject}.ev_ntm_revenue_median.w",
                        unit="ratio",
                        as_of_date=published,
                        published_date=published,
                        value_numeric=float(m.group(1)),
                        tier=Tier.PUBLISHED_ANALYSIS,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{title}: {m.group(0)}",
                    )
                )
        return out
