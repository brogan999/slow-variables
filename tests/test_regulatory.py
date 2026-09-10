import json
from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.regulatory import FdaDevices, Ncsl, Owid, RlList


def _item(body: bytes, url: str = "u") -> RawItem:
    return RawItem(url, body, 200, datetime(2026, 9, 11, tzinfo=timezone.utc), "h", None)


def test_fda_cumulative_by_month_end():
    csv_body = b"\xef\xbb\xbfDate of Final Decision,Submission Number,Device,Company,Panel (Lead),Primary Product Code\n06/29/2026,K1,A,X,Radiology,QIH\n06/02/2026,K2,B,Y,Radiology,QIH\n05/15/2026,K3,C,Z,Cardio,Q\n09/29/1995,P1,OLD,W,Pathology,N\n"
    rows = {r.as_of_date: r for r in FdaDevices().extract([_item(csv_body)])}
    assert (
        rows[date(2026, 5, 31)].value_numeric == 2
        and rows[date(2026, 6, 30)].value_numeric == 4
        and rows[date(2026, 6, 30)].tier == 4
    )


def test_ncsl_counts_bills_and_enactments():
    html = b"<table><tr><th>Jurisdiction</th><th>Bill Number</th><th>Bill Status</th></tr><tr><td>Alabama</td><td>H 169</td><td>Failed - Adjourned</td></tr><tr><td>Texas</td><td>S 12</td><td>Enacted</td></tr><tr><td>Utah</td><td>HB 452</td><td>Signed by Governor</td></tr></table>"
    rows = {r.series_key: r for r in Ncsl().extract([_item(html)])}
    assert (
        rows["ncsl.us.ai_bills_introduced.a"].value_numeric == 3
        and rows["ncsl.us.ai_bills_enacted.a"].value_numeric == 2
    )
    assert rows["ncsl.us.ai_bills_introduced.a"].review_status.value == "pending"  # scraped


def test_rl_list_counts_active_commercial_vendors():
    body = json.dumps(
        {
            "meta": {"generated": "2026-07-15", "vendor_count": 3},
            "vendors": [
                {"slug": "a", "segment": "Commercial vendors", "status": {"value": "active"}},
                {"slug": "b", "segment": "Commercial vendors", "status": {"value": "acquired"}},
                {"slug": "c", "segment": "Open source", "status": {"value": "active"}},
            ],
        }
    ).encode()
    r = RlList().extract([_item(body)])[0]
    assert r.value_numeric == 1 and r.as_of_date == date(2026, 7, 15)


def test_owid_series_per_entity_and_year():
    a = b"Entity,Code,Year,Private investment in AI by region\nWorld,OWID_WRL,2025,290094148769\nChina,CHN,2013,717196154\n"
    b = b"Entity,Year,Global corporate investment in AI\nTotal,2025,489591464709\n"
    rows = {r.series_key: r for r in Owid().extract([_item(a), _item(b)])}
    assert rows["owid.world.private_ai_investment_usd.a"].value_numeric == 290094148769 and rows[
        "owid.world.private_ai_investment_usd.a"
    ].as_of_date == date(2025, 12, 31)
    assert "owid.total.corporate_ai_investment_usd.a" in rows
