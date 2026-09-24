"""The singularity timeline (plan Part 17): dated forecasts of AI milestones, placed on one year axis by lane, each
read against tonight's indicators. The forecasts themselves are ledger predictions (seed/predictions.yaml, ledger
`singularity`, in the site's words), so they carry statuses with reasons and sit on the board and in the predictions
table like every other prediction. This module adds only what a timeline needs: lanes, the stated years, the ten
things to watch, the four worlds (read through the outlook's scenario grid) and an unscored lane of fiction."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from . import argument, board
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
    return {
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
