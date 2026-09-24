"""Import the Futures illustrations (owner-made in ChatGPT from the site's own prompts, Sep 2026) as served WebP.

    uv run python scripts/futures_images.py <index.csv> <zip or directory> [...]

The index is the owner's record of the set (file, category, the exact prompt, sha256, any correction made after
review). Each image is matched to its row by file name, checked against the index's sha256, written to web/public/futures/<stem>-<width>.webp,
and recorded in seed/futures/images.yaml with the prompt it was made from and the sha256 of the original file (the
originals are not committed). Prints unmatched files, and writes a contact sheet to the path in CONTACT for review."""

from __future__ import annotations

import csv
import hashlib
import io
import sys
import zipfile
from datetime import date
from pathlib import Path

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web/public/futures"
SEED = ROOT / "seed/futures/images.yaml"
CONTACT = Path("/tmp/futures-contact-sheet.jpg")
WIDTHS = [480, 960]


def originals(paths: list[str]) -> dict[str, bytes]:
    found: dict[str, bytes] = {}
    for p in map(Path, paths):
        if p.suffix == ".zip":
            with zipfile.ZipFile(p) as z:
                for n in z.namelist():
                    if n.lower().endswith((".png", ".jpg", ".jpeg", ".webp")) and not n.startswith("__MACOSX"):
                        found[Path(n).name] = z.read(n)
        else:
            for f in p.glob("*"):
                if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                    found[f.name] = f.read_bytes()
    return found


def main(prompts: str, *paths: str) -> None:
    rows = {Path(r["file"]).stem: r for r in csv.DictReader(open(prompts))}
    got = originals(list(paths))
    OUT.mkdir(parents=True, exist_ok=True)
    seed = yaml.safe_load(SEED.read_text()) if SEED.exists() else {"images": []}
    have = {x["stem"]: x for x in seed["images"]}
    unmatched, thumbs, mismatched = [], [], []
    for name, data in sorted(got.items()):
        stem = Path(name).stem
        row = rows.get(stem)
        if not row:
            unmatched.append(name)
            continue
        digest = hashlib.sha256(data).hexdigest()
        if row.get("sha256") and row["sha256"] != digest:
            mismatched.append(name)
            continue
        im = Image.open(io.BytesIO(data)).convert("RGB")
        for w in WIDTHS:
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(OUT / f"{stem}-{w}.webp", quality=72, method=6)
        have[stem] = {
            "stem": stem,
            "idea": stem.split("-")[0] + "-" + stem.split("-")[1] if stem.startswith("tv-") else None,
            "category": row["category"],
            "prompt": row["prompt"],
            "width": im.width,
            "height": im.height,
            "sha256": digest,
            "made_with": "ChatGPT image generation",
            "correction": (row.get("correction") or "").strip() or None,
            "imported": date.today(),
        }
        thumbs.append((stem, im.resize((240, round(im.height * 240 / im.width)))))
    SEED.write_text(
        "# Written by scripts/futures_images.py: one entry per illustration. Made by the site's owner in ChatGPT from the\n"
        "# prompt shown, which this site wrote from its own reworded line; illustrations, not evidence.\n"
        + yaml.safe_dump({"images": sorted(have.values(), key=lambda x: x["stem"])}, sort_keys=False, allow_unicode=True)
    )
    if thumbs:
        cols = 6
        sheet = Image.new("RGB", (cols * 244, ((len(thumbs) + cols - 1) // cols) * 168), "white")
        for k, (_, t) in enumerate(thumbs):
            sheet.paste(t.crop((0, 0, 240, 160)), ((k % cols) * 244, (k // cols) * 168))
        sheet.save(CONTACT, quality=85)
    print(f"{len(thumbs)} imported, {len(have)} in the seed, {len(rows) - len(have)} slots still empty")
    for n in unmatched:
        print("  unmatched:", n)
    for n in mismatched:
        print("  sha256 differs from the index:", n)


if __name__ == "__main__":
    main(*sys.argv[1:])
