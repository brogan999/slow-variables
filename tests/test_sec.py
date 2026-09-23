import json
from datetime import datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.sec_xbrl import SecXbrl
from ai_tracker.schema import Basis, Entity, Membership


def fact(start, end, val, filed, frame=None, form="10-Q"):
    return {
        "start": start,
        "end": end,
        "val": val,
        "filed": filed,
        "form": form,
        **({"frame": frame} if frame else {}),
    }


def test_sec_extract(raw):
    nvda = Entity(
        id="nvda", name="NVIDIA", cik="0001045810", memberships=[Membership(layer_id="compute_physical")]
    )
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json"
    rows = SecXbrl([nvda]).extract([raw("sec_nvda_companyfacts.json", url)])
    by = {(r.series_key, r.as_of_date.isoformat()): r for r in rows}
    fy = by[("sec.nvda.gross_profit.fy", "2026-01-25")], by[("sec.nvda.revenue.fy", "2026-01-25")]
    assert abs(fy[0].value_numeric / fy[1].value_numeric - 0.711) < 0.005  # FY26 GAAP gross margin 71.1%
    assert fy[0].audited_vs_reported == Basis.audited and fy[0].tier == 4 and fy[0].grade == "A"
    q = by[("sec.nvda.revenue.q", "2026-07-26")]
    assert (
        q.audited_vs_reported == Basis.company_stated and q.period_start is not None and q.entity_id == "nvda"
    )
    assert ("sec.nvda.rpo.q", "2026-07-26") in by  # instants keep the q grain
    # year-to-date rows (no frame) never leak in: no 6-month duration for a .q series
    assert all(
        (r.as_of_date - r.period_start).days < 100
        for r in rows
        if r.series_key.endswith(".q") and r.period_start
    )


def test_a_skipped_filer_does_not_shift_the_next_filers_rows(raw):
    """A private filer's 404 is skipped in fetch; the next download must still land on its own company."""
    private = Entity(id="xai", name="xAI", cik="0002079267", memberships=[Membership(layer_id="model")])
    nvda = Entity(
        id="nvda", name="NVIDIA", cik="0001045810", memberships=[Membership(layer_id="compute_physical")]
    )
    c = SecXbrl([private, nvda])
    rows = c.extract([raw("sec_nvda_companyfacts.json", c.urls[1])])  # only NVIDIA's download came back
    assert rows and all(r.entity_id == "nvda" and r.series_key.startswith("sec.nvda.") for r in rows)


def test_year_to_date_capex_is_kept_as_h1_and_9m_and_other_measures_are_not():
    capex = [
        fact("2026-01-01", "2026-03-31", 35, "2026-04-30", "CY2026Q1"),
        fact("2026-01-01", "2026-06-30", 70, "2026-07-01"),
        fact("2026-01-01", "2026-06-30", 80, "2026-07-23"),  # a later filing of the same period wins
        fact("2025-01-01", "2025-09-30", 63, "2025-10-30"),
    ]
    revenue = [fact("2026-01-01", "2026-06-30", 190, "2026-07-23")]  # year to date, no frame: skipped
    doc = {
        "facts": {
            "us-gaap": {
                "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": capex}},
                "Revenues": {"units": {"USD": revenue}},
            }
        }
    }
    googl = Entity(
        id="googl", name="Alphabet", cik="0001652044", memberships=[Membership(layer_id="compute_physical")]
    )
    c = SecXbrl([googl])
    body = json.dumps(doc).encode()
    item = RawItem(c.urls[0], body, 200, datetime(2026, 9, 13, tzinfo=timezone.utc), "x", None)
    by = {r.series_key: r for r in c.extract([item])}
    assert by["sec.googl.capex.h1"].value_numeric == 80 and by["sec.googl.capex.9m"].value_numeric == 63
    assert by["sec.googl.capex.q"].value_numeric == 35 and not any(
        k.startswith("sec.googl.revenue") for k in by
    )


def test_alphabets_two_revenue_tags_and_microsofts_8k_recast(raw):
    """Facts from SEC's companyfacts of 22 Sep 2026. Alphabet tagged its revenue `RevenueFromContractWithCustomer...`
    from 2018 to early 2025 and `Revenues` before and since; the two agree wherever both report, so a quarter only the
    older tag carries still lands. Microsoft's 8-K recast of December 2024 re-reported FY2022 revenue and RPO at 30 June
    2024, so SEC's frame sits on the 8-K; both are read from the 10-K that reported the same dates."""
    googl = Entity(id="googl", name="Alphabet", cik="0001652044", memberships=[Membership(layer_id="model")])
    msft = Entity(id="msft", name="Microsoft", cik="0000789019", memberships=[Membership(layer_id="model")])
    c = SecXbrl([googl, msft])
    rows = c.extract(
        [raw("sec_googl_two_revenue_tags.json", c.urls[0]), raw("sec_msft_8k_recast.json", c.urls[1])]
    )
    by = {(r.series_key, r.as_of_date.isoformat()): r for r in rows}
    q3 = by[("sec.googl.revenue.q", "2019-09-30")]
    assert q3.value_numeric == 40_499_000_000 and "RevenueFromContract" in q3.raw_snippet
    # where both tags report a quarter, the one in use now leads
    assert '"Revenues"' in by[("sec.googl.revenue.q", "2019-03-31")].raw_snippet
    fy22, rpo = by[("sec.msft.revenue.fy", "2022-06-30")], by[("sec.msft.rpo.q", "2024-06-30")]
    assert (fy22.value_numeric, rpo.value_numeric) == (198_270_000_000, 275_000_000_000)
    assert all(
        '"form": "10-K"' in r.raw_snippet and r.audited_vs_reported == Basis.audited for r in (fy22, rpo)
    )


