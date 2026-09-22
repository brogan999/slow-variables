"""The web never computes a number (CLAUDE.md): arithmetic lives in the export, and a page only draws what it wrote.
This fails on the tell-tale calls anywhere under web/src outside the files allowed them. PENDING lists the figures
not yet converted; it only shrinks, and a file that no longer needs its place must leave it."""

import re
from pathlib import Path

ROOT = Path("web/src")
# formatting, the chart primitives, placing a tooltip, and the footer's "updated N days ago"
ALLOWED = {"lib/format.ts", "components/chart.tsx", "components/HoverLayer.tsx", "components/Freshness.tsx"}
PENDING = {
    "components/FourClocks.tsx",
    "components/MigrationParts.tsx",
    "components/VentureFlowStrip.tsx",
    "app/methodology/page.tsx",
}
TELLS = re.compile(r"Math\.|\.reduce\(|toFixed\(|toLocale\w*String\(")


def test_the_web_computes_no_number():
    hits = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.ts*") if TELLS.search(p.read_text())}
    assert not hits - ALLOWED - PENDING, (
        f"arithmetic in the web; export the number instead: {sorted(hits - ALLOWED - PENDING)}"
    )
    assert not PENDING - hits, f"converted, so drop from PENDING: {sorted(PENDING - hits)}"
