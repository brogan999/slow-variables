"""SEC XBRL company facts for the public filers in seed/entities.yaml.

The `frame` field is the SEC's own dedupe: one canonical value per calendar period (CY2026Q2 = quarter,
CY2025 = year, CY2026Q2I = instant). Rows without a frame are cumulative year-to-date durations; they are skipped,
except for cash-flow capex, which most filers report only year to date: six- and nine-month rows are kept as `.h1` and
`.9m` so a metric can difference them into quarters.
"""

from __future__ import annotations

import json
import logging
import re
from datetime import date

import httpx

from ...schema import Basis, Entity, Extraction, Observation, Tier
from ...store import Seed
from ..base import Connector, RawItem, expect

CONCEPTS = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "gross_profit": ["GrossProfit"],
    "cost_of_revenue": ["CostOfRevenue"],
    "capex": [
        "PaymentsToAcquirePropertyPlantAndEquipment",
        "PaymentsToAcquireProductiveAssets",
        "PaymentsToAcquirePropertyPlantAndEquipmentAndIntangibleAssets",
    ],
    "rpo": ["RevenueRemainingPerformanceObligation"],
    "da": ["DepreciationDepletionAndAmortization", "DepreciationAndAmortization"],
}
FRAME = re.compile(r"^CY(\d{4})(?:Q([1-4]))?(I?)$")
YTD = {"capex"}  # cash-flow measures filed year to date
YTD_GRAIN = ((170, 195, "h1"), (260, 285, "9m"))


log = logging.getLogger(__name__)


class SecXbrl(Connector):
    source_id = "sec_xbrl"
    headers = {"Accept": "application/json"}
    expect_series = ["sec.nvda.revenue.q", "sec.nvda.gross_profit.q"]

    def __init__(self, entities: list[Entity] | None = None) -> None:
        super().__init__()
        self.entities = [e for e in (entities or Seed.load().entities) if e.cik]
        self.urls = [f"https://data.sec.gov/api/xbrl/companyfacts/CIK{e.cik}.json" for e in self.entities]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        out: list[RawItem] = []
        for url in self.urls:
            try:
                out.append(self.fetch_one(url, day, refetch))
            except httpx.HTTPStatusError as ex:
                if ex.response.status_code != 404:
                    raise
                log.info("sec_xbrl: no companyfacts for %s (private filer)", url.rsplit("/", 1)[-1])
        return out

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: list[Observation] = []
        by_url = dict(
            zip(self.urls, self.entities)
        )  # a skipped 404 must not shift every later filer onto the wrong company
        for item in items:
            ent = by_url[item.url]
            doc = json.loads(item.body)
            expect(set(doc), {"facts"}, f"sec {ent.id}")
            gaap = doc["facts"].get("us-gaap") or {}
            for measure, tags in CONCEPTS.items():
                present = [t for t in tags if t in gaap and gaap[t]["units"].get("USD")]
                if not present:
                    continue
                tag = max(
                    present, key=lambda t: max(r["end"] for r in gaap[t]["units"]["USD"])
                )  # filers retire tags
                best: dict[str, dict] = {}
                ytd: dict[tuple[str, str], dict] = {}
                for r in gaap[tag]["units"].get("USD") or []:
                    fr = r.get("frame")
                    if fr and (fr not in best or r["filed"] > best[fr]["filed"]):
                        best[fr] = r
                    elif not fr and measure in YTD and r.get("start") and r.get("form") in ("10-K", "10-Q"):
                        k = (r["start"], r["end"])
                        if k not in ytd or r["filed"] > ytd[k]["filed"]:
                            ytd[k] = r
                picked: list[tuple[str, dict]] = []
                for fr, r in best.items():
                    m = FRAME.match(fr)
                    if m and r.get("form") in ("10-K", "10-Q"):
                        picked.append(("q" if m.group(2) else "fy", r))
                for (start, end), r in ytd.items():
                    days = (date.fromisoformat(end) - date.fromisoformat(start)).days
                    picked += [(g, r) for lo, hi, g in YTD_GRAIN if lo <= days <= hi]
                for grain, r in picked:
                    rows.append(
                        self.obs(
                            item,
                            series_key=f"sec.{ent.id}.{measure}.{grain}",
                            unit="USD",
                            as_of_date=date.fromisoformat(r["end"]),
                            period_start=date.fromisoformat(r["start"]) if r.get("start") else None,
                            published_date=date.fromisoformat(r["filed"]),
                            value_numeric=float(r["val"]),
                            entity_id=ent.id,
                            tier=Tier.OFFICIAL_FILING,
                            audited_vs_reported=Basis.audited
                            if r["form"] == "10-K"
                            else Basis.company_stated,
                            extraction_method=Extraction.xbrl,
                            raw_snippet=json.dumps({tag: r}, sort_keys=True),
                        )
                    )
        return rows
