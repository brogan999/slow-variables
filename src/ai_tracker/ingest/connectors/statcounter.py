"""StatCounter Global Stats, AI chatbot market share (CC BY-SA 3.0; credit with a link): each month, each chatbot's
share of the visits that AI chatbots refer to the websites StatCounter tracks, worldwide. It measures referral
traffic, not use. Tier 3: a measurement network's reading of product behaviour. Only finished months are read: the
month in progress moves until it ends."""

from __future__ import annotations

import csv
import io
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, series_key
from .ramp import month_end

URL = (
    "https://gs.statcounter.com/chart.php?device_hidden=desktop%2Bmobile%2Btablet%2Bconsole&statType_hidden=ai_chatbot"
    "&region_hidden=ww&granularity=monthly&statType=AI%20Chatbot&region=Worldwide&fromInt=202504&toInt={to}"
    "&fromMonthYear=2025-04&toMonthYear={to_iso}&csv=1"
)


class StatCounterAI(Connector):
    source_id = "statcounter_ai"
    kind = "csv"
    optional = True
    expect_series = ["statcounter_ai.chatgpt.referral_share.m"]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        return [self.fetch_one(URL.format(to=day.strftime("%Y%m"), to_iso=day.strftime("%Y-%m")), day, refetch)]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item in items:
            rows = list(csv.DictReader(io.StringIO(item.body.decode("utf-8-sig"))))
            expect(set(rows[0]) if rows else set(), {"Date", "ChatGPT", "Claude", "Google Gemini"}, "statcounter ai chatbot csv")
            running = item.retrieved_at.strftime("%Y-%m")
            for r in rows:
                if r["Date"] >= running:  # the month in progress, and any month StatCounter has not reached
                    continue
                for name, v in r.items():
                    if name in ("Date", "Other") or v in ("", None) or float(v) == 0:
                        continue
                    out.append(
                        self.obs(
                            item,
                            series_key=series_key("statcounter_ai", name, "referral_share", "m"),
                            unit="share",
                            as_of_date=month_end(f"{r['Date']}-01"),
                            value_numeric=float(v) / 100,
                            tier=Tier.PRODUCT_BEHAVIOUR,
                            audited_vs_reported=Basis.reported,
                            extraction_method=Extraction.api,
                            raw_snippet=f"{r['Date']} {name} {v}%",
                        )
                    )
        return out
