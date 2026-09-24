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


def main(src: Path) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in NAMES:
        path = src / f"{name}.png"
        print(name, hashlib.sha256(path.read_bytes()).hexdigest())
        im = Image.open(path).convert("RGB")
        for w in WIDTHS:
            im.resize((w, round(im.height * w / im.width)), Image.LANCZOS).save(
                OUT / f"{name}-{w}.webp", quality=80, method=6
            )


if __name__ == "__main__":
    main(Path(sys.argv[1]))
