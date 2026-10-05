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


ROOT = WEB.parents[1]


def _contents() -> str:
    return (WEB / "lib" / "contents.ts").read_text()


def test_every_page_has_a_contents_entry_that_says_what_question_it_answers():
    text = _contents()
    entries = dict(re.findall(r'^\s*"(/[a-z/-]*)": \{ name: "[^"]+", question: "([^"]+\?)"', text, re.M))
    pages = [p.parent.relative_to(WEB / "app").as_posix() for p in (WEB / "app").rglob("page.tsx")]
    static = {"/" + ("" if p == "." else p) for p in pages if "[" not in p}
    assert static - {"/contents"} == set(entries), sorted(static - {"/contents"} ^ set(entries))
    # a page made once per record is described on the page that lists them
    for p in pages:
        if "[" in p:
            assert f'"/{p.split("[")[0]}' in text, f"no contents entry mentions /{p}"


def test_every_section_the_contents_page_links_to_exists():
    sources = "".join(f.read_text() for f in (WEB).rglob("*.tsx")) + "".join(f.read_text() for f in [*(ROOT / "seed").glob("*.yaml"), *(ROOT / "docs" / "argument").glob("*.md")])
    anchors = re.findall(r'\["([a-z0-9_-]+)", "[^"]+", "[^"]+\?"\]', _contents())
    assert len(anchors) > 40
    words = " ".join(re.sub(r"[^a-z0-9]+", " ", sources.lower()).split())  # an essay's anchor is its folio label, slugged
    for a in anchors:
        stem = re.sub(r"^(folio|vc)-", "", a)
        assert f'"{a}"' in sources or re.search(rf"\b{re.escape(stem)}\b", sources) or f" {stem.replace('-', ' ')} " in f" {words} ", a


def test_the_contents_page_is_one_click_from_every_page():
    assert '["/contents", "Contents"]' in NAV  # the menu, the search box and sitemap.xml all read this list
    assert 'href="/contents"' in (WEB / "app" / "layout.tsx").read_text()  # the footer
