"""Import a version of the Automatability Census bundle as published (plan Part 21).

    uv run python scripts/census_import.py ~/automatability-census/out/bundle/<version>

Checks every file against the bundle's manifest, copies the files unchanged to data/census/<version>/ (and the CSVs to
web/public/data/census/<version>/ for download), then fetches each deal-sheet source URL and writes its fetch record to
seed/census_fetches.yaml. A page that refuses scripts is read through the Internet Archive's raw copy, and that copy is
the link kept; sec.gov refuses a user agent without an email, so it always goes through the archive."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import date
from pathlib import Path

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[1]
UA = "slow-variables/0.1 github.com/brogan999/slow-variables"  # never the local .env agent: it carries an email


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url: str) -> dict:
    """The live page, or the Internet Archive's raw copy when the live page refuses scripts (sec.gov always does)."""
    links = [] if "sec.gov" in url else [url]
    links += [f"https://web.archive.org/web/{y}id_/{url}" for y in (2026, 2025)]
    for link in links:
        r = httpx.get(link, headers={"User-Agent": UA}, follow_redirects=True, timeout=60)
        if r.status_code == 200:
            break
    return {
        "url": link,
        "cited_as": url,
        "retrieved_at": date.today(),
        "http_status": r.status_code,
        "content_hash": hashlib.sha256(r.content).hexdigest(),
    }


def main(bundle: str) -> None:
    src = Path(bundle).expanduser().resolve()
    manifest = json.loads((src / "manifest.json").read_text())
    version = manifest["version"]
    for name, meta in manifest["files"].items():
        assert sha(src / name) == meta["sha256"], f"{name} does not match the bundle's manifest"
    data = ROOT / "data" / "census" / version
    pub = ROOT / "web" / "public" / "data" / "census" / version
    data.mkdir(parents=True, exist_ok=True)
    pub.mkdir(parents=True, exist_ok=True)
    for name in [*manifest["files"], "manifest.json"]:
        shutil.copyfile(src / name, data / name)
        if name.endswith(".csv"):
            shutil.copyfile(src / name, pub / name)
    urls = sorted({u for c in json.loads((src / "deal_sheets.json").read_text())["cards"] for u in c["sources"]})
    records = [fetch(u) for u in urls]
    (ROOT / "seed" / "census_fetches.yaml").write_text(
        "# Written by scripts/census_import.py: one fetch record per deal-sheet source link.\n"
        + yaml.safe_dump({"version": version, "fetches": records}, sort_keys=False, allow_unicode=True)
    )
    bad = [r for r in records if r["http_status"] != 200]
    print(f"{version}: {len(manifest['files'])} files copied, {len(records)} links fetched, {len(bad)} not 200")
    for r in bad:
        print(f"  {r['http_status']} {r['url']}")


if __name__ == "__main__":
    main(sys.argv[1])
