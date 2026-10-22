"""The private area: a login guards it, its content is fetched at request time from a store outside this
repository, and nothing public lists it, indexes it or names what it holds. Every fixture here is invented."""

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
AREA = WEB / "app" / "private"
LIB = WEB / "lib" / "private.ts"
BUNDLER = ROOT / "scripts" / "private_bundle.py"
HASHER = ROOT / "web" / "scripts" / "private-hash.mjs"
RUNBOOK = ROOT / "docs" / "private-area.md"
SECRETS = ("PRIVATE_PASSWORD_HASH", "PRIVATE_SESSION_SECRET", "PRIVATE_CONTENT_REPO", "PRIVATE_CONTENT_TOKEN")
MARK = "ZEBRA-FIXTURE-7"


def _body(text: str, name: str) -> str:
    """One exported function's source, up to the next export."""
    return re.split(r"\nexport ", re.split(rf"function {name}[(<]", text, maxsplit=1)[1], maxsplit=1)[0]


# the lock


def test_the_lock_is_server_only_and_checks_the_session_before_it_fetches():
    text = LIB.read_text()
    assert text.startswith('import "server-only"')
    load = _body(text, "load")
    assert "session(" in load and "fetch(" in load
    assert load.index("session(") < load.index("fetch(")
    assert "timingSafeEqual" in text and "scryptSync" in text and "createHmac" in text
    assert 'cache: "no-store"' in load


def test_the_area_does_not_exist_until_all_four_settings_are_present():
    configured = _body(LIB.read_text(), "configured")
    for name in SECRETS:
        assert name in configured, name
    layout = (AREA / "layout.tsx").read_text()
    assert 'export const dynamic = "force-dynamic"' in layout
    assert re.search(r"if \(!configured\(\)\) notFound\(\)", layout)
    # a layout does not stop its pages from rendering (Next's own guide), so each page and the route ask as well
    for f in [*AREA.rglob("page.tsx"), AREA / "session" / "route.ts"]:
        assert re.search(r"if \(!configured\(\)\) notFound\(\)", f.read_text()), f


def test_only_the_lock_reads_the_settings():
    names = (*SECRETS, "PRIVATE_CONTENT_BASE")
    for f in WEB.rglob("*.ts*"):
        if f != LIB:
            assert not any(n in f.read_text() for n in names), f
    assert all(n in LIB.read_text() for n in names)


def test_the_local_test_store_is_ignored_on_the_live_host():
    assert "process.env.VERCEL ? undefined : process.env.PRIVATE_CONTENT_BASE" in LIB.read_text()
    assert LIB.read_text().count("PRIVATE_CONTENT_BASE") == 1


def test_the_cookie_is_http_only_scoped_to_the_area_and_secure_on_the_live_host():
    text = LIB.read_text()
    assert '"__Secure-sv_private"' in text and '"sv_private"' in text
    issue = _body(text, "issue")
    for want in ("httpOnly: true", 'sameSite: "lax"', 'path: "/private"', "secure:"):
        assert want in issue, want


def test_every_page_but_the_login_asks_for_a_session():
    pages = list(AREA.rglob("page.tsx"))
    assert len(pages) >= 3
    for p in pages:
        if p.parent.name != "login":
            assert re.search(r"\b(session|load)(<[^>]+>)?\(", p.read_text()), p


def test_signing_in_is_a_post_from_this_site_that_answers_with_a_redirect():
    route = (AREA / "session" / "route.ts").read_text()
    assert re.findall(r"export async function (\w+)", route) == ["POST"]
    assert '"origin"' in route and "verify(" in route and "issue(" in route and "303" in route
    login = (AREA / "login" / "page.tsx").read_text()
    assert 'action="/private/session"' in login and 'method="post"' in login and 'type="password"' in login
    assert "Not recognised." in login


def test_links_inside_the_area_are_never_fetched_ahead():
    for f in AREA.rglob("*.tsx"):
        text = f.read_text()
        assert text.count("<Link ") == text.count("<Link prefetch={false} "), f


def test_a_failure_inside_the_area_prints_nothing_about_it():
    text = (AREA / "error.tsx").read_text()
    assert text.startswith('"use client"') and "error." not in text and "{error" not in text


