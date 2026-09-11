"""SEC Form D: the only primary source for private raises. Quarterly data-set zips plus EDGAR full-text search
for the current quarter. Issuers map to entities by CIK only; a name that merely equals a seed alias is listed by
`ai-tracker candidates` for a human to verify (a third of such matches are unrelated companies). Pooled funds
and SPVs are dropped, so "X SPV, a Series of ..." never creates a row.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re
import xml.etree.ElementTree as ET
import zipfile
from datetime import date
from pathlib import Path

import yaml

from ...schema import Basis, Entity, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect

INDEX = "https://www.sec.gov/data-research/sec-markets-data/form-d-data-sets"
EFTS = "https://efts.sec.gov/LATEST/search-index"
PRIMARY = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/primary_doc.xml"
FIRST_QUARTER = "2023q1"  # the AI-era window; earlier quarters are not fetched
SKIP_INDUSTRY = {"Pooled Investment Fund"}


def norm(name: str) -> str:
    name = re.sub(r"[,.]", "", name.lower())
    name = re.sub(
        r"\b(inc|corp|corporation|co|llc|ltd|limited|holdings?|labs?|technologies|technology|ai)\b", "", name
    )
    return re.sub(r"[^a-z0-9]+", " ", name).strip()


def entity_index(entities: list[Entity]) -> tuple[dict[str, str], dict[str, str]]:
    """CIK -> entity id (the only mapping that creates rows) and normalised alias -> entity id (candidates only)."""
    by_cik = {c: e.id for e in entities for c in [e.cik, *e.extra_ciks] if c}
    by_name: dict[str, str] = {}
    for e in entities:
        for a in [e.name, *e.aliases]:
            by_name.setdefault(norm(a), e.id)
    return by_cik, by_name


def parse_zip(body: bytes) -> list[dict[str, str]]:
    """One dict per primary issuer + offering, joined on accession number."""
    z = zipfile.ZipFile(io.BytesIO(body))

    def tsv(suffix: str) -> list[dict[str, str]]:
        name = next(n for n in z.namelist() if n.upper().endswith(suffix))
        return list(csv.DictReader(io.StringIO(z.read(name).decode("latin-1")), delimiter="\t"))

    sub = {r["ACCESSIONNUMBER"]: r for r in tsv("FORMDSUBMISSION.TSV")}
    off = {r["ACCESSIONNUMBER"]: r for r in tsv("OFFERING.TSV")}
    out = []
    for i in tsv("ISSUERS.TSV"):
        if i.get("IS_PRIMARYISSUER_FLAG", "").lower() not in ("yes", "true"):  # the data sets say YES/NO
            continue
        o = off.get(i["ACCESSIONNUMBER"])
        if not o:
            continue
        out.append({**o, **i, "FILING_DATE": sub.get(i["ACCESSIONNUMBER"], {}).get("FILING_DATE", "")})
    return out


def _date(s: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%m/%d/%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            continue
    return None


log = logging.getLogger(__name__)


class FormD(Connector):
    source_id = "formd"
    kind = "api"
    expect_series = ["formd.baseten.amount_sold_usd.pt"]

    def __init__(self, entities_path: Path = Path("seed/entities.yaml")) -> None:
        super().__init__()
        rows = (yaml.safe_load(entities_path.read_text()) or {}).get("entities") or []
        self.entities = [Entity(**r) for r in rows]
        self.by_cik, self.by_name = entity_index(self.entities)
        self.urls = [INDEX]
        self.filed: dict[str, date] = {}  # primary_doc URL -> filing date from its search hit

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        index = self.fetch_one(INDEX, day, refetch)
        links = sorted(
            set(re.findall(r'href="([^"]*?/(\d{4}q[1-4])_d\.zip)"', index.body.decode("utf-8", "ignore")))
        )
        items = [index]
        for href, q in links:
            if q >= FIRST_QUARTER:
                items.append(
                    self.fetch_one(
                        "https://www.sec.gov" + href if href.startswith("/") else href, day, refetch
                    )
                )
        for (
            e
        ) in self.entities:  # current quarter: full-text search by exact name, filtered to the entity's CIK
            if e.cik:
                url = f'{EFTS}?q="{e.name}"&forms=D&dateRange=custom&startdt={day.replace(day=1).isoformat()}'
                try:
                    hit = self.fetch_one(url, day, refetch)
                    items.append(hit)
                    # this quarter's filings carry their amounts in primary_doc.xml before the quarter's zip lands
                    for cik, adsh, filed in self._hits(hit):
                        doc = PRIMARY.format(cik=int(cik), acc=adsh.replace("-", ""))
                        self.filed[doc] = filed
                        items.append(self.fetch_one(doc, day, refetch))
                except Exception as ex:  # noqa: BLE001 - one search failing must not drop the quarterly zips
                    log.warning(
                        "formd: efts %s skipped this run: %s", e.id, ex
                    )  # supplementary; the zips are the record
        return items

    def _hits(self, item: RawItem) -> list[tuple[str, str, date]]:
        """(CIK, accession, filing date) for search hits filed by a seed entity's own CIK."""
        try:
            hits = json.loads(item.body).get("hits", {}).get("hits", [])
        except ValueError:
            return []
        out = []
        for h in hits:
            src = h.get("_source", {})
            cik = next((c.zfill(10) for c in src.get("ciks", []) if c.zfill(10) in self.by_cik), None)
            filed = _date(src.get("file_date", ""))
            if cik and filed and src.get("adsh"):
                out.append((cik, src["adsh"], filed))
        return out

    def _from_primary(self, item: RawItem) -> list[Observation]:
        """A filing's own primary_doc.xml, read into exactly the rows its line in the quarterly zip will produce, so
        the zip's rows later carry the same ids and add nothing twice."""
        x = ET.fromstring(item.body)

        def val(path: str) -> str:
            e = x.find(path)
            return (e.text or "").strip() if e is not None and e.text else ""

        ent = self._match(val("./primaryIssuer/cik"), "")
        if (
            not ent
            or val(".//industryGroupType") in SKIP_INDUSTRY
            or val(".//isPooledInvestmentFundType").lower() == "true"
        ):
            return []
        filed = self.filed.get(item.url) or item.retrieved_at.date()
        sale = _date(val(".//dateOfFirstSale/value")) or filed
        debt_only = val(".//isDebtType").lower() == "true" and val(".//isEquityType").lower() != "true"
        out = []
        for tag, measure in (
            ("totalAmountSold", "debt_sold_usd" if debt_only else "amount_sold_usd"),
            ("totalOfferingAmount", "offering_amount_usd"),
        ):
            raw = val(f".//offeringSalesAmounts/{tag}").replace(",", "")
            if not raw.replace(".", "").isdigit() or float(raw) <= 0:
                continue
            out.append(
                self.obs(
                    item,
                    series_key=f"formd.{ent}.{measure}.pt",
                    entity_id=ent,
                    unit="USD",
                    as_of_date=sale,
                    published_date=filed,
                    value_numeric=float(raw),
                    tier=Tier.OFFICIAL_FILING,
                    audited_vs_reported=Basis.company_stated,
                    extraction_method=Extraction.api,
                    raw_snippet=json.dumps(
                        {
                            "issuer": val("./primaryIssuer/entityName"),
                            "cik": val("./primaryIssuer/cik"),
                            tag: raw,
                            "sale_date": sale.isoformat(),
                            "filed": filed.isoformat(),
                            "form": val("./submissionType"),
                        },
                        sort_keys=True,
                    ),
                )
            )
        return out

    def _match(self, cik: str, name: str) -> str | None:
        # CIK only. A bare name match ("Sierra Co LLC", "PIKA Inc.") is a candidate for a human, never a row.
        return self.by_cik.get(cik.zfill(10))

    def candidates(self, items: list[RawItem]) -> list[dict[str, str]]:
        """Issuers whose normalised name equals a seed alias but whose CIK is not on the entity: review, then add the CIK."""
        out = []
        for item in items:
            if item.body[:2] != b"PK":
                continue
            for r in parse_zip(item.body):
                if (
                    r.get("INDUSTRYGROUPTYPE") in SKIP_INDUSTRY
                    or r.get("ISPOOLEDINVESTMENTFUNDTYPE", "").lower() == "true"
                ):
                    continue
                cik = r.get("CIK", "").zfill(10)
                ent = self.by_name.get(norm(r.get("ENTITYNAME", "")))
                if ent and cik not in self.by_cik:
                    out.append(
                        {
                            "entity": ent,
                            "issuer": r.get("ENTITYNAME", ""),
                            "cik": cik,
                            "city": r.get("CITY", ""),
                            "state": r.get("STATEORCOUNTRY", ""),
                            "industry": r.get("INDUSTRYGROUPTYPE", ""),
                        }
                    )
        return sorted({(c["entity"], c["cik"]): c for c in out}.values(), key=lambda c: c["entity"])

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: list[Observation] = []
        for item in items:
            if item.body[:2] == b"PK":
                rows += self._from_zip(item)
            elif item.url.startswith(EFTS):
                rows += self._from_efts(item)
            elif item.url.endswith("/primary_doc.xml"):
                rows += self._from_primary(item)
        expect({"zip"} if any(i.body[:2] == b"PK" for i in items) else set(), {"zip"}, "formd quarterly zips")
        return rows

    def _from_zip(self, item: RawItem) -> list[Observation]:
        out = []
        for r in parse_zip(item.body):
            if (
                r.get("INDUSTRYGROUPTYPE") in SKIP_INDUSTRY
                or r.get("ISPOOLEDINVESTMENTFUNDTYPE", "").lower() == "true"
            ):
                continue
            ent = self._match(r.get("CIK", ""), r.get("ENTITYNAME", ""))
            if not ent:
                continue
            sale = _date(r.get("SALE_DATE", "")) or _date(r.get("FILING_DATE", ""))
            filed = _date(r.get("FILING_DATE", "")) or sale
            if not sale or not filed:
                continue
            debt_only = (
                r.get("ISDEBTTYPE", "").lower() == "true" and r.get("ISEQUITYTYPE", "").lower() != "true"
            )
            for col, measure in (
                ("TOTALAMOUNTSOLD", "debt_sold_usd" if debt_only else "amount_sold_usd"),
                ("TOTALOFFERINGAMOUNT", "offering_amount_usd"),
            ):
                raw = (r.get(col) or "").replace(",", "").strip()
                if not raw.replace(".", "").isdigit() or float(raw) <= 0:
                    continue  # "Indefinite", blanks and zeros carry no number
                out.append(
                    self.obs(
                        item,
                        series_key=f"formd.{ent}.{measure}.pt",
                        entity_id=ent,
                        unit="USD",
                        as_of_date=sale,
                        published_date=filed,
                        value_numeric=float(raw),
                        tier=Tier.OFFICIAL_FILING,
                        audited_vs_reported=Basis.company_stated,
                        extraction_method=Extraction.api,
                        raw_snippet=json.dumps(
                            {
                                "accession": r["ACCESSIONNUMBER"],
                                "issuer": r["ENTITYNAME"],
                                "cik": r.get("CIK"),
                                col: raw,
                                "amendment": r.get("ISAMENDMENT"),
                                "sale_date": r.get("SALE_DATE"),
                                "filed": r.get("FILING_DATE"),
                            },
                            sort_keys=True,
                        ),
                    )
                )
        return out

    def _from_efts(self, item: RawItem) -> list[Observation]:
        # Hits only tell us a filing exists; the amounts live in the filing's primary_doc.xml, fetched by the nightly
        # once the quarter's zip lands. Until then the hit is recorded as a text observation so nothing is missed.
        try:
            hits = json.loads(item.body).get("hits", {}).get("hits", [])
        except ValueError:
            return []
        out = []
        for h in hits:
            src = h.get("_source", {})
            ciks = [c.zfill(10) for c in src.get("ciks", [])]
            ent = next((self.by_cik[c] for c in ciks if c in self.by_cik), None)
            filed = _date(src.get("file_date", ""))
            if not ent or not filed:
                continue
            out.append(
                self.obs(
                    item,
                    series_key=f"formd.{ent}.filing.pt",
                    entity_id=ent,
                    unit="filing",
                    as_of_date=filed,
                    published_date=filed,
                    value_text=f"Form D filed {filed.isoformat()} ({src.get('adsh')})",
                    tier=Tier.OFFICIAL_FILING,
                    audited_vs_reported=Basis.company_stated,
                    extraction_method=Extraction.api,
                    raw_snippet=json.dumps(
                        {k: src.get(k) for k in ("adsh", "file_date", "display_names", "ciks")},
                        sort_keys=True,
                    ),
                )
            )
        return out
