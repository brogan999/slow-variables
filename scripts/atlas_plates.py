"""Convert the Singularity Atlas plates (owner-supplied PNGs, Sep 2026) into the WebP sizes the pages serve.

    uv run python scripts/atlas_plates.py <directory holding the PNGs>

Writes web/public/atlas/<name>-<width>.webp and prints each source file's sha256, which seed/atlas.yaml records as
the plate's provenance. The PNGs themselves are not committed."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from PIL import Image

NAMES = [
    "hero-fresco",
    "economy",
    "work",
    "culture",
    "politics",
    "security",
    "technology",
    "biology",
    "daily",
]
WIDTHS = [480, 768, 1024]
OUT = Path(__file__).resolve().parents[1] / "web/public/atlas"


def trim(im: Image.Image, inset: float = 0.025) -> Image.Image:
    """Crop the white canvas round a painting, then a little more, so the torn paper edge never shows."""
    box = im.convert("L").point(lambda v: 255 if v < 230 else 0).getbbox() or (0, 0, *im.size)
    dx, dy = round((box[2] - box[0]) * inset), round((box[3] - box[1]) * inset)
    return im.crop((box[0] + dx, box[1] + dy, box[2] - dx, box[3] - dy))


def main(src: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        path = src / f"{name}.png"
        print(name, hashlib.sha256(path.read_bytes()).hexdigest())
        im = trim(Image.open(path).convert("RGB"))
        for w in WIDTHS:
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
                OUT / f"{name}-{w}.webp", quality=80, method=6
            )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