# nothing public points at it


def test_no_list_of_pages_names_the_area():
    for f in ("app/sitemap.ts", "app/search.json/route.ts", "lib/nav.ts", "lib/contents.ts", "app/robots.ts"):
        assert "/private" not in (WEB / f).read_text(), f


def test_the_area_is_never_indexed_and_never_cached():
    config = (ROOT / "web" / "next.config.ts").read_text()
    block = config.split('source: "/private/:path*"', 1)[1].split("]", 1)[0]
    assert '{ key: "X-Robots-Tag", value: "noindex, nofollow" }' in block
    assert '{ key: "Cache-Control", value: "private, no-store" }' in block
    assert "frame-ancestors 'none'" in config and "form-action 'self'" in config  # the site's policy is not loosened
    layout = (AREA / "layout.tsx").read_text()
    assert "robots: { index: false, follow: false }" in layout
    assert "Private. Not public." in layout
    assert "Drafted by Claude, a model made by Anthropic. Anthropic buys from, sells to or competes with companies that may be named here." in layout


def test_the_ask_panel_is_absent_from_the_area():
    panel = (WEB / "components" / "AskPanel.tsx").read_text()
    assert 'if (pathname === "/ask" || pathname.startsWith("/private")) return null;' in panel


def test_the_foot_of_a_private_page_offers_no_way_back_to_the_path():
    assert '["/ask", "/legal", "/private"]' in (WEB / "components" / "Journey.tsx").read_text()


# the bundler


def _bundle(src: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(BUNDLER), str(src), str(out)], capture_output=True, text=True, cwd=ROOT)


def _source(tmp_path: Path) -> Path:
    src = tmp_path / "source"
    (src / "notes").mkdir(parents=True)
    (src / "bundle.yaml").write_text(
        """
sections:
  - slug: example
    title: Example section
    documents:
      - {slug: first, title: First page, kind: doc, source: notes/first.md}
      - {slug: second, title: Second page, kind: doc, source: notes/second.md}
  - slug: other
    title: Other section
    documents:
      - {slug: rows, title: Example rows, kind: table, source: rows.csv, columns: [name, colour, size], filters: [colour]}
"""
    )
    (src / "notes" / "first.md").write_text(
        f"""# First page

{MARK} opens with **bold**, *italics* and `code`, then <script>alert("x")</script> in the text.

## A heading

#### A small heading

| Left | Right |
| --- | --- |
| one | <b>two</b> |

```
if a < b:
    print("<script>")
```

1. step one
2. step two

> a quoted line

See [the second page](second.md), [the rows](../rows.csv), [nowhere](missing.md) and [a site](https://example.com/a"onmouseover="x).
"""
    )
    (src / "notes" / "second.md").write_text(f"{MARK} is all the second page says.\n")
    (src / "rows.csv").write_text(
        "name,colour,size,unlisted\n" + "".join(f"{MARK}-{i},{'red' if i % 2 else 'blue'},{i},x\n" for i in range(6))
    )
    return src


def test_the_bundler_refuses_to_write_inside_the_repository(tmp_path):
    inside = ROOT / "web" / "public" / "bundle-refused"
    r = _bundle(_source(tmp_path), inside)
    assert r.returncode != 0 and "refused" in r.stderr
    assert not inside.exists()


def test_the_private_files_name_no_home_folder_and_no_private_path():
    files = [*AREA.rglob("*.ts*"), LIB, BUNDLER, HASHER, RUNBOOK]
    assert len(files) >= 10
    for f in files:
        for banned in ("~/", "/Users/"):
            assert banned not in f.read_text(), (f, banned)
    assert "docs/private" not in BUNDLER.read_text()


