"""The illustrations placed on pages outside Futures (/firm/kinds now, /story when it exists). Each is one WebP in
web/public/illustrations/, copied byte for byte from the owner's delivery and recorded in seed/illustrations.yaml with
its sha256, the model and prompt it was made from, and an alt text. Made with AI image generation; never evidence."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "seed" / "illustrations.yaml"
DIR = ROOT / "web" / "public" / "illustrations"
WIDTH, HEIGHT = 720, 480


def load() -> list[dict[str, Any]]:
    return (yaml.safe_load(SEED.read_text()) or []) if SEED.exists() else []


def webp_size(data: bytes) -> tuple[int, int] | None:
    """Width and height from a lossy WebP's own header; None for anything else.
    ponytail: reads only the lossy ('VP8 ') layout, which is all this set uses; add VP8L and VP8X if a set needs them."""
    if data[:4] != b"RIFF" or data[8:16] != b"WEBPVP8 " or data[23:26] != b"\x9d\x01\x2a":
        return None
    return int.from_bytes(data[26:28], "little") & 0x3FFF, int.from_bytes(data[28:30], "little") & 0x3FFF


def card(stem: str | None) -> dict[str, Any] | None:
    """What a page needs to show one: the served path, the alt text and the stage it pictures, if any."""
    r = next((x for x in load() if x["stem"] == stem), None)
    return {"file": f"/illustrations/{stem}.webp", "alt": r["alt"], "stage": r.get("stage")} if r else None


def problems(records: list[dict[str, Any]], d: Path = DIR) -> list[str]:
    errors: list[str] = []
    for r in records:
        where = f"illustrations: {r['stem']}"
        errors += [f"{where} has no {label}" for f, label in (("alt", "alt text"), ("prompt", "prompt")) if not (r.get(f) or "").strip()]
        f = d / f"{r['stem']}.webp"
        if not f.exists():
            errors.append(f"{where}.webp is missing")
            continue
        data = f.read_bytes()
        if hashlib.sha256(data).hexdigest() != r.get("sha256"):
            errors.append(f"{where}.webp differs from its recorded sha256")
        if webp_size(data) != (WIDTH, HEIGHT):
            errors.append(f"{where}.webp is not a WebP of {WIDTH} by {HEIGHT}")
    known = {f"{r['stem']}.webp" for r in records}
    errors += [f"illustrations: {p.name} has no record" for p in sorted(d.glob("*")) if p.name not in known]
    return errors


def placement_problems(records: list[dict[str, Any]], placed: dict[str, list[str]]) -> list[str]:
    """`placed` is each page's stems as its seed names them: every one is recorded for that page and used once, and
    every record for the page is used. A record that waits for a page not yet built is placed nowhere."""
    by = {r["stem"]: r for r in records}
    errors: list[str] = []
    for page, stems in placed.items():
        for s in sorted(set(stems)):
            if s not in by:
                errors.append(f"illustrations: {page} names {s}, which has no record")
            elif by[s].get("waits_for"):
                errors.append(f"illustrations: {s} is placed on {page} but its record waits for {by[s]['waits_for']}")
            elif by[s].get("page") != page:
                errors.append(f"illustrations: {s} is placed on {page} but recorded for {by[s].get('page')}")
            if stems.count(s) > 1:
                errors.append(f"illustrations: {s} is placed more than once on {page}")
        errors += [f"illustrations: {r['stem']} is recorded for {page} but not placed" for r in records if r.get("page") == page and r["stem"] not in stems]
    return errors
