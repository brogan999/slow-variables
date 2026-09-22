import re
from pathlib import Path

from ai_tracker.format import fmt

TABLE = [
    (0.063, "share", "6.3%"),
    (0.2247, "pts_a_year", "22.5 pts a year"),
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
    (9, "months", "9 months"),
    (4.3693, "months", "4.4 months"),
    (24.0, "count", "24"),
    (2028.0, "year", "2028"),
    (2025.84, "year", "2025.8"),
    (12345, "count", "12,345"),
    (7077, None, "7077"),
    (95_311, None, "95,311"),
    (0.85, "index", "0.85 index"),
    (112.5, "MW", "113 MW"),  # a tie rounds up, as toFixed does in the browser; Python's own format gives 112
    (2.5, "count", "3"),
    (197812.5, "wafers", "197,813 wafers"),
    (58.84, "pct", "58.8%"),
    (0.0625, "ratio", "0.063×"),
    (0.05, "ratio", "0.050×"),
    (float("inf"), "ratio", "—"),
    (None, "USD", "—"),
]


def test_values_read_the_way_the_site_renders_them():
    for value, unit, want in TABLE:
        assert fmt(value, unit) == want, (value, unit)
    # a value past the decimal context's reach still prints, never raises
    assert fmt(3e30, "count").replace(",", "").isdigit()


def test_every_unit_the_web_formatter_names_is_handled_here():
    ts = Path("web/src/lib/format.ts").read_text()
    body = ts[ts.index("export function fmt") : ts.index("export const words")]
    units = {u for m in re.finditer(r'case "([a-z_]+)":', body) for u in [m.group(1)]}
    py = Path("src/ai_tracker/format.py").read_text()
    missing = [u for u in units if f'"{u}"' not in py]
    assert not missing, f"web formats these units and Python does not: {missing}"
