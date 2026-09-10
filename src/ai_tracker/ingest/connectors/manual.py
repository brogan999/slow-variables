"""Figures quoted from documents. Every row's URL is fetched and its raw_snippet must appear verbatim on the page.

This is how the briefs' appendix numbers enter: never typed into an indicator, always as an observation whose
snippet-in-page assertion either passes or rejects the row. Rows land `pending`; merge to main approves them.
"""

from __future__ import annotations

import io
import logging
from datetime import date, datetime, timezone
from pathlib import Path

import httpx
import yaml

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem
from ..scrub import html_to_text, normalise, scrub

log = logging.getLogger(__name__)


def pdf_text(body: bytes) -> str:
    import pdfplumber

    with pdfplumber.open(io.BytesIO(body)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


class Manual(Connector):
    source_id = "manual"
    kind = "html"
    headers = {"Accept": "text/html,application/pdf,text/csv,*/*;q=0.8", "Accept-Language": "en"}

    def __init__(self, path: Path = Path("seed/manual_observations.yaml")) -> None:
        super().__init__()
        self.rows: list[dict] = (
            (yaml.safe_load(path.read_text()) or {}).get("observations") or [] if path.exists() else []
        )
        self.urls = [r["url"] for r in self.rows]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        items: list[RawItem] = []
        for url in self.urls:
            try:
                items.append(self.fetch_one(url, day, refetch))
            except (httpx.HTTPStatusError, PermissionError) as e:  # keep the row, mark it unverified
                status = e.response.status_code if isinstance(e, httpx.HTTPStatusError) else 999
                items.append(RawItem(url, b"", status, datetime.now(timezone.utc), "", None))
        return items

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out: list[Observation] = []
        for r, item in zip(self.rows, items):
            common = dict(
                series_key=r["series_key"],
                unit=r["unit"],
                as_of_date=r["as_of_date"],
                published_date=r.get("published_date") or item.published_date,
                entity_id=r.get("entity_id"),
                tier=Tier(int(r["tier"])),
                audited_vs_reported=Basis(r["basis"]),
                extraction_method=Extraction.manual,
                raw_snippet=r["raw_snippet"],
                value_numeric=r.get("value"),
                value_text=r.get("value_text"),
                run_rate_vs_booked=r.get("run_rate_vs_booked"),
            )
            if item.http_status >= 400:  # never store a number whose page we could not read
                self.errors.append(
                    f"{r['series_key']}: HTTP {item.http_status} for {item.url} - row rejected"
                )
                continue
            text = (
                pdf_text(item.body)
                if item.body[:5] == b"%PDF-"
                else html_to_text(item.body.decode("utf-8", "ignore"))
            )
            clean, flags = scrub(text)
            self.scrubbed += flags
            if normalise(r["raw_snippet"]) not in normalise(clean):
                self.errors.append(f"{r['series_key']}: snippet not found verbatim on {item.url}")
                log.error("manual: snippet not found for %s — row rejected", r["series_key"])
                continue
            out.append(
                self.obs(
                    item, disputed=bool(r.get("dispute_text")), dispute_text=r.get("dispute_text"), **common
                )
            )
        return out
