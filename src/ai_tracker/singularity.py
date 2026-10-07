"""The singularity timeline (plan Part 17): dated forecasts of AI milestones, placed on one year axis by lane, each
read against tonight's indicators. The forecasts themselves are ledger predictions (seed/predictions.yaml, ledger
`singularity`, in the site's words), so they carry statuses with reasons and sit on the board and in the predictions
table like every other prediction. This module adds only what a timeline needs: lanes, the stated years, the ten
things to watch, the four worlds (read through the outlook's scenario grid) and an unscored lane of fiction."""

from __future__ import annotations

import itertools
import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from . import argument, board, futures
from .outlook import source_problems

SPEC = Path(__file__).resolve().parents[2] / "seed" / "singularity.yaml"

# The year axis runs in five pieces, so the half-century that matters gets most of the width: a bin for anything
# before 1950, 1950 to 2020 compressed, 2020 to 2050 open, 2050 to 2100 compressed, and a bin for later or never.
PIECES = [(1950, 2020, 5.0, 30.0), (2020, 2050, 30.0, 80.0), (2050, 2100, 80.0, 94.0)]
BEFORE, AFTER = 2.5, 97.5
TICKS = [1950, 1970, 1990, 2020, 2025, 2030, 2035, 2040, 2045, 2050, 2075, 2100]


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def x(year: float) -> float:
    """A year's place on the axis, in percent of the width; anything after 2100 sits in the last bin."""
    if year > PIECES[-1][1]:
        return AFTER
    if year < PIECES[0][0]:
        return BEFORE
    for lo, hi, a, b in PIECES:
        if lo <= year <= hi:
            return round(a + (b - a) * (year - lo) / (hi - lo), 2)
    return AFTER  # unreachable: the pieces cover 1950 to 2100


def _year(d: date | str | None) -> float | None:
    if d is None:
        return None
    d = date.fromisoformat(d) if isinstance(d, str) else d
    return d.year + (d.timetuple().tm_yday - 1) / 365.25


def axis() -> dict[str, Any]:
    return {
        "ticks": [{"year": y, "x": x(y)} for y in TICKS],
        "breaks": [p[2] for p in PIECES[1:]],  # where the scale changes, marked on the plate
        "bins": [{"label": "before 1950", "x": BEFORE}, {"label": "after 2100", "x": AFTER}],
    }


TABLE_LANES = ["superhuman_coder", "automated_researcher", "agi", "superintelligence"]
WORDS = ["happening", "slower", "too_early"]  # the words a ledger status can map to (board.WORDS["ledger"])
GAP = 3.0  # percent of the axis two marks on one row must keep apart, so their glyphs never touch


def _stack(marks: list[dict[str, Any]]) -> int:
    """Give each placed mark the lowest row its whole stated range clears by GAP; return how many rows the lane needs."""
    ends: list[float] = []
    for m in sorted(marks, key=lambda m: (m.get("x_low") if m.get("x_low") is not None else m["x"], m["x"])):
        start = m.get("x_low") if m.get("x_low") is not None else m["x"]
        end = max(m["x"], m.get("x_high") or m["x"])
        row = next((i for i, e in enumerate(ends) if start - e >= GAP), len(ends))
        if row == len(ends):
            ends.append(end)
        else:
            ends[row] = end
        m["slot"] = row
    return max(len(ends), 1)


def _years(m: dict[str, Any]) -> str:
    if m["low"] and m["high"]:
        return f"{m['low']}–{m['high']}" + (f", most likely {m['mid']}" if m["mid"] else "")
    return str(m["mid"]) if m["mid"] else f"by {m['high']}"


def reading(s: Any, sign: str, facts: dict[str, Any], today: date) -> dict[str, Any] | None:
    if sign in facts:
        return facts[sign]
    return argument.fact(s, {"indicator": sign}, today)


