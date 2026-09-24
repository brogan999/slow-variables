"""Import the Sci-Fi Idea Bank export into a private working file (plan Part 20).

    uv run python scripts/futures_import.py <idea-bank .xlsx> <out .jsonl>

Reads the main tab ("Sci-Fi Idea Bank") and the shortlist flag from "Copy of Sci-Fi Idea Bank", gives each row a
stable id, normalises its dates by futures.when/arrival, and passes the text through ingest.scrub before anything
reaches a model. The output holds Technovelgy's descriptions, so it goes only to the git-ignored docs/private/."""

from __future__ import annotations

import hashlib
import json
import sys

import duckdb

from ai_tracker.futures import arrival, when
from ai_tracker.ingest.scrub import scrub

COLS = [
    "date",
    "name",
    "novel",
    "author",
    "description",
    "built",
    "by_whom",
    "product",
    "first_made",
    "details",
    "bits_atoms",
    "companies",
]


def rows(path: str, sheet: str) -> list[tuple]:
    con = duckdb.connect()
    con.execute("LOAD excel")
    got = con.execute(
        f"SELECT * FROM read_xlsx(?, sheet='{sheet}', header=false, all_varchar=true, stop_at_empty=false, range='A1:M5000')",
        [path],
    ).fetchall()
    return [r for r in got if any(r)]


def clean(s: str | None) -> str:
    text, _flags = scrub(s or "")
    return text.strip()


def main(path: str, out: str) -> None:
    main_rows = rows(path, "Sci-Fi Idea Bank")
    head = main_rows.index(next(r for r in main_rows if r[1] == "Date"))
    shortlist = {
        (r[2], r[4]) for r in rows(path, "Copy of Sci-Fi Idea Bank") if (r[0] or "").strip().lower() == "x"
    }
    seen: set[str] = set()
    n = 0
    with open(out, "w") as f:
        for r in main_rows[head + 1 :]:
            d = dict(zip(COLS, r[1:13]))
            imagined = when(d["date"])
            if imagined["kind"] != "year" or not d["name"]:
                continue
            key = f"{d['name'].strip()}|{(d['novel'] or '').strip()}|{imagined['year']}"
            rid = "tv-" + hashlib.sha1(key.encode()).hexdigest()[:10]
            if rid in seen:  # an exact repeat of name, work and year
                continue
            seen.add(rid)
            row = {
                "id": rid,
                "name": d["name"].strip(),
                "work": (d["novel"] or "").strip(),
                "author": (d["author"] or "").strip(),
                "imagined": imagined["year"],
                "description": clean(
                    d["description"]
                ),  # Technovelgy's text: private, only ever read by a model
                "bits_atoms": (d["bits_atoms"] or "").strip() or None,
                "arrival": arrival(imagined["year"], d["built"], d["first_made"]),
                "sheet_product": (d["product"] or "").strip() or None,
                "shortlist": (d["name"], d["novel"]) in shortlist,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            n += 1
    print(f"{n} rows, {sum(1 for _ in shortlist)} shortlist flags, {len(main_rows) - head - 1 - n} skipped")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
