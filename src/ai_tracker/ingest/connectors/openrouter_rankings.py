"""OpenRouter /rankings: the dehydrated query payload on the page carries token totals per model for the day's
top-model table. Scraped (pending until merge), tier 3. Only the listed models appear, so any concentration
computed from it is over the top slice, not the whole market; the metric says so.
"""

from __future__ import annotations

import json
import re

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, slug

URL = "https://openrouter.ai/rankings"


def parse_payload(html: str) -> list[dict]:
    s = html.replace('\\"', '"')
    m = re.search(r'"queries":\[\{"dehydratedAt":\d+,"state":\{"data":(\[\{"date":.*)', s)
    if not m:
        return []
    arr, depth = m.group(1), 0
    for k, ch in enumerate(arr):
        depth += ch == "["
        depth -= ch == "]"
        if depth == 0:
            return json.loads(arr[: k + 1])
    return []


class OpenRouterRankings(Connector):
    source_id = "openrouter_rankings"
    kind = "html"
    urls = [URL]
    optional = (
        True  # OpenRouter's CDN answers GitHub runners with 403 on robots.txt; a local ingest fills the gap
    )
    headers = {"Accept": "text/html"}
    expect_series = ["openrouter_rankings.*.tokens.d"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        rows = parse_payload(item.body.decode("utf-8", "ignore"))
        expect(
            set(rows[0]) if rows else set(),
            {"date", "model_permaslug", "total_completion_tokens", "total_prompt_tokens"},
            "openrouter rankings payload",
        )
        out = []
        for r in rows:
            model = slug(r["model_permaslug"])
            when = r["date"][:10]
            out.append(
                self.obs(
                    item,
                    series_key=f"openrouter_rankings.{model}.tokens.d",
                    unit="tokens",
                    as_of_date=when,
                    published_date=when,
                    value_numeric=float(r["total_completion_tokens"] + r["total_prompt_tokens"]),
                    tier=Tier.PRODUCT_BEHAVIOUR,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.scrape,
                    raw_snippet=f"{r['model_permaslug']} {r['date'][:10]} prompt {r['total_prompt_tokens']} completion {r['total_completion_tokens']}",
                )
            )
        return out
