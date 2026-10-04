"""Import the Futures illustrations as served WebP. Two sets:

    uv run python scripts/futures_images.py <index.csv> <zip or directory> [...]   # owner-made in ChatGPT, Sep 2026: two widths
    uv run python scripts/futures_images.py --generated <delivery dir> [sheets dir]  # Qwen Image set, Oct 2026: one width

The first form, below:

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


GENERATED = ROOT / "seed/futures/images_generated.jsonl"
WIDTH = 720  # idea cards show at most 360 px wide
PER_SHEET, COLS = 48, 6


def _encode(job: tuple[str, str, str, bool]) -> tuple[str, str]:
    """One original at a time: its sha256, and the served WebP written unless the hash differs from the catalogue's."""
    path, stem, want, withheld = job
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest == want and not withheld:
        im = Image.open(io.BytesIO(data)).convert("RGB")
        im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS).save(OUT / f"{stem}-{WIDTH}.webp", quality=72, method=6)
    return stem, digest


def generated(delivery: str, sheets: str = "/tmp/futures-sheets") -> None:
    """The Qwen Image set: catalogue.csv names each file and its sha256, prompts.jsonl the prompt it was made from.
    Writes one WebP per image, the seed JSONL (keeping any `withheld` reason already there), and contact sheets."""
    import json
    from multiprocessing import Pool

    d = Path(delivery)
    rows = list(csv.DictReader(open(d / "catalogue.csv")))
    prompts = {json.loads(line)["id"]: json.loads(line)["final_prompt"] for line in open(d / "prompts.jsonl")}
    kept = {json.loads(line)["stem"]: json.loads(line) for line in GENERATED.read_text().splitlines()} if GENERATED.exists() else {}
    OUT.mkdir(parents=True, exist_ok=True)
    with Pool() as pool:
        digests = dict(pool.imap_unordered(_encode, [(str(d / r["file"]), Path(r["file"]).stem, r["sha256"], bool(kept.get(Path(r["file"]).stem, {}).get("withheld"))) for r in rows], chunksize=8))
    out, bad = [], []
    for r in sorted(rows, key=lambda r: r["file"]):
        stem = Path(r["file"]).stem
        if digests[stem] != r["sha256"]:
            bad.append(stem)
            continue
        row = {"stem": stem, "idea": r["id"], "sha256": r["sha256"], "model": r["model"], "revision": int(r["revision"]), "prompt": prompts[r["id"]]}
        if kept.get(stem, {}).get("withheld"):
            row["withheld"] = kept[stem]["withheld"]
        out.append(row)
    GENERATED.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in out))
    Path(sheets).mkdir(parents=True, exist_ok=True)
    for n in range(0, len(out), PER_SHEET):
        page = out[n:n + PER_SHEET]
        sheet = Image.new("RGB", (COLS * 244, ((len(page) + COLS - 1) // COLS) * 168), "white")
        for k, x in enumerate(y for y in page if not y.get("withheld")):
            sheet.paste(Image.open(OUT / f"{x['stem']}-{WIDTH}.webp").resize((240, 160)), ((k % COLS) * 244, (k // COLS) * 168))
        sheet.save(Path(sheets) / f"sheet-{n // PER_SHEET + 1:03d}.jpg", quality=85)
        (Path(sheets) / f"sheet-{n // PER_SHEET + 1:03d}.txt").write_text("".join(f"{k + 1} {x['stem']}\n" for k, x in enumerate(page)))
    print(f"{len(out)} imported, {len(bad)} with a sha256 that differs from the catalogue")
    for stem in bad:
        print("  sha256 differs:", stem)


if __name__ == "__main__":
    generated(*sys.argv[2:]) if sys.argv[1] == "--generated" else main(*sys.argv[1:])