def test_the_bundler_writes_a_manifest_and_one_file_for_each_document(tmp_path):
    out = tmp_path / "out"
    r = _bundle(_source(tmp_path), out)
    assert r.returncode == 0, r.stderr
    manifest = json.loads((out / "manifest.json").read_text())
    assert [(s["slug"], s["title"]) for s in manifest["sections"]] == [("example", "Example section"), ("other", "Other section")]
    docs = [d for s in manifest["sections"] for d in s["documents"]]
    assert [(d["slug"], d["title"], d["kind"]) for d in docs] == [("first", "First page", "doc"), ("second", "Second page", "doc"), ("rows", "Example rows", "table")]
    for d in docs:
        assert re.fullmatch(r"[a-z0-9-]+\.json", d["file"]) and (out / d["file"]).exists(), d
    assert sorted(p.name for p in out.iterdir()) == sorted(["manifest.json", *(d["file"] for d in docs)])
    assert MARK not in (out / "manifest.json").read_text()  # the list of pages carries titles, never a page's text


def test_the_bundler_escapes_everything_and_renders_the_marks(tmp_path):
    out = tmp_path / "out"
    assert _bundle(_source(tmp_path), out).returncode == 0
    manifest = json.loads((out / "manifest.json").read_text())
    first = json.loads((out / manifest["sections"][0]["documents"][0]["file"]).read_text())
    html = first["html"]
    assert first["title"] == "First page" and "<h1>" not in html  # the title is drawn once, by the page
    assert "<script" not in html and "&lt;script&gt;alert(" in html and "<b>" not in html
    assert "<strong>bold</strong>" in html and "<em>italics</em>" in html and "<code>code</code>" in html
    assert "<h2>A heading</h2>" in html and "<h4>A small heading</h4>" in html
    assert "<table" in html and "<th>Left</th>" in html and "<td>one</td>" in html and "&lt;b&gt;two&lt;/b&gt;" in html
    assert "<pre><code>if a &lt; b:\n    print(" in html and "```" not in html
    assert "<ol><li>step one</li><li>step two</li></ol>" in html
    assert "<blockquote>a quoted line</blockquote>" in html
    assert '<a href="/private/example/second">the second page</a>' in html
    assert '<a href="/private/other/rows">the rows</a>' in html
    assert "missing.md" in html and 'href="missing.md"' not in html  # a link to nothing in the spec stays text
    assert 'rel="nofollow noopener" href="https://example.com/a' in html
    assert "onmouseover=" not in re.sub(r"&quot;onmouseover=", "", html)  # a quote in an address cannot open an attribute


def test_the_bundler_builds_a_table_from_a_csv_with_its_declared_filters(tmp_path):
    out = tmp_path / "out"
    assert _bundle(_source(tmp_path), out).returncode == 0
    manifest = json.loads((out / "manifest.json").read_text())
    table = json.loads((out / manifest["sections"][1]["documents"][0]["file"]).read_text())
    assert table["title"] == "Example rows"
    assert table["columns"] == ["name", "colour", "size"] and table["filters"] == ["colour"]
    assert len(table["rows"]) == 6 and table["rows"][1] == [f"{MARK}-1", "red", "1"]


def test_the_bundler_refuses_a_slug_that_is_not_plain_and_a_filter_that_is_not_a_column(tmp_path):
    src = _source(tmp_path)
    spec = (src / "bundle.yaml").read_text()
    (src / "bundle.yaml").write_text(spec.replace("slug: second", "slug: ../second"))
    assert "slug" in _bundle(src, tmp_path / "a").stderr
    (src / "bundle.yaml").write_text(spec.replace("filters: [colour]", "filters: [weight]"))
    assert "filter" in _bundle(src, tmp_path / "b").stderr


def test_the_table_is_filtered_on_the_server_and_opens_on_one_value():
    page = (AREA / "[section]" / "[[...slug]]" / "page.tsx").read_text()
    assert '"use client"' not in page and "searchParams" in page and 'method="get"' in page and "<select" in page
    assert "{shown.length}" in page  # the count is the length of what is shown, not arithmetic
    assert "dangerouslySetInnerHTML" in page and "prose-folio" in page


# the hashing script and the runbook


def test_the_hashing_script_reads_stdin_and_matches_the_lock(tmp_path):
    text = HASHER.read_text()
    assert "process.argv" not in text and "scryptSync" in text and text.count("console.log(") == 1
    r = subprocess.run(["node", str(HASHER)], input="an invented pass phrase\n", capture_output=True, text=True)
    assert r.returncode == 0 and re.fullmatch(r"[0-9a-f]{32}:[0-9a-f]{128}\n", r.stdout), r.stdout + r.stderr
    assert "64" in _body(LIB.read_text(), "verify") or "length" in _body(LIB.read_text(), "verify")


