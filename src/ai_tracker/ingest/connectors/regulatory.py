"""Regulatory and directory sources: FDA's AI-enabled device list (CSV), NCSL's state AI legislation table (HTML),
rl-list.com's RL-environment vendor directory (JSON) and Our World in Data's AI investment series (CSV)."""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect


def _month_end(d: date) -> date:
    nxt = date(d.year + (d.month == 12), 1 if d.month == 12 else d.month + 1, 1)
    return date.fromordinal(nxt.toordinal() - 1)


class FdaDevices(Connector):
    """Cumulative count of FDA-authorised AI-enabled devices at each month end (fda.gov list, tier 4)."""

    source_id = "fda_devices"
    urls = ["https://www.fda.gov/media/178541/download?attachment"]
    expect_series = ["fda.us.ai_devices_cumulative.m"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows = list(csv.DictReader(io.StringIO(items[0].body.decode("utf-8-sig", "ignore"))))
        expect(
            set(rows[0]) if rows else set(), {"Date of Final Decision", "Submission Number"}, "fda columns"
        )
        dates = sorted(d for d in (self._d(r["Date of Final Decision"]) for r in rows) if d)
        out, months = [], sorted({_month_end(d) for d in dates if d.year >= 2018})
        for m in months:
            n = sum(1 for d in dates if d <= m)
            out.append(
                self.obs(
                    items[0],
                    series_key="fda.us.ai_devices_cumulative.m",
                    unit="count",
                    as_of_date=m,
                    published_date=m,
                    value_numeric=float(n),
                    tier=Tier.OFFICIAL_FILING,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.api,
                    raw_snippet=f"{n} devices with a final decision on or before {m.isoformat()} in the FDA AI-enabled device list",
                )
            )
        return out

    @staticmethod
    def _d(s: str) -> date | None:
        try:
            return datetime.strptime(s.strip(), "%m/%d/%Y").date()
        except ValueError:
            return None


class Ncsl(Connector):
    """State AI bills introduced and enacted in a legislative year, counted from NCSL's tracking table (scrape -> pending)."""

    source_id = "ncsl"
    kind = "html"
    year = 2025
    urls = [f"https://www.ncsl.org/technology-and-communication/artificial-intelligence-{year}-legislation"]
    expect_series = ["ncsl.us.ai_bills_introduced.a"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        html = items[0].body.decode("utf-8", "ignore")
        table = re.search(r"<table.*?</table>", html, re.S)
        expect({"table"} if table else set(), {"table"}, "ncsl table")
        rows = [
            re.sub(r"<[^>]+>", " ", tr) for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", table.group(0), re.S)
        ]
        bills = [r for r in rows if re.search(r"\b[HSA]\.?[BR]?\s?\d+", r) and "Jurisdiction" not in r]
        enacted = [r for r in bills if re.search(r"Enacted|Signed|Adopted", r)]
        as_of = date(self.year, 12, 31)
        out = []
        for measure, n in (("ai_bills_introduced", len(bills)), ("ai_bills_enacted", len(enacted))):
            out.append(
                self.obs(
                    items[0],
                    series_key=f"ncsl.us.{measure}.a",
                    unit="count",
                    as_of_date=as_of,
                    published_date=items[0].published_date,
                    value_numeric=float(n),
                    tier=Tier.PUBLISHED_ANALYSIS,
                    audited_vs_reported=Basis.reported,
                    extraction_method=Extraction.scrape,
                    raw_snippet=f"{n} rows ({measure}) in NCSL's Artificial Intelligence {self.year} Legislation table",
                )
            )
        return out


class RlList(Connector):
    """Count of active commercial RL-environment vendors in rl-list.com's directory JSON."""

    source_id = "rl_list"
    urls = ["https://rl-list.com/rl-list-dataset.json"]
    expect_series = ["rl_list.commercial.active_vendor_count.pt"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        d = json.loads(items[0].body)
        expect(set(d), {"meta", "vendors"}, "rl-list keys")
        vendors = [
            v
            for v in d["vendors"]
            if v.get("segment") == "Commercial vendors" and (v.get("status") or {}).get("value") == "active"
        ]
        as_of = date.fromisoformat(d["meta"]["generated"])
        return [
            self.obs(
                items[0],
                series_key="rl_list.commercial.active_vendor_count.pt",
                unit="count",
                as_of_date=as_of,
                published_date=as_of,
                value_numeric=float(len(vendors)),
                tier=Tier.PUBLISHED_ANALYSIS,
                audited_vs_reported=Basis.reported,
                extraction_method=Extraction.api,
                raw_snippet=f"{len(vendors)} active commercial vendors of {d['meta'].get('vendor_count')} listed; generated {d['meta']['generated']}",
            )
        ]


class Owid(Connector):
    """Our World in Data's AI investment series (from the AI Index / Quid): private investment by region, corporate investment by type."""

    source_id = "owid"
    urls = [
        "https://ourworldindata.org/grapher/private-investment-in-artificial-intelligence.csv",
        "https://ourworldindata.org/grapher/corporate-investment-in-artificial-intelligence-by-type.csv",
    ]
    expect_series = ["owid.world.private_ai_investment_usd.a"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item, measure in zip(items, ("private_ai_investment_usd", "corporate_ai_investment_usd")):
            rows = list(csv.DictReader(io.StringIO(item.body.decode("utf-8", "ignore"))))
            expect(set(rows[0]) if rows else set(), {"Entity", "Year"}, "owid columns")
            col = next(c for c in rows[0] if c not in ("Entity", "Code", "Year"))
            for r in rows:
                if not r.get(col):
                    continue
                out.append(
                    self.obs(
                        item,
                        series_key=f"owid.{re.sub(r'[^a-z0-9]+', '_', r['Entity'].lower()).strip('_')}.{measure}.a",
                        unit="USD",
                        as_of_date=date(int(r["Year"]), 12, 31),
                        published_date=item.published_date,
                        value_numeric=float(r[col]),
                        tier=Tier.PUBLISHED_ANALYSIS,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{r['Entity']} {r['Year']}: {col} = {r[col]}",
                    )
                )
        return out
