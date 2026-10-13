"""Bring the data market's dossiers into the repository (plan Part 57f).

    uv run python scripts/data_market_dossiers.py <folder of public drafts> <folder of the gate's fetched pages>

A draft is a markdown file named D<number>-<slug>.md: prose, then a "Sources" list of "- [key] name — url", then private
notes after a rule, which are dropped. The gate has already fetched each source under the site's rules and kept its text
and fetch record. For every number in the prose this finds the passage of a cited source that states it; a dossier with
a number no cited source states is left out and named. The drafts and the fetched pages stay outside the repository.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

from ai_tracker.data_market import (
    DOSSIER_FETCHES,
    DOSSIER_TEXT,
    DOSSIERS,
    SOCIAL,
    prose_figures,
    prose_quotes,
    squash,
)


def main(args: list[str]) -> None:
    drafts, pages = Path(args[0]), Path(args[1])
    records = {r["url"]: r for r in json.loads((pages.parent / "fetches.json").read_text())}

    def page(url: str) -> str:
        p = pages / (hashlib.sha1(url.encode()).hexdigest() + ".txt")
        return re.sub(r"\s+", " ", re.sub(r"(?<=\d),(?=\d)", "", p.read_text())) if p.exists() else ""

    out, used, left = [], set(), []
    DOSSIER_TEXT.mkdir(parents=True, exist_ok=True)
    for old in DOSSIER_TEXT.glob("*.md"):
        old.unlink()
    for f in sorted(drafts.glob("D*.md")):
        n, slug = re.match(r"D(\d+)-(.+)\.md", f.name).groups()
        body = f.read_text().split("\n---\n")[0]
        parts = re.split(r"\n#{2,3} Sources\n", body, maxsplit=1)
        text, listed = parts[0], parts[1] if len(parts) > 1 else ""
        sources = [
            {"key": m.group(1), "name": m.group(2).strip(" —-"), "url": m.group(3)}
            for m in re.finditer(r"^- \[([^\]]+)\] (.*?)(https?://\S+)\s*$", listed, re.M)
        ]
        url = {s["key"]: s["url"] for s in sources}
        bad = [
            s["key"]
            for s in sources
            if SOCIAL.search(s["url"]) or records.get(s["url"], {}).get("http_status") != 200
        ]
        figs, missing = [], []
        for number, cited in prose_figures(text):
            for k in cited:
                m = re.search(r"(?<![\d.])" + re.escape(number) + r"(?!\d|\.\d)", page(url.get(k, "")))
                if m:
                    t = page(url[k])
                    figs.append(
                        {
                            "figure": number,
                            "key": k,
                            "snippet": t[max(0, m.start() - 70) : m.end() + 70].strip(),
                        }
                    )
                    break
            else:
                missing.append(number)
        quotes = []
        for q, cited in prose_quotes(text):
            pieces = [squash(x) for x in re.split(r"\.\.\.|…", q) if len(x.strip()) > 12]
            k = next((k for k in cited if k in url and all(x in squash(page(url[k])) for x in pieces)), None)
            if k:
                quotes.append({"key": k, "quote": q})
            else:
                missing.append(f"quotation {q[:30]!r}")
        if bad or missing:
            left.append(
                f"{f.name}: "
                + "; ".join(
                    filter(
                        None,
                        [
                            bad and f"sources not read: {', '.join(bad)}",
                            missing and f"figures not stated: {', '.join(missing)}",
                        ],
                    )
                )
            )
            continue
        figs = list({(g["figure"], g["key"]): g for g in figs}.values())
        (DOSSIER_TEXT / f"{slug}.md").write_text(text.strip() + "\n")
        out.append(
            {
                "id": slug,
                "n": int(n),
                "title": text.strip().split("\n")[0].lstrip("# ").strip(),
                "sources": sources,
                "figures": figs,
                "quotes": quotes,
            }
        )
        used |= {s["url"] for s in sources}
    DOSSIERS.write_text(
        "# Written by scripts/data_market_dossiers.py: each dossier's sources, and the passage of a source that states each figure.\n"
        + yaml.safe_dump({"dossiers": out}, sort_keys=False, allow_unicode=True, width=1000)
    )
    DOSSIER_FETCHES.write_text(
        "# Written by scripts/data_market_dossiers.py: one fetch record per dossier source.\n"
        + yaml.safe_dump(
            {
                "fetches": [
                    {
                        k: (date.fromisoformat(v) if k == "retrieved_at" else v)
                        for k, v in records[u].items()
                        if k in ("url", "retrieved_at", "http_status", "content_hash")
                    }
                    for u in sorted(used)
                ]
            },
            sort_keys=False,
            width=1000,
        )
    )
    print(f"{len(out)} dossiers, {len(used)} sources; left out: {len(left)}")
    for line in left:
        print("  " + line)


if __name__ == "__main__":
    main(sys.argv[1:])
