"""Epoch AI company data (CC BY 4.0): funding rounds, revenue run-rates, compute spend from ai_companies.zip.

Tier is per table, not per publisher: rounds and run-rates are compiled from press (tier 5); Epoch's `Confidence`
column maps to the basis flag (Confident -> reported, Likely/Uncertain -> estimated), never to the tier.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import date

from ...schema import Basis, Entity, Extraction, Observation, Tier
from ...store import Seed
from ..base import Connector, RawItem, expect

ROUNDS, REVENUE, COMPUTE = (
    "ai_companies_funding_rounds.csv",
    "ai_companies_revenue_reports.csv",
    "ai_companies_compute_spend.csv",
)


def num(v: str | None) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def day(v: str | None) -> date | None:
    try:
        return date.fromisoformat(str(v).strip()[:10])
    except (TypeError, ValueError):
        return None


def slug(company: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", company.strip().lower()).strip("_")


class Epoch(Connector):
    source_id = "epoch"
    urls = ["https://epoch.ai/data/ai_companies.zip"]
    expect_series = ["epoch.*.round_equity_usd.pt", "epoch.*.revenue_run_rate_usd.pt"]

    def __init__(self, entities: list[Entity] | None = None) -> None:
        super().__init__()
        ents = entities if entities is not None else Seed.load().entities
        self.alias = {a.strip().lower(): e.id for e in ents for a in (e.name, e.id, *e.aliases)}

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        z = zipfile.ZipFile(io.BytesIO(item.body))
        expect(set(z.namelist()), {ROUNDS, REVENUE, COMPUTE}, "epoch ai_companies.zip")

        def table(name: str, required: set[str]) -> list[dict[str, str]]:
            recs = list(csv.DictReader(io.StringIO(z.read(name).decode("utf-8-sig", "ignore"))))
            expect(set(recs[0]) if recs else set(), required, name)
            return recs

        def basis(r: dict[str, str]) -> Basis:
            return (
                Basis.reported
                if (r.get("Confidence") or "").strip().lower() == "confident"
                else Basis.estimated
            )

        def emit(
            r: dict[str, str], key: str, value: float, as_of: date, published: date | None, **kw: object
        ) -> Observation:
            return self.obs(
                item,
                series_key=key,
                unit="USD",
                as_of_date=as_of,
                published_date=published or item.published_date,
                value_numeric=value,
                entity_id=self.alias.get(r["Company"].strip().lower()),
                tier=Tier.CREDIBLE_REPORTING,
                audited_vs_reported=basis(r),
                extraction_method=Extraction.api,
                raw_snippet=json.dumps({k: v for k, v in r.items() if v}, sort_keys=True)[:1500],
                **kw,
            )

        rows: list[Observation] = []
        for r in table(ROUNDS, {"Company", "Close date", "Funding (equity)", "Confidence"}):
            eq, closed = num(r.get("Funding (equity)")), day(r.get("Close date"))
            if not eq or not closed or (r.get("Status") or "Closed").strip() != "Closed":
                continue
            s = slug(r["Company"])
            rows.append(
                emit(
                    r,
                    f"epoch.{s}.round_equity_usd.pt",
                    eq,
                    closed,
                    day(r.get("Report date")),
                    value_text=None,
                )
            )
            pm = num(r.get("Valuation (post-money)"))
            if pm:
                rows.append(emit(r, f"epoch.{s}.post_money_usd.pt", pm, closed, day(r.get("Report date"))))
        for r in table(REVENUE, {"Company", "Date", "Annualized revenue (USD)", "Scope", "Confidence"}):
            v, d = num(r.get("Annualized revenue (USD)")), day(r.get("Date")) or day(r.get("Report date"))
            if not v or not d or (r.get("Scope") or "").strip() != "Full company":
                continue
            rows.append(
                emit(
                    r,
                    f"epoch.{slug(r['Company'])}.revenue_run_rate_usd.pt",
                    v,
                    d,
                    day(r.get("Report date")),
                    run_rate_vs_booked="run_rate",
                )
            )
        for r in table(COMPUTE, {"Company", "Amount", "Period type", "Date", "Confidence"}):
            v, d = num(r.get("Amount")), day(r.get("Date"))
            grain = {"Year": "fy", "Quarter": "q"}.get((r.get("Period type") or "").strip())
            if not v or not d or not grain:
                continue
            rows.append(
                emit(
                    r,
                    f"epoch.{slug(r['Company'])}.compute_spend_usd.{grain}",
                    v,
                    d,
                    day(r.get("Report date")),
                )
            )
        return rows
