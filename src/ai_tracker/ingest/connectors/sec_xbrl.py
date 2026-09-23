"""SEC XBRL company facts for the public filers in seed/entities.yaml.

The `frame` field is the SEC's own dedupe: one canonical value per calendar period (CY2026Q2 = quarter,
CY2025 = year, CY2026Q2I = instant), carried by the last filing that reported it. Only 10-K and 10-Q filings and their
amendments are read: when the frame sits on an 8-K recast, the period is read from the latest 10-K or 10-Q with the same
dates, and left out if the two disagree. A year comes only from a 10-K, since SEC can frame the trailing twelve months a
10-Q reports as a year no 10-K has covered yet; an instant counts only for a balance (RPO). A 10-K audits the year and
the balance sheet, not the quarters it lists. Rows without a frame are cumulative year-to-date durations; they are skipped,
except for cash-flow capex, which most filers report only year to date: six- and nine-month rows are kept as `.h1` and
`.9m` so a metric can difference them into quarters.

Filers retire tags, so the tag with the latest period leads. Filers also swap between the two revenue tags and back
(Alphabet did both), so for revenue the other tag fills the periods the leading one lacks, but only when the two agree
on every period both report: where they differ they measure different things, such as total revenue against revenue
from contracts alone.
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
FORMS = ("10-K", "10-Q", "10-K/A", "10-Q/A")
YTD = {"capex"}  # cash-flow measures filed year to date
INSTANT = {"rpo"}  # balances; a cash-flow tag framed at an instant is a tagging slip
YTD_GRAIN = ((170, 195, "h1"), (260, 285, "9m"))
FILL = {"revenue"}  # the capex and D&A tags name different things, so they never fill each other


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
                got = [_periods(t, gaap[t]["units"].get("USD") or [], measure) for t in tags if t in gaap]
                ranked = sorted(
                    (p for p in got if p), key=lambda p: max(r["end"] for *_, r in p.values()), reverse=True
                )  # filers retire tags: the one with the latest period leads
                if not ranked:
                    continue
                picked = ranked[0]
                for other in ranked[1:] if measure in FILL else []:
                    shared = picked.keys() & other.keys()  # at least one, all equal: all() of nothing is True
                    if shared and all(picked[k][2]["val"] == other[k][2]["val"] for k in shared):
                        picked = other | picked
                    elif shared:
                        log.info(
                            "sec_xbrl: %s %s differs from the leading tag; left out",
                            ent.id,
                            next(iter(other.values()))[1],
                        )
                for grain, tag, r in picked.values():
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
                            if r["form"] == "10-K" and (grain == "fy" or not r.get("start"))
                            else Basis.company_stated,
                            extraction_method=Extraction.xbrl,
                            raw_snippet=json.dumps({tag: r}, sort_keys=True),
                        )
                    )
        return rows


def _periods(tag: str, facts: list[dict], measure: str) -> dict[str | tuple, tuple[str, str, dict]]:
    """One tag's facts, one per period: {frame, or (start, end) for a year-to-date row: (grain, tag, fact)}."""
    latest: dict[tuple[str | None, str], dict] = {}
    for r in facts:
        k = (r.get("start"), r["end"])
        if r.get("form") in FORMS and (k not in latest or r["filed"] > latest[k]["filed"]):
            latest[k] = r
    out: dict[str | tuple, tuple[str, str, dict]] = {}
    for r in facts:
        m = FRAME.match(fr := r.get("frame") or "")
        p = r if r.get("form") in FORMS else latest.get((r.get("start"), r["end"]))
        if not m or not p or bool(m.group(3)) != (measure in INSTANT):
            continue
        if p["val"] != r["val"]:
            log.warning(
                "sec_xbrl: %s %s on %s %s differs from its 10-K/10-Q; left out",
                tag,
                fr,
                r["form"],
                r.get("accn"),
            )
        elif m.group(2) or p["form"].startswith("10-K"):
            out[fr] = ("q" if m.group(2) else "fy", tag, p)
    for (start, end), r in latest.items() if measure in YTD else ():
        days = (date.fromisoformat(end) - date.fromisoformat(start)).days if start else 0
        for lo, hi, g in YTD_GRAIN:
            if lo <= days <= hi:
                out[(start, end)] = (g, tag, r)
    return out
