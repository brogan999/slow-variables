"""Build the data market's seed from the research database (plan Part 57).

    uv run python scripts/data_market_import.py <path to data_market.db> [--no-fetch]

Every vendor page the research read is fetched again here, once, with the site's User-Agent and only where robots.txt
allows; its fetch record goes to seed/data_market_fetches.yaml. A vendor is listed under a signal only when a reviewing
run found a note from one of its own pages that supports the signal, and that page answered; the page is the evidence. Social-media links are never fetched. The database is
private and stays outside the repository; the seed this writes is edited by hand afterwards like any other.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import httpx
import yaml

from ai_tracker.data_market import FETCHES, SOCIAL, SPEC
from ai_tracker.ingest.base import robots_ok, ua

THEMES = {
    "graders_quality": "Graders and quality control",
    "proof_of_lift": "Proof that the data improves a model",
    "long_horizon": "Long tasks",
    "coding": "Coding",
    "private_code": "Private code",
    "office_work": "Office work",
    "named_software_use": "Use of named software",
    "computer_use": "Computer use",
    "human_ai_sessions": "People working with AI",
    "company_records": "Companies' own records",
    "exclusivity_first_use": "Exclusivity and first use",
    "pricing_terms": "Prices and terms",
    "expert_pay": "What experts are paid",
    "data_buying_role": "Who does the buying",
    "enterprise_custom_models": "Custom models for enterprises",
    "evals_private": "Private tests",
    "finance": "Finance",
    "legal": "Law",
    "healthcare_medicine": "Healthcare and medicine",
    "science_math": "Science and mathematics",
    "chips_hardware": "Chips and hardware",
    "biology_lab": "Biology made in the lab",
    "forecasting": "Forecasting",
    "safety_security": "Safety and security",
    "synthetic_data": "Machine-made data",
    "infrastructure": "Infrastructure",
    "robotics_capture": "Robots: recordings of people",
    "robotics_teleop": "Robots: remote operation",
    "robotics_deployment": "Robots: deployment",
    "video_world": "Video and world models",
    "audio_speech": "Audio and speech",
    "gameplay": "Gameplay",
    "other": "Other",
}


def fetch(url: str) -> dict:
    rec: dict = {"url": url, "retrieved_at": date.today()}
    try:
        if not robots_ok(url):
            return {**rec, "http_status": 0, "note": "robots.txt disallows"}
        r = httpx.get(url, headers={"User-Agent": ua()}, follow_redirects=True, timeout=60)
    except httpx.HTTPError as e:
        return {**rec, "http_status": 0, "note": type(e).__name__}
    rec["http_status"] = r.status_code
    if r.status_code == 200:
        rec["content_hash"] = hashlib.sha256(r.content).hexdigest()
    return rec


def main(args: list[str]) -> None:
    db = sqlite3.connect(args[0])
    db.row_factory = sqlite3.Row
    vendors = db.execute("select * from vendors where status != 'left_out' order by slug").fetchall()
    ids = {v["slug"] for v in vendors}
    pages = [
        r
        for r in db.execute(
            "select s.slug, s.url, t.tag from signals s join signal_tags t on t.slug = s.slug and t.n = s.n order by s.slug, s.n"
        )
        if r["slug"] in ids and r["url"].startswith("https://") and not SOCIAL.search(r["url"])
    ]

    attempts = (
        Path(args[0]).parent / "site_fetches.json"
    )  # every attempt, kept beside the database so a rerun fetches nothing twice
    known = {
        f["url"]: f for f in (yaml.safe_load(FETCHES.read_text())["fetches"] if FETCHES.exists() else [])
    }
    if attempts.exists():
        known |= {
            f["url"]: {**f, "retrieved_at": date.fromisoformat(f["retrieved_at"])}
            for f in json.loads(attempts.read_text())
        }
    todo = sorted({r["url"] for r in pages} - set(known))
    if todo and "--no-fetch" not in args:
        with ThreadPoolExecutor(8) as pool:
            for rec in pool.map(fetch, todo):
                known[rec["url"]] = rec
                print(rec["http_status"], rec["url"], flush=True)
    ok = {u for u, f in known.items() if f.get("http_status") == 200 and f.get("content_hash")}

    # the reviewing run's verdicts: the one note of a vendor's that supports a signal, where any does
    pairs: dict[str, list[dict[str, str]]] = {}
    for r in db.execute(
        "select p.signal_id, p.vendor, s.url from pairing p join signals s on s.slug = p.vendor and s.n = p.n order by p.signal_id, p.vendor"
    ):
        if r["vendor"] in ids and r["url"] in ok and not SOCIAL.search(r["url"]):
            pairs.setdefault(r["signal_id"], []).append({"vendor": r["vendor"], "url": r["url"]})
    listed = {e["vendor"] for es in pairs.values() for e in es}

    signals = [
        {
            "id": r["id"],
            "theme": r["tag"],
            "headline": r["public_headline"] or r["headline"],
            "implies": r["public_implies"] or r["implies"],
            "shown_by": [e["vendor"] for e in pairs[r["id"]]],
            "evidence": pairs[r["id"]],
        }
        for r in db.execute("select * from rollup order by id")
        if r["id"] in pairs
    ]
    used = {e["url"] for s in signals for e in s["evidence"]}
    out_vendors = [
        {
            "id": v["slug"],
            "name": v["name"],
            "role": "builder" if (v["sells"] or "").startswith("buyer") else "seller",
            "evidence": "evidenced" if v["status"] == "included" else "weak",
            "sells": v["public_sells"] or v["sells"],
            "pages": sorted({e["url"] for s in signals for e in s["evidence"] if e["vendor"] == v["slug"]}),
        }
        for v in vendors
        if v["slug"] in listed
    ]
    out_vendors = [v for v in out_vendors if v["pages"]]
    doc = yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}
    doc = {
        "made_by": doc.get("made_by") or {"model": "", "date": date.today(), "method": "", "reviewed_by": ""},
        "disclosure": doc.get("disclosure") or "",
        "themes": {k: v for k, v in THEMES.items() if any(s["theme"] == k for s in signals)},
        "vendors": out_vendors,
        "signals": signals,
    }
    SPEC.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))
    FETCHES.write_text(
        "# Written by scripts/data_market_import.py: one fetch record per vendor page the seed cites.\n"
        + yaml.safe_dump({"fetches": [known[u] for u in sorted(used)]}, sort_keys=False, width=1000)
    )
    left = sorted(ids - {v["id"] for v in out_vendors})
    print(
        f"{len(out_vendors)} vendors, {len(signals)} signals, {len(used)} pages cited of {len(ok)} that answered; no page answered for: {', '.join(left) or 'none'}"
    )
    attempts.write_text(json.dumps(list(known.values()), default=str, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