def test_a_tag_fills_only_where_it_agrees_and_a_period_no_10k_or_10q_states_is_left_out():
    docs = {
        "a": {
            "Revenues": [
                fact("2026-04-01", "2026-06-30", 10, "2026-07-30", "CY2026Q2"),
                fact("2026-01-01", "2026-03-31", 9, "2026-04-30", "CY2026Q1"),
            ],
            "RevenueFromContractWithCustomerExcludingAssessedTax": [  # differs on the quarter both report
                fact("2026-01-01", "2026-03-31", 7, "2026-04-30", "CY2026Q1"),
                fact("2025-10-01", "2025-12-31", 6, "2026-01-30", "CY2025Q4"),
            ],
            "GrossProfit": [  # an 8-K recast changed the year's number
                fact("2025-01-01", "2025-12-31", 5, "2026-02-20", form="10-K"),
                fact("2025-01-01", "2025-12-31", 4, "2026-06-01", "CY2025", form="8-K"),
            ],
            "CostOfRevenue": [
                fact("2025-01-01", "2025-12-31", 3, "2026-03-01", "CY2025", form="20-F"),
                fact(
                    "2025-10-01", "2025-12-31", 1, "2026-02-20", "CY2025Q4", form="10-K"
                ),  # a quarter: unaudited
            ],
            "RevenueRemainingPerformanceObligation": [  # an amendment is read
                {"end": "2026-03-31", "val": 2, "filed": "2026-06-01", "form": "10-Q/A", "frame": "CY2026Q1I"}
            ],
            "PaymentsToAcquirePropertyPlantAndEquipment": [
                fact("2026-04-01", "2026-06-30", 8, "2026-07-30", "CY2026Q2"),
                fact("2026-01-01", "2026-06-30", 20, "2026-07-30"),
                fact("2026-01-01", "2026-06-30", 19, "2026-08-15", form="10-Q/A"),  # restated half year
                {"end": "2025-12-31", "val": 3, "filed": "2026-02-20", "form": "10-K", "frame": "CY2025Q4I"},
            ],
            "PaymentsToAcquireProductiveAssets": [  # agrees, but capex tags never fill each other
                fact("2026-04-01", "2026-06-30", 8, "2026-07-30", "CY2026Q2"),
                fact("2026-01-01", "2026-03-31", 12, "2026-04-30", "CY2026Q1"),
            ],
            "DepreciationDepletionAndAmortization": [  # a 10-Q's trailing twelve months, framed as a year
                fact("2025-07-01", "2026-06-30", 30, "2026-07-30", "CY2026")
            ],
        },
        "b": {  # no period in common, so nothing shows the two tags measure the same thing
            "Revenues": [fact("2026-04-01", "2026-06-30", 10, "2026-07-30", "CY2026Q2")],
            "RevenueFromContractWithCustomerExcludingAssessedTax": [
                fact("2019-01-01", "2019-03-31", 1, "2019-04-30", "CY2019Q1")
            ],
        },
        "c": {  # a tag holding only six-month figures has no period of its own, so it does not lead
            "Revenues": [fact("2026-01-01", "2026-06-30", 19, "2026-07-30")],
            "RevenueFromContractWithCustomerExcludingAssessedTax": [
                fact("2026-04-01", "2026-06-30", 10, "2026-07-30", "CY2026Q2")
            ],
        },
    }
    ents = [
        Entity(id=k, name=k, cik=f"000000000{i}", memberships=[Membership(layer_id="model")])
        for i, k in enumerate(docs)
    ]
    c = SecXbrl(ents)
    items = [
        RawItem(
            url,
            json.dumps({"facts": {"us-gaap": {t: {"units": {"USD": fs}} for t, fs in d.items()}}}).encode(),
            200,
            datetime(2026, 9, 22, tzinfo=timezone.utc),
            "x",
            None,
        )
        for url, d in zip(c.urls, docs.values())
    ]
    by = {(r.series_key, r.as_of_date.isoformat()): r for r in c.extract(items)}
    assert set(by) == {
        ("sec.a.revenue.q", "2026-06-30"),
        ("sec.a.revenue.q", "2026-03-31"),
        ("sec.a.cost_of_revenue.q", "2025-12-31"),
        ("sec.a.rpo.q", "2026-03-31"),
        ("sec.a.capex.q", "2026-06-30"),
        ("sec.a.capex.h1", "2026-06-30"),
        ("sec.b.revenue.q", "2026-06-30"),
        ("sec.c.revenue.q", "2026-06-30"),
    }
    assert by[("sec.a.revenue.q", "2026-03-31")].value_numeric == 9
    assert by[("sec.a.capex.h1", "2026-06-30")].value_numeric == 19
    assert by[("sec.a.rpo.q", "2026-03-31")].audited_vs_reported == Basis.company_stated
    assert by[("sec.a.cost_of_revenue.q", "2025-12-31")].audited_vs_reported == Basis.company_stated
