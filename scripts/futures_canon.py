"""Write the Futures canon forecasts seed from the private survey (plan Part 20, 3/4).

    uv run python scripts/futures_canon.py <private final.jsonl> <canon sources.json>

final.jsonl is the reviewed survey: dated technology forecasts found in the singularity canon's non-fiction, each line in
this site's words and checked against its passages by three reviewers. This writes seed/futures/forecasts.jsonl
(public fields only; passage indices stay private) and seed/futures/canon_sources.yaml: each work credited by title,
author and year, with a link only where the page was fetched here (a record already in another seed, or a fresh fetch)."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = "slow-variables/0.1 github.com/brogan999/slow-variables"
ODDS = {"10": "ten", "25": "twenty-five", "50": "fifty", "80": "eighty", "2/3": "two-thirds"}


def odds_in_words(text: str | None) -> str | None:
    """Attributed odds may use number words but never digits (years excepted)."""
    if not text:
        return text
    text = re.sub(r"(\d+)\s*(%|percent)", lambda m: f"{ODDS[m[1]]} percent", text)
    return re.sub(r"\b2/3\b", ODDS["2/3"], text)


def known_fetches() -> dict[str, dict]:
    out = {}
    for f in ("singularity.yaml", "atlas.yaml", "outlook.yaml"):
        for x in yaml.safe_load((ROOT / "seed" / f).read_text()).get("sources") or []:
            if x.get("url") and x.get("http_status") == 200:
                out[x["url"]] = x
    return out


def fetch(url: str) -> dict | None:
    try:
        r = httpx.get(url, headers={"User-Agent": UA}, follow_redirects=True, timeout=45)
    except httpx.HTTPError:
        return None
    if r.status_code != 200:
        return None
    return {"retrieved_at": date.today(), "http_status": 200, "content_hash": hashlib.sha256(r.content).hexdigest()}


def main(final: str, canon_sources: str) -> None:
    rows = [json.loads(line) for line in Path(final).read_text().splitlines()]
    canon = {s["slug"]: s for s in json.loads(Path(canon_sources).read_text())}
    known = known_fetches()
    works = sorted({p["slug"] for r in rows for p in r["passages"]})
    sources = []
    for slug in works:
        s = canon[slug]
        src = {"id": slug, "title": s["title"], "author": s["author"], "year": s["year"]}
        url = s.get("url") or ""
        rec = known.get(url) or (fetch(url) if url.startswith("http") and "sec.gov" not in url else None)
        if rec:
            src |= {"url": url, "retrieved_at": rec["retrieved_at"], "http_status": 200, "content_hash": rec["content_hash"]}
        sources.append(src)
    (ROOT / "seed" / "futures" / "canon_sources.yaml").write_text(
        "# Written by scripts/futures_canon.py: the canon works the forecasts come from. A link appears only where the page\n"
        "# was fetched; books and pages that refuse scripts are credited by title, author and year.\n"
        + yaml.safe_dump({"sources": sources}, sort_keys=False, allow_unicode=True)
    )
    with (ROOT / "seed" / "futures" / "forecasts.jsonl").open("w") as f:
        for r in sorted(rows, key=lambda r: r["id"]):
            f.write(
                json.dumps(
                    {
                        "id": r["id"],
                        "who": r["who"],
                        "technology": r["technology"],
                        "line": r["line"],
                        "category": r["category"],
                        "when": r["when"],
                        "odds": odds_in_words(r["odds"]),
                        "quote": r["quote"],
                        "ai_milestone": r["ai_milestone"],
                        "ledger_id": r["ledger_id"],
                        "works": sorted({p["slug"] for p in r["passages"]}),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"{len(rows)} forecasts, {len(sources)} works, {sum('url' in s for s in sources)} linked")


if __name__ == "__main__":
    main(*sys.argv[1:3])
