from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.clouded_judgment import CloudedJudgment

RSS = b"""<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Clouded Judgement 9.4.26 - Recurrent Depth</title><link>https://ex.test/p1</link>
<pubDate>Fri, 04 Sep 2026 13:04:29 GMT</pubDate>
<content:encoded><![CDATA[<p>Overall Stats:</p><p>Overall Median: 4.4x</p><p>Top 5 Median: 31.0x</p><p>10Y: 4.8%</p>]]></content:encoded></item>
<item><title>Off-week essay</title><link>https://ex.test/p2</link><pubDate>Fri, 28 Aug 2026 13:00:00 GMT</pubDate>
<content:encoded><![CDATA[<p>No stats this week.</p>]]></content:encoded></item>
</channel></rss>"""


def test_multiples_parsed_from_full_post_body():
    rows = CloudedJudgment().extract(
        [RawItem("f", RSS, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), "h", None)]
    )
    assert [(r.series_key, r.value_numeric, r.as_of_date, r.url) for r in rows] == [
        ("clouded_judgment.saas_public.ev_ntm_revenue_median.w", 4.4, date(2026, 9, 4), "https://ex.test/p1"),
        (
            "clouded_judgment.saas_public_top5.ev_ntm_revenue_median.w",
            31.0,
            date(2026, 9, 4),
            "https://ex.test/p1",
        ),
    ]
    assert rows[0].raw_snippet.endswith("Overall Median: 4.4x") and rows[0].tier == 6
