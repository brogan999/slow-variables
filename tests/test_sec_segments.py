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