def build(s: Any, today: date | None = None, outlook: dict[str, Any] | None = None) -> dict[str, Any]:
    spec = load()
    if not spec:
        return {}
    today = today or date.today()
    preds = {r["id"]: r for r in s._ledger_rows()}
    facts = {
        **((outlook or {}).get("facts") or {}),
        **argument.facts(s, {"facts": spec.get("facts") or {}}, today),
    }
    lanes, flat = [], []
    for lane in spec["lanes"]:
        marks = []
        for f in lane.get("forecasts") or []:
            p = preds[f["id"]]
            made = _year(p["claim_date"])
            end = _year(p.get("window_end"))
            mid = f.get("mid") or (_year(p["window_mid"]) if p.get("window_mid") else None)
            low, high = f.get("low"), f.get("high") or (int(end) if end else None)
            # None: a call with odds but no date, or one that doubts a date (a bet against it), listed rather than placed
            at = None if f.get("doubts") or f.get("odds") else mid or high
            word = board.WORDS["ledger"].get(p.get("status"), "too_early")
            m = {
                "id": p["id"],
                "who": p["claimant"],
                "line": p["claim_text"],
                "ledger": p["ledger"],
                "quoted": p["ledger"] != "singularity",  # the other ledgers keep the claimant's own words
                "made": p["claim_date"],
                "made_year": int(made),
                "step": bool(f.get("step")),  # a step toward the milestone, not a date for it
                "low": low,
                "mid": mid,
                "high": high,
                "x_low": x(low) if low else None,
                "x_high": x(high) if high else None,
                "x": x(at) if at is not None else None,
                "status": p.get("status"),
                "word": word,
                "settles": p.get("window_end"),
                "years": None,
                "href": f"/predictions#{p['id']}",
            }
            m["years"] = _years(m) if at is not None else None
            if m["x_low"] is not None and m["x_high"] is not None:
                m["span_width"] = round(m["x_high"] - m["x_low"], 2)
            marks.append(m)
            flat.append({**m, "lane": lane["id"]})
        marks.sort(key=lambda m: (m["x"] is None, m["x"] or 0, m["made"]))
        placed = [m for m in marks if m["x"] is not None]
        slots = _stack(placed)
        lanes.append(
            {
                "id": lane["id"],
                "label": lane["label"],
                "definition": lane["definition"],
                "forecasts": placed,
                "undated": [m for m in marks if m["x"] is None],
                "slots": slots,
                "signposts": [
                    {"id": k, "reading": reading(s, k, facts, today)} for k in lane.get("signposts") or []
                ],
            }
        )
    due = sorted(
        (m for m in flat if m["settles"] and m["settles"] < today.isoformat()), key=lambda m: m["settles"]
    )
    latest: dict[tuple[str, str], dict[str, Any]] = {}
    for m in (
        flat
    ):  # the brief's forecaster table: each forecaster's latest dated call on each milestone, since 2023
        if m["step"] or m["x"] is None or m["made"] < "2023-01-01":
            continue
        k = (re.sub(r"\s*\(.*\)$", "", m["who"]), m["lane"])
        if k not in latest or (m["made"], m["x"]) > (latest[k]["made"], latest[k]["x"]):
            latest[k] = m
    short = {la["id"]: la.get("short") or la["label"] for la in spec["lanes"]}
    cols = [c for c in TABLE_LANES if c in short]
    table: dict[str, dict[str, Any]] = {}
    for (who, lane_id), m in latest.items():
        if lane_id in cols:
            table.setdefault(who, {})[lane_id] = {
                "text": _years(m),
                "href": m["href"],
                "word": m["word"],
                "made": m["made"][:7],
                "x": m["x"],
            }
    rows = sorted(table.items(), key=lambda kv: (kv[1].get("agi", {}).get("x", 1000), kv[0]))
    stops = sorted({*spec.get("stops", []), today.year})
    tallies = {
        str(y): {w: sum(1 for m in flat if m["made_year"] <= y and m["word"] == w) for w in WORDS}
        for y in stops
    }
    cells = {
        (c["progress"], c["rules"]): c for c in ((outlook or {}).get("scenarios") or {}).get("cells") or []
    }
    names = {
        x["id"]: x.get("short") or x["who"]
        for x in [*((outlook or {}).get("sources") or []), *spec.get("sources", [])]
    }
    worlds = []
    for w in spec.get("worlds") or []:
        cs = [cells[(c["progress"], c["rules"])] for c in w["cells"] if (c["progress"], c["rules"]) in cells]
        worlds.append(
            {
                **w,
                "consistent": all(c["consistent"] for c in cs),
                "grid": w["cells"],
                "argued_by": [names.get(h, h) for h in w.get("argued_by") or []],
            }
        )
    fic_urls = {x["id"]: x["url"] for x in spec.get("sources") or []}
    fiction = sorted(
        (
            f
            | {
                "x": x(f["set_in_year"]) if f.get("set_in_year") else None,
                "url": fic_urls.get(f["source"]),
                "anchor": "fic-" + f["source"],
            }
            for f in spec.get("fiction") or []
        ),
        key=lambda f: (f.get("set_in_year") or 10**4, f["title"]),
    )
    fic_placed = [f for f in fiction if f["x"] is not None]
    fic_slots = _stack(fic_placed)
    out = {
        "as_of": today.isoformat(),
        "intro": spec.get("intro"),
        "axis": axis() | {"today": x(_year(today))},
        "lanes": lanes,
        "due": due,
        "table": {
            "cols": [{"id": c, "label": short[c]} for c in cols],
            "rows": [{"who": w, "cells": c} for w, c in rows],
        },
        "stops": stops,
        "tallies": tallies,
        "questions": [
            q | {"reading": reading(s, q["reads"], facts, today) if q.get("reads") else None}
            for q in spec.get("questions") or []
        ],
        "worlds": worlds,
        "fiction": fiction,
        "fiction_slots": fic_slots,
        "sources": [
            x
            for x in spec.get("sources") or []
            if x["id"] not in {f["source"] for f in spec.get("fiction") or []}
        ],
        "words": {w: board.load()["words"][w]["label"] for w in WORDS},
    }
    return out | {"figures": figures(out, (outlook or {}).get("scenarios") or {}, futures.ideas())}


