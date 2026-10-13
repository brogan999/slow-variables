"""Build the bundle the site's private area reads (plan Part 59). Generic: it names no document.

    uv run python scripts/private_bundle.py <source folder> <output folder>

The source folder is outside the repository and holds bundle.yaml, a spec its owner keeps there:

    sections:
      - slug: example
        title: Example section
        documents:
          - {slug: first, title: First page, kind: doc, source: notes/first.md}
          - {slug: rows, title: Example rows, kind: table, source: rows.csv, columns: [name, colour], filters: [colour]}

This writes manifest.json (sections and titles, no text) and one JSON file for each document into the output
folder, which is a clone of the private store the site fetches from. A doc is markdown turned into escaped HTML;
a link from one listed document to another becomes that document's address on the site. A table is a CSV's
declared columns as rows of text. It refuses to write inside the repository.
"""

from __future__ import annotations

import csv
import json
import re
import sys
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
        if not (src / d["source"]).resolve().is_relative_to(src):
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
