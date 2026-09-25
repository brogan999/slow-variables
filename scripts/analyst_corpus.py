"""Build the private analyst's search index: a SQLite FTS5 table over the owner's local reading, outside the repo.

    uv run python scripts/analyst_corpus.py [--db ~/.ai-tracker/analyst.db]

Each chunk (about 1,500 tokens) keeps its collection, title, author, year, URL and access tier: public, paid (a paid
newsletter post), book, or own (the owner's notes). Every chunk passes through ingest/scrub.py; files that are prompts
addressed to a model are skipped. Nothing here is published: paid and book text is for paraphrase with credit, and
the database never enters the repo or the query service's image.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import zipfile
from collections.abc import Iterator
from pathlib import Path

from ai_tracker.ingest.scrub import html_to_text, scrub

HOME = Path.home()
REPO = Path(__file__).resolve().parents[1]
DB = HOME / ".ai-tracker" / "analyst.db"
CHUNK = 6000  # characters, about 1,500 tokens
PROMPTY = re.compile(r"prompt|^claude\.md$|^agents\.md$", re.I)
BOOK_KINDS = {"epub", "local", "manual", "buy"}  # the singularity canon's own kinds for book-derived text
# (collection, root, glob, default author, default access)
SOURCES = [
    ("knowledge_base", HOME / "knowledge-base", "**/*.md", "Alex Brogan (notes)", "own"),
    ("singularity_canon", HOME / "singularity-canon" / "text", "*.md", None, "public"),
    ("the_diff", HOME / "thediff" / "corpus", "*.md", "Byrne Hobart", "paid"),
    ("sean_cai", HOME / "rl-env-gtm-research" / "substack-full", "*.md", "Sean Cai", "paid"),
    ("gary_marcus", HOME / "gary-marcus" / "substack-full", "*.md", "Gary Marcus", "public"),
    ("normal_technology", HOME / "normaltech-predictions" / "corpus", "*.md", "Arvind Narayanan and Sayash Kapoor", "public"),
    ("sales_canon", HOME / "sales-canon", "phase*/**/*.md", "Startup Sales Canon (book-derived notes)", "book"),
    ("tracker_private", HOME / "ai-tracker" / "docs" / "private", "**/*.md", "Alex Brogan (notes)", "own"),
]
EPUBS = [("inference_engineering", HOME / "Downloads" / "Inference Engineering.epub", "book")]


def front(text: str) -> tuple[dict[str, str], str]:
    """YAML-ish front matter as flat strings, and the body after it."""
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = {k.strip(): v.strip().strip('"') for k, v in re.findall(r"^(\w+):\s*(.*)$", m[1], re.M)}
    return meta, text[m.end() :]


def describe(collection: str, path: Path, text: str, author: str | None, access: str) -> tuple[dict[str, str], str]:
    meta, body = front(text)
    head = body[:600]
    title = meta.get("title") or next(iter(re.findall(r"^#\s+(.+)$", head, re.M)), path.stem)
    year = meta.get("year") or next(iter(re.findall(r"\b((?:19|20)\d\d)-\d\d-\d\d\b", head)), "")
    url = meta.get("source") or next(iter(re.findall(r"https?://[^\s)*]+", head)), "")
    if collection == "singularity_canon" and meta.get("kind") in BOOK_KINDS:
        access = "book"
    if re.search(r"\(paid\)|\[paid\]", head):
        access = "paid"
    elif re.search(r"\(free\)|\[free\]", head) and access == "paid":
        access = "public"
    byline = next(iter(re.findall(r"^By (.+)$", head, re.M)), None)  # a post's own byline beats the collection's default
    return {"title": title, "author": meta.get("author") or byline or author or "", "year": str(year), "url": url, "access": access}, body


def chunks(body: str) -> Iterator[str]:
    """Paragraph-packed pieces of about CHUNK characters; a single huge paragraph is cut at the limit."""
    buf = ""
    for para in re.split(r"\n\s*\n", body):
        while len(para) > CHUNK:
            yield para[:CHUNK]
            para = para[CHUNK:]
        if len(buf) + len(para) > CHUNK and buf:
            yield buf
            buf = ""
        buf += para + "\n\n"
    if buf.strip():
        yield buf


def epub_author(path: Path) -> str:
    with zipfile.ZipFile(path) as z:
        opf = next((n for n in z.namelist() if n.endswith(".opf")), None)
        text = z.read(opf).decode("utf-8", errors="ignore") if opf else ""
    return ", ".join(re.findall(r"<dc:creator[^>]*>([^<]+)</dc:creator>", text))


def epub_text(path: Path) -> Iterator[tuple[str, str]]:
    """Each chapter of an epub as (name, text), in spine order where the archive lists it."""
    with zipfile.ZipFile(path) as z:
        names = sorted(n for n in z.namelist() if n.endswith((".xhtml", ".html", ".htm")))
        for n in names:
            text = html_to_text(z.read(n).decode("utf-8", errors="ignore"))
            if len(text.strip()) > 200:
                yield Path(n).stem, text


def build(db: Path) -> dict[str, int]:
    if REPO in db.resolve().parents:  # paid posts and book text must never sit where git or the image can take them
        raise SystemExit(f"refusing to write the analyst index inside the repo: {db}")
    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    con.execute(
        "CREATE VIRTUAL TABLE chunks USING fts5(text, title, author, collection UNINDEXED, year UNINDEXED,"
        " access UNINDEXED, url UNINDEXED, path UNINDEXED, part UNINDEXED, tokenize = 'porter unicode61')"
    )
    counts: dict[str, int] = {"skipped_prompt_files": 0, "flagged_chunks": 0}

    def add(collection: str, path: str, d: dict[str, str], body: str) -> None:
        for n, piece in enumerate(chunks(body)):
            text, flags = scrub(piece)
            counts["flagged_chunks"] += bool(flags)
            if len(text.strip()) < 80:
                continue
            con.execute(
                "INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [text, d["title"], d["author"], collection, d["year"], d["access"], d["url"], path, n],
            )
            counts[collection] = counts.get(collection, 0) + 1

    for collection, root, pattern, author, access in SOURCES:
        for f in sorted(root.glob(pattern)) if root.is_dir() else []:
            if PROMPTY.search(f.name):
                counts["skipped_prompt_files"] += 1
                continue
            d, body = describe(collection, f, f.read_text(errors="ignore").replace("\\$", "$"), author, access)
            add(collection, str(f), d, body)
    for collection, path, access in EPUBS:
        if path.exists():
            who = epub_author(path)
            for name, text in epub_text(path):
                add(collection, f"{path}#{name}", {"title": f"{path.stem}: {name}", "author": who, "year": "", "url": "", "access": access}, text)
    con.commit()
    con.close()
    tmp.replace(db)
    return counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DB)
    a = ap.parse_args()
    for k, v in build(a.db.expanduser()).items():
        print(f"{k:24} {v}")
    print(f"wrote {a.db.expanduser()}")
