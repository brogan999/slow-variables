import re
from datetime import date

from ai_tracker.ingest.connectors.sec_segments import SecSegments


def test_segment_facts_by_grain_and_form(raw):
    c = SecSegments()
    from dataclasses import replace

    item = raw("sec_seg_min.xml")
    body = item.body.decode()
    q_only = replace(item, body=re.sub(r'<context id="c_fy">.*?</context>\n', "", body, flags=re.S).encode())
    fy_only = replace(
        item, body=re.sub(r'<context id="c_(q|two)">.*?</context>\n', "", body, flags=re.S).encode()
    )
    c.plan = [("nvda", "10-Q", item.url, date(2026, 8, 27)), ("nvda", "10-K", item.url, date(2026, 2, 25))]
    rows = {r.series_key: r for r in c.extract([q_only, fy_only])}
    q = rows["sec_seg.nvda.data_center.revenue.q"]
    assert q.value_numeric == 41.1e9 and q.period_start == date(2026, 4, 27) and q.entity_id == "nvda"
    assert q.audited_vs_reported.value == "company_stated" and q.published_date == date(2026, 8, 27)
    fy = rows["sec_seg.nvda.data_center.revenue.fy"]
    assert fy.value_numeric == 150e9 and fy.audited_vs_reported.value == "audited"
    assert not any(
        "30000000000" in r.raw_snippet for r in rows.values()
    )  # two-dimension contexts are not the segment


def test_customer_revenue_shares_are_kept_per_customer_and_receivables_are_not(raw):
    c = SecSegments()
    item = raw("sec_seg_min.xml")
    c.plan = [("nvda", "10-Q", item.url, date(2026, 8, 27))]
    rows = {r.series_key: r for r in c.extract([item])}
    share = rows["sec_seg.nvda.customer_revenue_share.revenuecustomer1.q"]
    assert share.value_numeric == 0.16 and share.unit == "share" and share.as_of_date == date(2026, 7, 26)
    assert not any(
        "0.23" in r.raw_snippet for r in rows.values()
    )  # a receivables share is not a revenue share


def test_real_nvidia_10k_reproduces_the_ledger_rows():
    import gzip
    import hashlib
    from datetime import datetime, timezone
    from pathlib import Path

    from ai_tracker.ingest.base import RawItem

    body = gzip.decompress((Path(__file__).parent / "fixtures" / "sec_seg_nvda_10k_fy26.xml.gz").read_bytes())
    url = "https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125_htm.xml"
    item = RawItem(
        url, body, 200, datetime(2026, 9, 9, tzinfo=timezone.utc), hashlib.sha256(body).hexdigest(), None
    )
    c = SecSegments()
    c.plan = [("nvda", "10-K", url, date(2026, 2, 25))]
    rows = {(r.series_key, r.as_of_date): r for r in c.extract([item])}
    fy = rows[("sec_seg.nvda.data_center.revenue.fy", date(2026, 1, 25))]
    assert fy.value_numeric == 193_737_000_000 and fy.period_start == date(2025, 1, 27)
    assert fy.audited_vs_reported.value == "audited" and fy.id == "10682b11aa2ab089"  # the id stored in data/
    assert (
        rows[("sec_seg.nvda.customer_revenue_share.customerone.fy", date(2026, 1, 25))].value_numeric == 0.22
    )
