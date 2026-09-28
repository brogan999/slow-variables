"""Fetch the primary sources behind the value-chain company profiles (seed/value_chain.yaml).

    uv run python scripts/value_chain_sources.py <id> <entity> <url> <form> <filed YYYY-MM-DD> [...]

Each source is fetched once, with the site's User-Agent and only where robots.txt allows. Its fetch record
(retrieved_at, http_status, content_hash) is merged into the seed's `sources:` block. Its text, with any sentence
addressed to a model scrubbed out, is cached in ~/.ai-tracker/value_chain/<id>.txt for the authors to read; the cache
is local and never committed.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
import tempfile
from datetime import date
from html import unescape
from pathlib import Path

import httpx
import yaml

from ai_tracker.ingest.base import robots_ok, ua
from ai_tracker.ingest.scrub import scrub

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seed" / "value_chain.yaml"
CACHE = Path.home() / ".ai-tracker" / "value_chain"


def text_of(body: bytes, url: str) -> str:
    if url.lower().endswith(".pdf") or body[:4] == b"%PDF":
        with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
            f.write(body)
            f.flush()
            return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, check=True).stdout
    html = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", body.decode("utf-8", "ignore"))
    return unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)))


def fetch(sid: str, entity: str, url: str, form: str, filed: str) -> dict:
    if not robots_ok(url):
        raise SystemExit(f"{sid}: robots.txt disallows {url}")
    r = httpx.get(url, headers={"User-Agent": ua()}, follow_redirects=True, timeout=120)
    rec = {"id": sid, "entity": entity, "url": url, "form": form, "filed": date.fromisoformat(filed), "retrieved_at": date.today(), "http_status": r.status_code}
    if r.status_code == 200:
        rec["content_hash"] = hashlib.sha256(r.content).hexdigest()
        clean, flagged = scrub(text_of(r.content, url))
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / f"{sid}.txt").write_text(clean)
        print(f"{sid}: {r.status_code}, {len(clean):,} chars cached" + (f", {len(flagged)} sentences scrubbed" if flagged else ""))
    else:
        print(f"{sid}: answered {r.status_code}")
    return rec


def main(args: list[str]) -> None:
    if not args or len(args) % 5:
        raise SystemExit(__doc__)
    text = SEED.read_text() if SEED.exists() else "companies: []\nsources:\n"
    have = {s["id"] for s in (yaml.safe_load(text) or {}).get("sources") or []}
    new = [fetch(*args[i : i + 5]) for i in range(0, len(args), 5)]
    if again := [r["id"] for r in new if r["id"] in have]:
        raise SystemExit(f"already recorded: {', '.join(again)}; a source is fetched once")
    # appended as text, so the hand-edited profiles above keep their layout
    SEED.write_text(text.rstrip("\n") + "\n" + yaml.safe_dump(new, sort_keys=False, allow_unicode=True, width=10000))


if __name__ == "__main__":
    main(sys.argv[1:])
