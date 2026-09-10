from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.feeds import Feeds, parse_feed

RSS = b"""<rss version="2.0"><channel><title>x</title>
<item><title><![CDATA[Research acceleration: The view inside OpenAI]]></title><link>https://ex.test/a</link>
<description><![CDATA[Early data on <b>agent</b> usage.]]></description><pubDate>Sun, 06 Sep 2026 08:00:00 GMT</pubDate></item>
<item><title>Unrelated launch</title><link>https://ex.test/b</link><description>x</description><pubDate>Mon, 07 Sep 2026 08:00:00 GMT</pubDate></item>
</channel></rss>"""
ATOM = b"""<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Tracking recursive self-improvement</title>
<link href="https://ex.test/c"/><published>2026-08-14T00:00:00Z</published><summary>funding</summary></entry></feed>"""


def _feeds(tmp_path):
    p = tmp_path / "sources.yaml"
    p.write_text(
        "sources:\n"
        "  - {id: f1, name: f1, org: o, url: 'https://ex.test/rss', kind: rss, default_tier: 7, cadence: irregular, lens: both,"
        " connector: feeds, watch: {research_acceleration: 'research acceleration|agent-workday'}}\n"
        "  - {id: f2, name: f2, org: o, url: 'https://ex.test/atom', kind: rss, default_tier: 6, cadence: irregular, lens: both,"
        " connector: feeds, watch: {self_improvement: 'self-improv'}}\n"
    )
    return Feeds(p)


def _item(url, body):
    return RawItem(url, body, 200, datetime(2026, 9, 10, tzinfo=timezone.utc), "h", None)


def test_feed_matches_become_text_observations(tmp_path):
    rows = _feeds(tmp_path).extract([_item("https://ex.test/rss", RSS), _item("https://ex.test/atom", ATOM)])
    assert [(r.series_key, r.url, r.as_of_date, r.tier) for r in rows] == [
        ("watch.f1.research_acceleration.pt", "https://ex.test/a", date(2026, 9, 6), 7),
        ("watch.f2.self_improvement.pt", "https://ex.test/c", date(2026, 8, 14), 6),
    ]
    assert (
        rows[0].value_text == "Research acceleration: The view inside OpenAI"
        and rows[0].review_status.value == "approved"
    )


def test_empty_feed_is_an_error_not_silence(tmp_path):
    c = _feeds(tmp_path)
    assert c.extract(
        [_item("https://ex.test/rss", b"<rss><channel/></rss>"), _item("https://ex.test/atom", ATOM)]
    )
    assert c.errors == ["f1: feed parsed to 0 posts"] and parse_feed(b"<rss><channel/></rss>") == []
