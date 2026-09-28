"""The reading path in nav.ts: every stop is a real page, in reading order, lit by its own prefix, and no deep-dive
prefix is shadowed by a broader one listed before it."""

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
NAV = (WEB / "lib" / "nav.ts").read_text()


def test_every_stop_is_a_page_in_reading_order():
    stops = re.findall(r'\{ n: "([0-9ab]+)", name: "[^"]+", href: "([^"]+)"', NAV)
    assert [n for n, _ in stops] == ["1", "2", "3", "4", "5", "6a", "6b", "7"]
    for _, href in stops:
        assert (WEB / "app" / href.strip("/") / "page.tsx").exists(), href


def test_each_stop_lights_itself_and_specific_prefixes_come_first():
    stops = dict((h, n) for n, h in re.findall(r'\{ n: "([0-9ab]+)", name: "[^"]+", href: "([^"]+)"', NAV))
    parents = re.findall(r'\["(/[a-z/]+)", "([0-9ab]+)"\]', NAV)
    assert {h: n for h, n in parents if h in stops} == stops
    for i, (href, _) in enumerate(parents):
        assert not any((href + "/").startswith(p + "/") for p, _ in parents[:i]), f"{href} is shadowed"
