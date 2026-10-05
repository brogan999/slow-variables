"""The reading path in nav.ts: every stop is a real page, in reading order, lit by its own prefix, and no deep-dive
prefix is shadowed by a broader one listed before it."""

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"
NAV = (WEB / "lib" / "nav.ts").read_text()


def test_every_stop_is_a_page_in_reading_order():
    stops = re.findall(r'\{ n: "([0-9ab]+)", name: "[^"]+", href: "([^"]+)"', NAV)
    assert [n for n, _ in stops] == ["1", "2", "3", "4", "5", "6", "7a", "7b", "8"]
    assert dict((h, n) for n, h in stops)["/firm"] == "6"  # who owns what closes the act on the money
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


def test_ask_is_switched_on_now_the_workspace_has_credit():
    assert "askOnline: true" in (WEB / "lib" / "site.ts").read_text()


def test_the_ask_side_panel_is_on_every_page_only_while_ask_is_on():
    layout = (WEB / "app" / "layout.tsx").read_text()
    assert "{SITE.askOnline ? <AskPanel /> : null}" in layout  # the root layout, so the conversation survives a route change
    assert 'pathname === "/ask"' in (WEB / "components" / "AskPanel.tsx").read_text()  # the full page needs no second chat


def test_the_side_panel_and_the_ask_page_share_one_way_of_asking_and_it_posts_only_to_the_ask_route():
    panel, chat, shared = ((WEB / "components" / f).read_text() for f in ("AskPanel.tsx", "Chat.tsx", "AskShared.tsx"))
    assert re.findall(r'fetch\(\s*"([^"]+)"', shared) == ["/api/query/ask"]
    for name, text in (("AskPanel.tsx", panel), ("Chat.tsx", chat)):
        assert "useAsk(" in text and "fetch(" not in text and "/api/" not in text, name


def test_the_side_panel_sends_nothing_until_the_reader_submits():
    panel = (WEB / "components" / "AskPanel.tsx").read_text()
    # every effect in the panel is free of a send: a question costs money, so only a submit or a click asks one
    effects = re.findall(r"useEffect\(.*?\]\);", panel, re.S)  # each runs to its dependency list
    assert len(effects) == panel.count("useEffect(") >= 6
    for effect in effects:
        assert not re.search(r"\b(send|ask|onAsk|onRetry)\(", effect), effect


def test_the_side_panel_keeps_a_bounded_checked_conversation_and_new_chat_clears_it():
    panel = (WEB / "components" / "AskPanel.tsx").read_text()
    assert 'const KEY = "ask-panel:1"' in panel  # a change to a turn's shape takes a new key, so an old store is ignored
    assert 'typeof t?.q === "string"' in panel and ".slice(-20)" in panel
    assert "sessionStorage.removeItem(KEY)" in panel  # an empty conversation leaves nothing behind
    assert re.search(r'onClick=\{\(\) => \{ reset\(\);[^}]*\}\} aria-label="New chat"', panel)
    assert 'aria-label="Go to the Ask page"' in panel and "Open in full page" not in panel  # it opens a fresh conversation


def test_the_page_makes_room_for_the_panel_only_where_its_wide_layouts_still_fit():
    css = (WEB / "app" / "globals.css").read_text()
    assert "@media (min-width: 1680px) { body:has(> .ask-panel) { padding-right: 400px; } }" in css


def test_the_privacy_notice_says_what_the_side_panel_keeps_in_the_tab():
    assert "sessionStorage" in (WEB / "components" / "AskPanel.tsx").read_text()
    legal = (WEB / "app" / "legal" / "page.tsx").read_text()
    assert "session storage" in legal and "stores nothing on your device" not in legal
    # a browser can restore or copy a tab's session, so the notice promises only the session, not erasure
    assert "kept only for this tab&apos;s session" in legal and "erases it" not in legal and "outlasts the tab" not in legal
    method = (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert "keeps nothing in your browser beyond the tab&apos;s session" in method
    assert "never stored on a server" in (WEB / "components" / "Chat.tsx").read_text()


def test_the_path_is_called_nine_stops_wherever_it_is_counted():
    said = [f for f in (WEB / "lib" / "nav.ts", WEB / "app" / "page.tsx", WEB / "components" / "Journey.tsx") if "nine stops" in f.read_text()]
    assert len(said) == 3 and not [f for f in WEB.rglob("*.ts*") if "eight stops" in f.read_text()]
