"""Ramp AI Index: the monthly series embedded in the /data/ai-index page. The CSV download is disallowed by robots.txt,
so the connector reads only the page, which robots allows. Tier 3 (card spend observed on Ramp), reported.

Shares are Ramp's published percentages over 100, dated to the end of their month, so these rows continue the
hand-entered Ramp series (the same published figures, more precisely) and supersede them.
"""

from __future__ import annotations

import json
import re
from datetime import date, timedelta

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

URL = "https://ramp.com/data/ai-index"
VENDORS = {  # Ramp's vendor label -> (series subject, entity id)
    "Anthropic": ("anthropic", "anthropic"),
    "OpenAI": ("openai", "openai"),
    "xAI": ("xai", "xai"),
    "Google": ("google", "google_deepmind"),
    "DeepSeek": ("deepseek", "deepseek"),
    "Mistral AI": ("mistral", "mistral"),
}


def month_end(first: str) -> date:
    d = date.fromisoformat(first).replace(day=28) + timedelta(days=4)
    return d - timedelta(days=d.day)


def arrays(html: str) -> dict[str, list[dict]]:
    """The page ships its data as JSON escaped inside a script string: `\\"key\\":[{\\"date_month\\":...}]`."""
    out = {}
    for key in ("adoptionOverall", "adoptionVendor", "spendPerEmployee"):
        m = re.search(r'\\"' + key + r'\\":(\[\{.*?\}\])(?=,\\"[A-Za-z]+\\":|\})', html, re.S)
        if m:
            out[key] = json.loads(m.group(1).replace('\\"', '"'))
    return out


class Ramp(Connector):
    source_id = "ramp"
    urls = [URL]
    kind = "html"
    expect_series = ["ramp.us_businesses.paid_ai_adoption_share.m", "ramp.anthropic.business_paid_share.m"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        data = arrays(item.body.decode("utf-8", "ignore"))
        expect(
            set(data), {"adoptionOverall", "adoptionVendor", "spendPerEmployee"}, "ramp ai-index page data"
        )
        rows: list[Observation] = []

        def add(key: str, entity: str | None, unit: str, value: float, rec: dict) -> None:
            rows.append(
                self.obs(
                    item,
                    series_key=key,
                    entity_id=entity,
                    unit=unit,
                    as_of_date=month_end(rec["date_month"]),
                    published_date=item.retrieved_at.date(),
                    value_numeric=value,
                    tier=Tier.PRODUCT_BEHAVIOUR,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.scrape,
                    raw_snippet=json.dumps(rec, sort_keys=True),
                )
            )

        for r in data["adoptionOverall"]:
            add(
                "ramp.us_businesses.paid_ai_adoption_share.m",
                None,
                "share",
                round(r["adoption_rate_pct"] / 100, 6),
                r,
            )
        for r in data["adoptionVendor"]:
            if r.get("vendor") in VENDORS and r.get("adoption_rate_pct") is not None:
                subject, entity = VENDORS[r["vendor"]]
                add(
                    f"ramp.{subject}.business_paid_share.m",
                    entity,
                    "share",
                    round(r["adoption_rate_pct"] / 100, 6),
                    r,
                )
        for r in data["spendPerEmployee"]:
            if isinstance(r.get("median_pepm"), (int, float)):
                add(
                    "ramp.us_businesses.ai_spend_per_employee_median_usd.m",
                    None,
                    "USD",
                    float(r["median_pepm"]),
                    r,
                )
        return rows