BOX = (2.0, 1.9)  # percent of the plot two marks must keep apart, across and down, before one is set aside
SAID = (3.0, 25.0, 90.0)  # the year-said scale: 1960 to 2020 squeezed into the first quarter, 2020 to next year in the rest
# the year-given scale of the same plot, from its foot: the two decades most forecasts name get most of the height
GIVEN = [(1990, 2020, 0.0, 10.0), (2020, 2040, 10.0, 65.0), (2040, 2100, 65.0, 96.0)]
STATES = ["holding", "failing", "both", "untestable"]  # what a claim on the outlook can read
LAG_TOP = 10  # decades between imagining and building; anything longer shares the last bin


def _lin(v: float, lo: float, hi: float, a: float, b: float) -> float:
    return round(a + (b - a) * (v - lo) / (hi - lo), 2)


def _said_x(v: float, year: int) -> float:
    """Percent across the said-against-given plot for the date a forecast was made."""
    a, b, c = SAID
    return _lin(max(v, 1960), 1960, 2020, a, b) if v <= 2020 else _lin(v, 2020, year + 1, b, c)


def _at(m: dict[str, Any]) -> int:
    """The year the timeline places a forecast at: its most likely year, else the last year of its range."""
    return m["mid"] or m["high"]


def figures(doc: dict[str, Any], scenarios: dict[str, Any], ideas: list[dict[str, Any]]) -> dict[str, Any]:
    """What the page's figures draw, from the built page: it reads the lanes, the due list and the worlds and changes
    none of them. Every count and position is worked out here, so the web only places it."""
    year, today = int(doc["as_of"][:4]), _year(doc["as_of"])
    label = {la["id"]: la["label"] for la in doc["lanes"]}

    spread = []
    for la in doc["lanes"]:
        dated = sorted((m for m in la["forecasts"] if not m["step"]), key=lambda m: (_at(m), m["made"]))
        years = [_at(m) for m in dated]
        spread.append(
            {
                "id": la["id"],
                "label": la["label"],
                "n": len(la["forecasts"]) + len(la["undated"]),
                "n_dated": len(dated),
                "n_steps": len(la["forecasts"]) - len(dated),
                "n_undated": len(la["undated"]),
                "marks": [
                    {"id": m["id"], "who": m["who"], "made": m["made"][:4], "at": _at(m), "years": m["years"], "x": x(_at(m)),
                     "href": m["href"]}
                    for m in dated
                ],
                "first": years[0] if years else None,
                "last": years[-1] if years else None,
                "x": x(years[0]) if years else None,
                "w": round(x(years[-1]) - x(years[0]), 2) if years else 0,
                # no middle is worked out: a row's marks are deadlines, most likely years, range ends and years at odds
                "theme": la["id"] not in TABLE_LANES,  # a row that gathers different claims on one theme
            }
        )

    b = SAID[1]

    def said_x(v: float) -> float:
        return _said_x(v, year)

    def given_y(v: float) -> float:
        """Percent from the top of the plot; a year after the last piece sits on the top edge."""
        return next((round(100 - _lin(v, lo, hi, p, q), 2) for lo, hi, p, q in GIVEN if v <= hi), 0.0)

    marks: list[dict[str, Any]] = []
    for la in doc["lanes"]:
        if la["id"] not in TABLE_LANES:
            continue
        for m in la["forecasts"]:
            if m["step"]:
                continue
            ranged = bool(m["low"] and m["high"])
            marks.append(
                {
                    "id": m["id"], "who": m["who"], "lane": la["id"], "made": m["made"], "at": _at(m), "years": m["years"],
                    "word": m["word"], "href": m["href"], "x": said_x(_year(m["made"])), "x_made": said_x(_year(m["made"])), "y": given_y(_at(m)),
                    "y_low": given_y(m["low"]) if ranged else None, "y_high": given_y(m["high"]) if ranged else None,
                    "moved": False,
                }
            )  # fmt: skip
    marks.sort(key=lambda m: (m["made"], m["at"], m["id"]))
    # a mark that would cover an earlier one is set aside at the nearest free place, right or left, never right of
    # today, and says so (the web ties it back to x_made)
    for i, m in enumerate(marks):
        tries = (m["x_made"] + sign * k * BOX[0] for k in itertools.count(1) for sign in (1, -1))
        while m["x"] > said_x(today) or any(abs(m["x"] - p["x"]) < BOX[0] and abs(m["y"] - p["y"]) < BOX[1] for p in marks[:i]):
            m["x"], m["moved"] = round(next(tries), 2), True
    four = [la for la in doc["lanes"] if la["id"] in TABLE_LANES]
    said = {
        "marks": marks,
        "n": len(marks),
        "n_moved": sum(1 for m in marks if m["moved"]),
        "y_breaks": [given_y(lo) for lo, _, _, _ in GIVEN[1:]],  # where the scale up the side changes
        "lanes": [{"id": la["id"], "label": la["label"]} for la in four],
        "left_out": {
            "steps": sum(1 for la in four for m in la["forecasts"] if m["step"]),
            "undated": sum(len(la["undated"]) for la in four),
        },
        # a phone has no room for the squeezed decades' middle ticks
        "x_ticks": [
            {"x": said_x(v), "label": str(v), "minor": v in (1980, 2000)}
            for v in [1960, 1980, 2000, 2020, *range(2022, year + 1, 2)]
        ],
        "y_ticks": [{"y": given_y(v), "label": str(v)} for v in (2000, 2020, 2025, 2030, 2035, 2040, 2060, 2080, 2100)],
        "break": b,
        "this_year": given_y(year),  # a mark below it names a year that has passed; a mark on it names this year
        # the year each forecast was made, as a year, drawn on the year-given scale: a step for each year, so nothing
        # can sit below it but the start of a stated range
        "said_line": " ".join(
            f"{said_x(v)},{given_y(v)} {said_x(min(v + 1, today))},{given_y(v)}" for v in range(GIVEN[0][0], year + 1)
        ),
    }

    rows = doc["due"]
    lo = min([m["made_year"] for m in rows] or [year]) // 10 * 10

    def due_x(v: float) -> float:
        return _lin(v, lo, year + 1, 2.0, 98.0)

    def named(m: dict[str, Any]) -> dict[str, Any]:
        return {"id": m["id"], "who": m["who"], "lane": label[m["lane"]], "line": m["line"], "quoted": bool(m.get("quoted")),
                "made": m["made"][:4], "years": m["years"], "word": m["word"], "step": m["step"], "href": m["href"]}  # fmt: skip

    due = {
        "rows": [
            named(m)
            | {
                "settles": m["settles"],
                "due": m["settles"][:4],
                "x_made": due_x(_year(m["made"])),
                "x_due": due_x(_year(m["settles"])),
                "w": round(due_x(_year(m["settles"])) - due_x(_year(m["made"])), 2),
                "x_low": due_x(m["low"]) if m["low"] else None,  # where a stated range of years begins
                "w_low": round(due_x(_year(m["settles"])) - due_x(m["low"]), 2) if m["low"] else None,
            }
            for m in rows
        ],
        "n": len(rows),
        "counts": {w: sum(1 for m in rows if m["word"] == w) for w in doc["words"]},
        "ticks": [{"year": v, "x": due_x(v)} for v in range(lo, year + 1, 20)],
        "today": due_x(today),
        # a year that has passed on a forecast with no closing date on record: not on this calendar, and named
        "unclosed": [
            named(m | {"lane": la["id"]}) for la in doc["lanes"] for m in la["forecasts"] if not m["settles"] and _at(m) < year
        ],
    }

    cell = {(k["progress"], k["rules"]): k for k in scenarios.get("cells") or []}
    names: dict[tuple[str, str], list[str]] = {}
    for w in doc["worlds"]:
        for k in w["grid"]:
            names.setdefault((k["progress"], k["rules"]), []).append(w["id"])

    def count(cells: list[dict[str, Any]]) -> dict[str, int]:
        return {s: sum(1 for k in cells for g in k["signposts"] if g["state"] == s) for s in STATES}

    world_rows = []
    for w in doc["worlds"]:
        mine = [cell[(k["progress"], k["rules"])] for k in w["grid"] if (k["progress"], k["rules"]) in cell]
        world_rows.append(
            {
                "id": w["id"],
                "label": w["label"],
                "short": w.get("short") or w["label"],
                "consistent": w["consistent"],  # the page's own word, unchanged
                "n_cells": len(mine),
                "open": sum(1 for k in mine if k["consistent"]),
                "bare": sum(1 for k in mine if not k["signposts"]),
                "states": count(mine),
            }
        )
    worlds = {
        "progress": scenarios.get("progress") or [],
        "rules": scenarios.get("rules") or [],
        "cells": [
            {
                "progress": p["id"],
                "rules": r["id"],
                "argued": (p["id"], r["id"]) in cell,
                "worlds": names.get((p["id"], r["id"]), []),
                "consistent": cell.get((p["id"], r["id"]), {}).get("consistent"),
                "tested": cell.get((p["id"], r["id"]), {}).get("tested"),
                "signs": cell.get((p["id"], r["id"]), {}).get("signposts", []),
            }
            for p in scenarios.get("progress") or []
            for r in scenarios.get("rules") or []
        ],
        "worlds": world_rows,
        "states": count(list(cell.values())),
        "bare": sum(1 for k in cell.values() if not k["signposts"]),
        "unplaced": sum(1 for k in cell if k not in names),
    }

    states = [i["arrival"]["state"] for i in ideas]
    # counted in decades, the grain most of the idea bank's dates have: the decade built less the decade imagined
    gaps = sorted(
        min((i["arrival"]["decade"] - i["imagined"] // 10 * 10) // 10, LAG_TOP)
        for i in ideas
        if i["arrival"]["state"] == "marked_built"
    )
    top = max((gaps.count(k) for k in range(LAG_TOP + 1)), default=0) or 1
    lag = {
        "bins": [
            {
                "key": str(k),
                "label": "the same decade" if k == 0 else f"{k} or more decades later" if k == LAG_TOP
                else f"{k} decade{'s' if k > 1 else ''} later",
                "n": gaps.count(k),
                "w": round(100 * gaps.count(k) / top, 1),
            }
            for k in range(LAG_TOP + 1)
        ],
        "n": len(gaps),
        "middle_key": str(gaps[(len(gaps) - 1) // 2]) if gaps else None,
        "exact": sum(1 for i in ideas if "lag_years" in i["arrival"]),
        "undated": states.count("marked_built_date_unclear"),
        "existed": states.count("already_existed"),
        "not_built": states.count("not_marked_built"),
        "ideas": len(ideas),
    }
    return {"spread": spread and {"lanes": spread}, "said": said, "due": due, "worlds": worlds, "lag": lag}


def problems(
    spec: dict[str, Any],
    predictions: list[Any],
    outlook_spec: dict[str, Any],
    indicator_ids: set[str],
    compare_ids: set[str],
    statuses: dict[str, str | None],
    today: date,
) -> list[str]:
    """Errors CI catches before the page names a forecast, reading or source it cannot resolve."""
    if not spec:
        return []
    errors = source_problems(spec.get("sources") or [], "singularity")
    by_id = {p.id: p for p in predictions}
    ours = {p.id for p in predictions if p.ledger == "singularity" and p.published}
    urls = [x["url"] for x in spec.get("sources") or []]
    outlook_urls = {x["url"] for x in outlook_spec.get("sources") or []}
    errors += [f"singularity: source url {u} is also an outlook source" for u in set(urls) & outlook_urls]
    errors += [f"singularity: source url {u} is listed twice" for u in {u for u in urls if urls.count(u) > 1}]
    known_urls = set(urls) | outlook_urls
    known_facts = set(spec.get("facts") or {}) | set(outlook_spec.get("facts") or {})
    placed: set[str] = set()
    for lane in spec.get("lanes") or []:
        for f in lane.get("forecasts") or []:
            if f["id"] not in by_id:
                errors.append(f"singularity: lane {lane['id']} places unknown prediction {f['id']}")
            placed.add(f["id"])
        for k in lane.get("signposts") or []:
            if k not in known_facts | indicator_ids:
                errors.append(f"singularity: lane {lane['id']} signpost {k} is no fact or indicator")
    errors += [f"singularity: prediction {k} sits on no lane" for k in sorted(ours - placed)]
    for k in sorted(ours):
        p = by_id[k]
        if p.claim_url not in known_urls:
            errors.append(f"singularity: {k} links to a url no source records as fetched")
        if k in compare_ids:
            errors.append(f"singularity: {k} is listed in compare.yaml, whose four columns cannot show it")
        if p.window_start and p.window_start > today and statuses.get(k) not in (None, "not_yet_testable"):
            errors.append(f"singularity: {k} has not opened its window, so it reads not_yet_testable")
    for q in spec.get("questions") or []:
        if q.get("reads") and q["reads"] not in known_facts | indicator_ids:
            errors.append(f"singularity: question '{q['id']}' reads {q['reads']}, no fact or indicator")
    cells = {(c["progress"], c["rules"]) for c in (outlook_spec.get("scenarios") or {}).get("cells") or []}
    for w in spec.get("worlds") or []:
        errors += [
            f"singularity: world {w['id']} names no grid cell {c['progress']} x {c['rules']}"
            for c in w.get("cells") or []
            if (c["progress"], c["rules"]) not in cells
        ]
    srcs = {x["id"] for x in spec.get("sources") or []} | {x["id"] for x in outlook_spec.get("sources") or []}
    for w in spec.get("worlds") or []:
        errors += [
            f"singularity: world {w['id']} names unknown source {h}"
            for h in w.get("argued_by") or []
            if h not in srcs
        ]
    errors += [
        f"singularity: fiction {f['title']} names unknown source {f.get('source')}"
        for f in spec.get("fiction") or []
        if f.get("source") not in srcs
    ]
    return errors


def strings(spec: dict[str, Any]) -> list[str]:
    """Every sentence the section puts in front of a reader, for the no-figure tests."""
    out = [spec.get("intro") or ""]
    out += [lane[k] for lane in spec.get("lanes") or [] for k in ("label", "definition")]
    out += [q[k] for q in spec.get("questions") or [] for k in ("question", "fast", "slow") if q.get(k)]
    out += [w[k] for w in spec.get("worlds") or [] for k in ("label", "text")]
    out += [f["line"] for f in spec.get("fiction") or []]
    return [t for t in out if t]
