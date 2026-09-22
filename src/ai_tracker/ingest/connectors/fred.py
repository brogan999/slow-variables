"""FRED CSV series (no key needed), as two sources: the Bick-Blandin-Deming Real-Time Population Survey's genAI
series (`fred`), and official statistics the adaptation stage reads as context (`fred_official`: power-plant output,
real output, hours, pay, jobs by sector), each credited to its own authors."""

from __future__ import annotations

import csv
import io
from datetime import date, timedelta

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, series_key
from .ramp import month_end

# id -> (series suffix, unit, multiplier, divisor, tier, grain). RPS is a survey run by Fed economists and hosted on FRED: tier 6.
# The rest are official statistics (the Fed, BEA, BLS): tier 4. A monthly series lands at month end and a quarterly
# one at quarter end, each with its period start, so three months never collide on one date. The two numbers turn the
# published unit into the stored one (percent to share, thousands of jobs to jobs, billions of dollars to dollars); a
# multiplier and a divisor, not one float, so a percent series stores exactly what it always stored.
OFFICIAL = Tier.OFFICIAL_FILING
SERIES = {
    "RPSGENAIASSISTWRKHRSALL": ("us_workers.hours_assisted_share", "share", 1, 100, Tier.PUBLISHED_ANALYSIS, "q"),
    "RPSGENAIUSAGESHARELWWORK": ("us_workers.work_use_weekly_share", "share", 1, 100, Tier.PUBLISHED_ANALYSIS, "q"),
    "RPSGENAIUSAGESHAREALL": ("us_adults.any_use_share", "share", 1, 100, Tier.PUBLISHED_ANALYSIS, "q"),
    "RPSGENAIUSAGESHARELWALL": ("us_adults.use_last_week_share", "share", 1, 100, Tier.PUBLISHED_ANALYSIS, "q"),
    "IPG22111S": ("us.electric_power_generation", "index", 1, 1, OFFICIAL, "m"),  # power plants (NAICS 22111), 2017 = 100
    "GDPC1": ("us.real_gdp", "USD", 10**9, 1, OFFICIAL, "q"),  # chained 2017 dollars, annual rate
    "A939RX0Q048SBEA": ("us.real_gdp_per_capita", "USD", 1, 1, OFFICIAL, "q"),  # chained 2017 dollars
    "AWHAEPBS": ("us.weekly_hours_professional_business", "hours", 1, 1, OFFICIAL, "m"),
    "LES1252881600Q": ("us.median_real_weekly_earnings", "USD", 1, 1, OFFICIAL, "q"),  # full-time, 1982-84 dollars
    "USEHS": ("us.jobs_education_health", "jobs", 1000, 1, OFFICIAL, "m"),
    "USLAH": ("us.jobs_leisure_hospitality", "jobs", 1000, 1, OFFICIAL, "m"),
    "PAYEMS": ("us.jobs_nonfarm", "jobs", 1000, 1, OFFICIAL, "m"),
}
START = "2015-01-01"  # the official histories run back decades; the site reads them from here
REAL = {  # the price base of a series in constant dollars, carried on each row so a page never prints it as plain dollars
    "GDPC1": "In chained 2017 dollars, at an annual rate",
    "A939RX0Q048SBEA": "In chained 2017 dollars",
    "LES1252881600Q": "In 1982-84 dollars",
}


def quarter_end(d: date) -> date:
    m = ((d.month - 1) // 3 + 1) * 3
    first_next = date(d.year + (m == 12), 1 if m == 12 else m + 1, 1)
    return first_next - timedelta(days=1)


def _url(sid: str) -> str:
    base = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
    return base if SERIES[sid][4] != OFFICIAL else f"{base}&cosd={START}"


SURVEY_IDS = [sid for sid, s in SERIES.items() if s[4] != OFFICIAL]
OFFICIAL_IDS = [sid for sid, s in SERIES.items() if s[4] == OFFICIAL]


class Fred(Connector):
    source_id = "fred"
    ids = SURVEY_IDS
    urls = [_url(sid) for sid in SURVEY_IDS]
    expect_series = ["fred.us_workers.hours_assisted_share.q", "fred.us_adults.any_use_share.q"]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        out: list[RawItem] = []
        for url in self.urls:
            try:  # one failing series must not stop the rest
                out.append(self.fetch_one(url, day, refetch))
            except Exception as e:
                self.errors.append(f"{url}: {type(e).__name__}: {e}")
        return out

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: list[Observation] = []
        by_url = {_url(sid): sid for sid in self.ids}  # paired by URL: a skipped series must not shift the next
        for item in items:
            sid = by_url[item.url]
            suffix, unit, mul, div, tier, grain = SERIES[sid]
            recs = list(csv.DictReader(io.StringIO(item.body.decode("utf-8", "ignore"))))
            expect(set(recs[0]) if recs else set(), {"observation_date", sid}, f"fred {sid}")
            for r in recs:
                if r[sid] in (".", "", None):
                    continue
                start = date.fromisoformat(r["observation_date"])
                rows.append(
                    self.obs(
                        item,
                        series_key=series_key("fred", *suffix.split("."), grain),
                        unit=unit,
                        as_of_date=month_end(r["observation_date"]) if grain == "m" else quarter_end(start),
                        period_start=start,
                        value_numeric=float(r[sid]) * mul / div,
                        tier=tier,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{sid} {r['observation_date']},{r[sid]}",
                        note=REAL.get(sid),
                    )
                )
        return rows


class FredOfficial(Fred):
    """The same fetch and reading for official statistics, under their own source so each figure credits the
    agencies that publish them: the Federal Reserve Board, the Bureau of Economic Analysis and the Bureau of Labor
    Statistics. Tier 4."""

    source_id = "fred_official"
    ids = OFFICIAL_IDS
    urls = [_url(sid) for sid in OFFICIAL_IDS]
    expect_series = ["fred.us.real_gdp.q", "fred.us.jobs_nonfarm.m"]
