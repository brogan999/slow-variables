import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[1] / "web" / "src"


def test_the_legal_notice_has_a_private_address_and_is_linked_from_every_page():
    site = (WEB / "lib" / "site.ts").read_text()
    email = re.search(r'legalEmail: "([^"]*)"', site)
    assert email and re.fullmatch(r"[^@\s]+@[^@\s]+\.[a-z]{2,}", email.group(1)), "set SITE.legalEmail"
    layout = (WEB / "app" / "layout.tsx").read_text()
    assert 'href="/legal"' in layout and 'href="/legal#privacy"' in layout  # the footer is on every page
    assert '"/legal"' in (WEB / "app" / "sitemap.ts").read_text()
    page = (WEB / "app" / "legal" / "page.tsx").read_text()
    for anchor in ("operator", "advice", "forecasts", "warranty", "ai", "sources", "licences", "privacy", "liability", "general"):
        assert f'id="{anchor}"' in page, anchor