def test_the_runbook_warns_about_preview_and_the_plan_records_the_part():
    text = RUNBOOK.read_text()
    for name in SECRETS:
        assert name in text, name
    assert re.search(r"\*\*[^*]*Preview[^*]*\*\*", text)
    assert "Production" in text and "rotate" in text.lower()
    plan = (ROOT / "docs" / "plan.md").read_text()
    assert "## Part 59 (13 Oct 2026): a private area behind a login" in plan


def test_a_line_that_opens_with_a_bar_but_is_no_table_is_a_paragraph_not_a_hang(tmp_path):
    src = _source(tmp_path)
    (src / "notes" / "second.md").write_text("| a lone bar, with no rule beneath it\n\nthen a paragraph\n")
    r = subprocess.run([sys.executable, str(BUNDLER), str(src), str(tmp_path / "out")], capture_output=True, text=True, timeout=20)
    assert r.returncode == 0, r.stderr
    assert "a lone bar" in (tmp_path / "out" / "example--second.json").read_text()


# figures: a document may carry inline drawings, checked against a short list of drawing elements


FIGURE = (
    '<svg viewBox="0 0 100 40" width="100%" role="img" xmlns="http://www.w3.org/2000/svg" aria-labelledby="t">'
    '<title id="t">An invented chart</title><rect x="0" y="0" width="50" height="20" fill="var(--slow, #00897b)" rx="2"/>'
    f'<g><title>a tile</title><text x="2" y="12" font-size="11" fill="var(--ink)">{MARK}</text></g>'
    '<line x1="0" y1="0" x2="10" y2="10" stroke="var(--axis)"/></svg>'
)


def _figured(tmp_path: Path, svg: str) -> Path:
    src = _source(tmp_path)
    (src / "notes" / "chart.svg").write_text(svg)
    spec = (src / "bundle.yaml").read_text()
    (src / "bundle.yaml").write_text(spec.replace("source: notes/first.md}", "source: notes/first.md, figures: [notes/chart.svg]}"))
    return src


def test_a_document_carries_its_figures_as_checked_inline_drawings(tmp_path):
    out = tmp_path / "out"
    r = _bundle(_figured(tmp_path, FIGURE), out)
    assert r.returncode == 0, r.stderr
    first = json.loads((out / "example--first.json").read_text())
    assert first["figures"] == [FIGURE]
    assert "figures" not in json.loads((out / "example--second.json").read_text())


def test_a_figure_that_could_run_or_fetch_anything_is_refused(tmp_path):
    for i, bad in enumerate([
        FIGURE.replace("</svg>", "<script>alert(1)</script></svg>"),
        FIGURE.replace("<rect ", '<rect onclick="alert(1)" '),
        FIGURE.replace("</svg>", '<a href="https://example.com"><text>x</text></a></svg>'),
        FIGURE.replace("</svg>", "<foreignObject><div>x</div></foreignObject></svg>"),
        FIGURE.replace('fill="var(--slow, #00897b)"', 'fill="url(https://example.com/x)"'),
        FIGURE.replace("<rect ", '<rect style="background:url(x)" '),
        "<div>not a drawing</div>",
    ]):
        r = _bundle(_figured(tmp_path / str(i), bad), tmp_path / f"out{i}")
        assert r.returncode != 0 and "refused" in r.stderr, (i, r.stderr)


def test_a_figure_outside_the_source_folder_is_refused(tmp_path):
    src = _figured(tmp_path, FIGURE)
    spec = (src / "bundle.yaml").read_text()
    (src / "bundle.yaml").write_text(spec.replace("figures: [notes/chart.svg]", "figures: [../elsewhere.svg]"))
    (tmp_path / "elsewhere.svg").write_text(FIGURE)
    r = _bundle(src, tmp_path / "out")
    assert r.returncode != 0 and "refused" in r.stderr


def test_the_page_draws_a_documents_figures_full_width_above_its_text():
    page = (AREA / "[section]" / "[[...slug]]" / "page.tsx").read_text()
    assert "body.figures" in page
    assert page.index("body.figures") < page.index("prose-folio")
