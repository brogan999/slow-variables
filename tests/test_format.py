import re
from pathlib import Path

from ai_tracker.format import fmt

TABLE = [
    (0.063, "share", "6.3%"),
    (-3.4, "pct_change_yoy", "-3.4%"),
    (172_000_000_000, "USD", "$172B"),
    (2_575_000_000, "USD", "$2.6B"),
    (762_000_000, "USD", "$762M"),
    (5_400, "USD", "$5.4k"),
    (0.0057, "USD", "$0.0057"),
    (6.342778, "ratio", "6.34×"),
    (1044.78, "minutes", "17.4 h"),
    (31.0, "minutes", "31.0 min"),
    (107.99, "days", "108 days"),
    (24.0, "count", "24"),
    (7077, None, "7077"),
    (95_311, None, "95,311"),
    (0.85, "index", "0.85 index"),
    (None, "USD", "—"),
]


def test_values_read_the_way_the_site_renders_them():
    for value, unit, want in TABLE:
        assert fmt(value, unit) == want, (value, unit)


def test_every_unit_the_web_formatter_names_is_handled_here():
    ts = Path("web/src/lib/format.ts").read_text()
    body = ts[ts.index("export function fmt") : ts.index("export const tick")]
    units = {u for m in re.finditer(r'case "([a-z_]+)":', body) for u in [m.group(1)]}
    py = Path("src/ai_tracker/format.py").read_text()
    missing = [u for u in units if f'"{u}"' not in py]
    assert not missing, f"web formats these units and Python does not: {missing}"
