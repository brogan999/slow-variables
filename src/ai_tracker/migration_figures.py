"""The drawn figures on /argument/migration, laid out here so the web only places them. Every block summarises records
the page already holds (the scorecard, the acquisitions tally's newest derived row, each gauge's age); the chain is a
model drawn from seed words on a fixed scale, with no figure of its own."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING, Any

from .analysis.tightness import score_input
from .chart import MONTHS

if TYPE_CHECKING:
    from .store import Store

DEALS = "lab_vertical_integration_events_4q"
# the chain's drawing rule: how tall a link stands for each word the seed gives it (percent of the plot)
DRAWN = {"short": 24, "little": 42, "some": 66, "plenty": 92}
# a reading with under a tenth of its age limit left is "near its limit", the line `check` already warns at
NEAR = 0.9
# the essay's conjecture names one group of unscored inputs: those nobody publishes a series for
CONJECTURE = "no_public_series"
REASONS = ("no_public_series", "not_read_yet", "gauge_unsound", "stale_or_thin")
BUYER_KINDS = {"model": "labs", "compute_physical": "computing and cloud companies"}


def _day(d: date) -> str:
    return f"{d.day} {MONTHS[d.month - 1]} {d.year}"


def chain(spec: dict[str, Any]) -> dict[str, Any]:
    states, before = [], {}
    for st in spec["states"]:
        hs = {x["id"]: DRAWN[st["levels"][x["id"]]] for x in spec["links"]}
        states.append(
            {
                "id": st["id"],
                "title": st["title"],
                "text": st["text"],
                "level": min(hs.values()),
                "links": [
                    {
                        **x,
                        "word": st["levels"][x["id"]],
                        "h": hs[x["id"]],
                        "shortest": hs[x["id"]] == min(hs.values()),
                        "was": before[x["id"]] if before and before[x["id"]] != hs[x["id"]] else None,
                    }
                    for x in spec["links"]
                ],
            }
        )
        before = hs
    return {"states": states, "between": spec["between"], "drawn": DRAWN}


def scale(card: dict[str, Any]) -> dict[str, Any]:
    floors = sorted(card["method"]["words"])
    ends = [f for f, _ in floors[1:]] + [100]
    scored = sorted((i for i in card["inputs"] if i["score"] is not None), key=lambda i: (-i["score"], i["n"]))
    return {
        "bands": [{"word": w, "x": f, "w": e - f} for (f, w), e in zip(floors, ends)],
        "rows": [
            {**{k: i[k] for k in ("id", "n", "name", "kind", "score", "word", "hatched", "confidence", "obs_ids")}, "x": i["score"]}
            for i in scored
        ],
        "unscored": [{k: i[k] for k in ("id", "n", "name")} for i in card["inputs"] if i["score"] is None],
        "total": card["total"],
    }


def blind(card: dict[str, Any]) -> dict[str, Any]:
    unscored = [i for i in card["inputs"] if i["score"] is None]
    groups = [
        {
            "kind": k,
            "conjecture": k == CONJECTURE,
            "inputs": [{"id": i["id"], "n": i["n"], "name": i["name"]} for i in unscored if i["withheld"]["kind"] == k],
        }
        for k in REASONS
    ]
    return {"groups": [{**g, "n": len(g["inputs"])} for g in groups if g["inputs"]], "total": len(unscored)}


def deals(s: Store) -> dict[str, Any] | None:
    """One mark for each deal the tally's newest reading counted, by buyer and by the quarter it was announced in.
    The deals are that derived row's own input rows, grouped as the metric groups them (buyer and target)."""
    rows = s.derived_for(DEALS)
    if not rows:
        return None
    d = rows[-1]
    obs = s.con.execute(
        "SELECT subject, measure, min(as_of_date), list(id ORDER BY id), min(series_key) FROM observations"
        " WHERE id IN (SELECT unnest(?)) GROUP BY 1, 2 ORDER BY 3, 1, 2",
        [d.input_observation_ids],
    ).fetchall()
    ends = [d.as_of_date]
    for _ in range(3):  # the four quarters the reading covers, oldest first
        ends.insert(0, ends[0].replace(day=1) - timedelta(days=62))
        ends[0] = (ends[0].replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    def quarter(day: date) -> str:
        return f"{day.year}-Q{(day.month - 1) // 3 + 1}"

    quarters = [
        {"id": quarter(e), "label": f"{MONTHS[e.month - 3]} to {MONTHS[e.month - 1]} {e.year}", "months": f"{MONTHS[e.month - 3]}–{MONTHS[e.month - 1]}", "year": str(e.year), "n": sum(1 for o in obs if quarter(o[2]) == quarter(e))}
        for e in ends
    ]
    names = {e.id: e.name for e in s.seed.entities}
    layer = {e.id: next((m.layer_id for m in e.memberships if m.is_primary), None) for e in s.seed.entities}
    buyers = []
    for b in dict.fromkeys(o[0] for o in obs):
        mine = [o for o in obs if o[0] == b]
        buyers.append(
            {
                "id": b,
                "name": names[b],
                "kind": layer[b],
                "n": len(mine),
                "cells": [
                    {
                        "quarter": q["id"],
                        "deals": [
                            {"target": o[1], "date": o[2].isoformat(), "day": _day(o[2]), "obs_ids": o[3], "href": f"/series/{o[4]}#{o[3][0]}"}
                            for o in mine
                            if quarter(o[2]) == q["id"]
                        ],
                    }
                    for q in quarters
                ],
            }
        )
    buyers.sort(key=lambda b: (-b["n"], b["name"]))
    return {
        "total": {"value": d.value, "unit": "count", "as_of": d.as_of_date.isoformat(), "obs_ids": d.input_observation_ids, "derived_id": d.id, "href": "/indicators/lab_vertical_integration_exit_bell"},
        "quarters": quarters,
        "kinds": [{"id": k, "label": label, "n": sum(b["n"] for b in buyers if b["kind"] == k)} for k, label in BUYER_KINDS.items()],
        "buyers": buyers,
        "chart_sources": s._chart_sources(d.input_observation_ids),
    }


def after(inp: dict[str, Any], readings: dict[str, dict[str, Any]], drop: set[str], rules: dict[str, Any]) -> dict[str, Any] | None:
    """The input's score by the page's own rule once the readings in `drop` no longer count; None when withheld."""
    r = score_input(inp, {k: v for k, v in readings.items() if k not in drop}, rules)
    return None if r["score"] is None else {"score": r["score"], "word": r["word"]}


def ages(card: dict[str, Any], spec: dict[str, Any], today: date) -> dict[str, Any]:
    seed = {i["id"]: i for i in spec["inputs"]}
    rows = []
    for i in card["inputs"]:
        if i["score"] is None:
            continue
        readings = {g["id"]: {"x": g["reading"]["value"], "age": g["age_days"], "grade": g["grade"]} for g in i["gauges"] if g["reading"]}
        gauges = []
        for g in i["gauges"]:
            if g["points"] is None:
                continue
            last = today + timedelta(days=g["max_age_days"] - g["age_days"])
            gauges.append(
                {
                    **{k: g[k] for k in ("id", "label", "age_days", "max_age_days")},
                    "x": round(100 * g["age_days"] / g["max_age_days"], 2),
                    "near": g["age_days"] > NEAR * g["max_age_days"],
                    "last": last.isoformat(),
                    "last_label": _day(last),
                    "as_of": g["reading"]["as_of"],
                    "obs_ids": g["reading"]["obs_ids"],
                    "href": g["reading"]["href"],
                }
            )
        rows.append(
            {
                **{k: i[k] for k in ("id", "n", "name", "score", "word")},
                "gauges": gauges,
                "after": after(seed[i["id"]], readings, {g["id"] for g in gauges if g["near"]}, spec["rules"]),
            }
        )
    return {
        "near_share": NEAR,
        "near_x": 100 * NEAR,
        "rows": rows,
        "near": sum(1 for r in rows for g in r["gauges"] if g["near"]),
        "scored_now": len(rows),
        "scored_after": sum(1 for r in rows if r["after"] is not None),
    }


def build(s: Store, block: dict[str, Any], card: dict[str, Any], tightness: dict[str, Any], today: date) -> dict[str, Any]:
    return {"chain": chain(block["chain"]), "scale": scale(card), "blind": blind(card), "deals": deals(s), "ages": ages(card, tightness, today)}
