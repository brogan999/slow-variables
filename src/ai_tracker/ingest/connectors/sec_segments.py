"""Segment revenue and operating income from inline-XBRL 10-Q/10-K instances (data.sec.gov has no dimensioned facts).

Per filer: the submissions API lists recent filings; each 10-Q/10-K instance (`<primary>_htm.xml`) is parsed for facts whose
context carries one of the configured segment members. Instances never change, so they are cached by accession number.
Quarterly durations (80-100 days) become `.q` rows; fiscal years (350-380) become `.fy`; the missing Q4 is a derived metric.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime, timezone

import httpx

from ...schema import Basis, Extraction, Observation, Tier
from ..base import CACHE, Connector, RawItem, expect, ua

# entity -> {segment_id: member local name}. Add a member only after seeing it in a filing.
SEGMENTS = {
    "nvda": {
        "data_center": "nvda:DataCenterMember",
        "compute_networking": "nvda:ComputeAndNetworkingSegmentMember",
    },
    "amd": {"data_center": "amd:DataCenterMember"},
    "amzn": {"aws": "amzn:AmazonWebServicesSegmentMember"},
    "googl": {"cloud": "goog:GoogleCloudMember"},
    "msft": {"intelligent_cloud": "msft:IntelligentCloudMember"},
}
CIK = {
    "nvda": "0001045810",
    "amd": "0000002488",
    "amzn": "0001018724",
    "googl": "0001652044",
    "msft": "0000789019",
}
CONCEPTS = {
    "revenue": ["us-gaap:Revenues", "us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax"],
    "operating_income": ["us-gaap:OperatingIncomeLoss"],
}
FILINGS_PER_FILER = 9  # ~2 years of 10-Q + 10-K


class SecSegments(Connector):
    source_id = "sec_seg"
    headers = {"Accept": "application/json"}
    expect_series = ["sec_seg.nvda.data_center.revenue.q", "sec_seg.amzn.aws.operating_income.q"]

    def __init__(self, entities: list[str] | None = None) -> None:
        super().__init__()
        self.entities = entities or list(SEGMENTS)
        self.plan: list[tuple[str, str, str, date]] = []  # (entity, form, url, filed)

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        items: list[RawItem] = []
        d = CACHE / self.source_id
        d.mkdir(parents=True, exist_ok=True)
        for ent in self.entities:
            subs = httpx.get(
                f"https://data.sec.gov/submissions/CIK{CIK[ent]}.json",
                headers={"User-Agent": ua()},
                timeout=60,
            )
            subs.raise_for_status()
            r = subs.json()["filings"]["recent"]
            rows = [dict(zip(r.keys(), v)) for v in zip(*r.values())]
            picked = [x for x in rows if x["form"] in ("10-Q", "10-K")][:FILINGS_PER_FILER]
            for x in picked:
                acc = x["accessionNumber"].replace("-", "")
                url = f"https://www.sec.gov/Archives/edgar/data/{int(CIK[ent])}/{acc}/{x['primaryDocument'].replace('.htm', '_htm.xml')}"
                p = d / f"{ent}-{acc}.xml"
                if p.exists() and not refetch:
                    body = p.read_bytes()
                    retrieved = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
                else:
                    resp = httpx.get(url, headers={"User-Agent": ua()}, timeout=120)
                    resp.raise_for_status()
                    body = resp.content
                    p.write_bytes(body)
                    retrieved = datetime.now(timezone.utc)
                items.append(RawItem(url, body, 200, retrieved, hashlib.sha256(body).hexdigest(), None))
                self.plan.append((ent, x["form"], url, date.fromisoformat(x["filingDate"])))
        return items

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: dict[str, Observation] = {}
        for (ent, form, _url, filed), item in zip(self.plan, items):
            xml = item.body.decode("utf-8", "ignore")
            ctx = dict(
                re.findall(r'<(?:xbrli:)?context id="([^"]+)">(.*?)</(?:xbrli:)?context>', xml, flags=re.S)
            )
            expect({"contexts"} if ctx else set(), {"contexts"}, f"sec_seg {ent} {filed}")
            periods: dict[str, tuple[set[str], date | None, date | None]] = {}
            for cid, body in ctx.items():
                members = set(
                    re.findall(r"<(?:xbrldi:)?explicitMember[^>]*>([^<]+)</(?:xbrldi:)?explicitMember>", body)
                )
                s = re.search(r"<(?:xbrli:)?startDate>([^<]+)", body)
                e = re.search(r"<(?:xbrli:)?endDate>([^<]+)", body)
                periods[cid] = (
                    members,
                    date.fromisoformat(s.group(1)) if s else None,
                    date.fromisoformat(e.group(1)) if e else None,
                )
            for seg_id, member in SEGMENTS[ent].items():
                for measure, tags in CONCEPTS.items():
                    before = len(rows)
                    for tag in tags:
                        for cid, val in re.findall(
                            rf'<{tag}\b[^>]*contextRef="([^"]+)"[^>]*>([^<]+)</{tag}>', xml
                        ):
                            members, s, e = periods.get(cid, (set(), None, None))
                            if member not in members or not s or not e:
                                continue
                            # exactly this segment: no second dimension member beyond the consolidation marker
                            extra = members - {member, "us-gaap:OperatingSegmentsMember"}
                            if extra:
                                continue
                            days = (e - s).days
                            grain = "q" if 80 <= days <= 100 else "fy" if 350 <= days <= 380 else None
                            if not grain:
                                continue
                            key = f"sec_seg.{ent}.{seg_id}.{measure}.{grain}"
                            k = (key, e)
                            if k in rows and rows[k].published_date >= filed:
                                continue  # keep the latest filing's value for a period (restatements win)
                            rows[k] = self.obs(
                                item,
                                series_key=key,
                                unit="USD",
                                as_of_date=e,
                                period_start=s,
                                published_date=filed,
                                value_numeric=float(val.replace(",", "")),
                                entity_id=ent,
                                tier=Tier.OFFICIAL_FILING,
                                audited_vs_reported=Basis.audited if form == "10-K" else Basis.company_stated,
                                extraction_method=Extraction.xbrl,
                                raw_snippet=json.dumps(
                                    {
                                        "tag": tag,
                                        "member": member,
                                        "start": s.isoformat(),
                                        "end": e.isoformat(),
                                        "value": val,
                                        "form": form,
                                        "filed": filed.isoformat(),
                                    },
                                    sort_keys=True,
                                ),
                            )
                        if len(rows) > before:
                            break  # first concept tag that yields rows in this filing wins
        return list(rows.values())
