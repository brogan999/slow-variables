"""The reading path in nav.ts: every stop is a real page, in reading order, and every deep-dive prefix names a stop."""

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
NAV = (WEB / "lib" / "nav.ts").read_text()


def test_every_stop_is_a_page_in_reading_order():
    stops = re.findall(r'\{ n: "([0-9ab]+)", name: "[^"]+", href: "([^"]+)"', NAV)
    assert [n for n, _ in stops] == ["1", "2", "3", "4", "5", "6a", "6b", "7"]
    for _, href in stops:
        assert (WEB / "app" / href.strip("/") / "page.tsx").exists(), href
    parents = set(re.findall(r'\["(/[a-z/]+)", "([0-9ab]+)"\]', NAV))
    assert {n for _, n in parents} <= {n for n, _ in stops} and {h for _, h in stops} <= {h for h, _ in parents}
