"""Build the bundle the site's private area reads (plan Part 59). Generic: it names no document.

    uv run python scripts/private_bundle.py <source folder> <output folder>

The source folder is outside the repository and holds bundle.yaml, a spec its owner keeps there:

    sections:
      - slug: example
        title: Example section
        documents:
          - {slug: first, title: First page, kind: doc, source: notes/first.md}
          - {slug: rows, title: Example rows, kind: table, source: rows.csv, columns: [name, colour], filters: [colour]}
          - {slug: drawn, title: A page with a chart, kind: doc, source: notes/drawn.md, figures: [notes/chart.svg]}

This writes manifest.json (sections and titles, no text) and one JSON file for each document into the output
folder, which is a clone of the private store the site fetches from. A doc is markdown turned into escaped HTML;
a link from one listed document to another becomes that document's address on the site. A table is a CSV's
declared columns as rows of text. A doc's figures are SVG files carried whole, after a check that they hold only
drawing elements and nothing that can run, link or fetch; the page draws them full width above the text. It refuses to
write inside the repository.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data_market_private import markdown  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9][a-z0-9-]*")
FENCE = re.compile(r"^```[^\n]*\n(.*?)^```[ \t]*$", re.S | re.M)
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s#]+)(#[^)\s]*)?\)")


def html(text: str, here: Path, urls: dict[Path, str]) -> str:
    """Markdown as escaped HTML: the shared renderer between fenced code blocks, then links between documents."""

    def link(m: re.Match) -> str:
        url = urls.get((here.parent / m.group(2)).resolve())
        return f'<a href="{url}{m.group(3) or ""}">{m.group(1)}</a>' if url else m.group(0)

    out = []
    for i, part in enumerate(FENCE.split(re.sub(r"\A\s*# .*\n", "", text))):  # the page draws the title itself
        if i % 2:
            out.append(f"<pre><code>{escape(part.rstrip())}</code></pre>")
        elif part.strip():
            body = LINK.sub(link, markdown(part)).replace("<table>", '<table class="data">')
            out.append(body.replace('<a href="http', '<a rel="nofollow noopener" href="http'))
    return "\n".join(out)


# a figure may hold only these elements and attributes; anything else, and any value that could fetch or run, is refused
DRAWING = {"svg", "g", "rect", "line", "path", "circle", "text", "tspan", "title", "desc"}
ATTRS = {
    "viewBox", "width", "height", "role", "id", "aria-labelledby", "aria-label", "style", "x", "y", "x1", "y1", "x2",
    "y2", "cx", "cy", "r", "rx", "d", "fill", "stroke", "stroke-width", "opacity", "font-size", "font-weight",
    "font-family", "text-anchor", "dominant-baseline", "transform",
}
UNSAFE = re.compile(r"url\(|javascript:|expression\(|@import", re.I)


def figure(path: Path) -> str:
    text = path.read_text()
    if "<!" in text:
        sys.exit(f"refused: {path.name} carries a declaration or comment")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        sys.exit(f"refused: {path.name} is not well-formed: {e}")
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag not in DRAWING or (el is root) != (tag == "svg"):
            sys.exit(f"refused: {path.name} holds an element that is not a drawing: {tag}")
        for name, value in el.attrib.items():
            if "}" in name or name not in ATTRS or UNSAFE.search(value):
                sys.exit(f"refused: {path.name} has an attribute that is not allowed: {name}")
    return text


def table(path: Path, doc: dict) -> dict:
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        columns = doc.get("columns") or list(reader.fieldnames or [])
        filters = doc.get("filters") or []
        if missing := [c for c in columns if c not in (reader.fieldnames or [])]:
            sys.exit(f"refused: {doc['slug']} lists a column the file does not have: {missing}")
        if missing := [c for c in filters if c not in columns]:
            sys.exit(f"refused: {doc['slug']} lists a filter that is not one of its columns: {missing}")
        rows = [[(r.get(c) or "").strip() for c in columns] for r in reader]
    return {"title": doc["title"], "columns": columns, "rows": rows, "filters": filters}


def main(args: list[str]) -> None:
    src, out = Path(args[0]).resolve(), Path(args[1]).resolve()
    if out.is_relative_to(ROOT):
        sys.exit("refused: the bundle must be written outside the repository")
    spec = yaml.safe_load((src / "bundle.yaml").read_text())
    docs = [(s, d) for s in spec["sections"] for d in s["documents"]]
    for s, d in docs:
        if not (SLUG.fullmatch(str(s["slug"])) and SLUG.fullmatch(str(d["slug"]))):
            sys.exit(f"refused: a slug is lower-case letters, digits and hyphens: {s['slug']}/{d['slug']}")
        if d["kind"] not in ("doc", "table"):
            sys.exit(f"refused: {d['slug']} has a kind that is neither doc nor table")
        for f in [d["source"], *d.get("figures", [])]:
            if not (src / f).resolve().is_relative_to(src):
                sys.exit(f"refused: {d['slug']} reads a file outside the source folder")
    urls = {(src / d["source"]).resolve(): f"/private/{s['slug']}/{d['slug']}" for s, d in docs}
    name = lambda s, d: f"{s['slug']}--{d['slug']}.json"  # noqa: E731

    out.mkdir(parents=True, exist_ok=True)
    for s, d in docs:
        path = (src / d["source"]).resolve()
        body = (
            table(path, d)
            if d["kind"] == "table"
            else {"title": d["title"], "html": html(path.read_text(), path, urls)}
        )
        if d.get("figures"):
            body["figures"] = [figure((src / f).resolve()) for f in d["figures"]]
        (out / name(s, d)).write_text(json.dumps(body))
    manifest = {
        "sections": [
            {
                "slug": s["slug"],
                "title": s["title"],
                "documents": [
                    {"slug": d["slug"], "title": d["title"], "kind": d["kind"], "file": name(s, d)}
                    for d in s["documents"]
                ],
            }
            for s in spec["sections"]
        ]
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(f"wrote {len(docs)} documents in {len(spec['sections'])} sections")


if __name__ == "__main__":
    main(sys.argv[1:])
