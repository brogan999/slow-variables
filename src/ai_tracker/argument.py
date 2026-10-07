"""The opening argument as data: facts for the essays' [fact:id] tokens, the five slow variables, the clocks plate,
the Perez phase and the exits. The essays never type a number; `problems` re-tests every sentence's premise nightly."""

from __future__ import annotations

import re
from datetime import date, timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .store import Store

SPEC = Path("seed/argument.yaml")
TIGHTNESS = Path("seed/tightness.yaml")
ESSAYS = {
    "home": Path("docs/argument/home.md"),
    "full": Path("docs/argument/full.md"),
    "migration": Path("docs/argument/migration.md"),
}
# the fuller case record behind Folio IV, shown on /argument as a fold-out and read by Ask's evidence search
RECORD = Path("docs/interpretation/past-technology-waves.md")
# each essay's own plates and facts: the migration essay keeps its facts apart, so the home page's date never moves
PLATES = {
    "home": {"clocks", "perez", "stack"},
    "full": {"clocks", "perez", "stack", "record", "map", "readings", "exits"},
    "migration": {"strip", "scorecard", "chain", "scale", "deals", "ages", "blind"},
}
STATES = ("holding", "failing", "untestable")
OPS = ("gt", "gte", "lt", "lte")


def unfetched(x: dict[str, Any]) -> str | None:
    """Why a source's URL lacks proof it was read: the day it was fetched, a 200, and a hash of what came back."""
    if (
        not isinstance(x.get("retrieved_at"), date)
        or not isinstance(x.get("http_status"), int)
        or not re.fullmatch(r"[0-9a-f]{64}", str(x.get("content_hash") or ""))
    ):
        return "has no fetch record (retrieved_at, http_status, content_hash)"
    if x.get("http_status") != 200:
        return f"answered {x.get('http_status')} when fetched; link a copy that loads"
    return None


def _bad_test(test: dict[str, Any] | None, known: dict[str, Any]) -> str | None:
    """Why an `expect` or a prediction's test cannot be run, checked whether or not a reading exists tonight."""
    if not test:
        return None
    if len(test) != 1 or next(iter(test)) not in OPS:
        return "needs exactly one of gt, gte, lt, lte"
    rhs = next(iter(test.values()))
    return f"is tested against unknown fact {rhs}" if isinstance(rhs, str) and rhs not in known else None


TOKEN = re.compile(r"\[(fact|plate):([a-z0-9_]+)\]")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text())


def _metric_href(s: Store, metric: str) -> str:
    ind = next(
        (i for i in s.seed.indicators if i.published and metric in (i.metric, (i.band_input or "")[7:])), None
    )
    return (
        f"/indicators/{ind.id}" if ind else f"/query#{metric}"
    )  # /query anchors each saved analysis by its metric


def fact(s: Store, spec: dict[str, Any], today: date | None = None) -> dict[str, Any] | None:
    if (
        "series" in spec
    ):  # one published figure, read straight from its series: the newest numeric row not in dispute
        rows = s.con.execute(
            "SELECT id, value_numeric, unit, as_of_date FROM observations WHERE series_key = ? AND value_numeric IS NOT NULL"
            " AND NOT coalesce(disputed, false) AND as_of_date <= ? ORDER BY as_of_date DESC, id",
            [spec["series"], today or date.today()],
        ).fetchall()
        row = rows[0] if rows else None
        if row and spec.get("pick") == "year_ago":  # the row a year before the newest, as for a metric
            row = next((r for r in rows if 355 <= (rows[0][3] - r[3]).days <= 375), None)
        if not row:
            return None
        return {
            "value": row[1],
            "unit": row[2],
            "as_of": row[3].isoformat(),
            "obs_ids": [row[0]],
            "href": f"/series/{spec['series']}#{row[0]}",
        }
    if "indicator" in spec:
        ind = next(i for i in s.seed.indicators if i.id == spec["indicator"])
        pts = s.headline(ind)
        if not pts:
            return None
        p = pts[-1]
        return {
            "value": p["value"],
            "unit": p["unit"],
            "as_of": p["as_of"],
            "obs_ids": p["obs_ids"],
            "href": f"/indicators/{ind.id}",
        }
    rows = s.derived_for(spec["metric"], spec.get("dims"))
    if spec.get("since"):  # only readings from a date on, such as the day a bet was agreed
        rows = [r for r in rows if r.as_of_date >= date.fromisoformat(str(spec["since"]))]
    if not rows:
        return None
    d = rows[-1]
    if spec.get("pick") == "max":  # the best reading in the window: a bet settled by any quarter stays settled
        d = max(reversed(rows), key=lambda r: r.value)
    if spec.get("pick") == "quarter_end":  # the latest reading dated on a calendar quarter's last day
        d = next(
            (
                r
                for r in reversed(rows)
                if (r.as_of_date + timedelta(days=1)).day == 1 and r.as_of_date.month in (3, 6, 9, 12)
            ),
            None,
        )
        if d is None:
            return None
    if spec.get("pick") == "year_ago":  # exactly a year back, give or take a quarter-end's calendar drift
        d = next((r for r in reversed(rows) if 355 <= (rows[-1].as_of_date - r.as_of_date).days <= 375), None)
        if d is None:
            return None
    return {
        "value": d.value,
        "unit": s.metric_spec(spec["metric"]).get("unit"),
        "as_of": min(
            d.as_of_date, today or date.today()
        ).isoformat(),  # a quarter still running is dated today
        "obs_ids": d.input_observation_ids,
        "derived_id": getattr(d, "id", None),
        "href": _metric_href(s, spec["metric"]),
    } | ({"newest": min(rows[-1].as_of_date, today or date.today()).isoformat()} if spec.get("pick") == "max" else {})


def _holds(expect: dict[str, Any] | None, value: float, other: dict[str, float | None]) -> bool | None:
    if not expect:
        return None
    ((op, rhs),) = expect.items()
    rhs = other.get(rhs) if isinstance(rhs, str) else rhs
    if rhs is None:
        return None
    return {"gt": value > rhs, "gte": value >= rhs, "lt": value < rhs, "lte": value <= rhs}[op]


def facts(
    s: Store, spec: dict[str, Any], today: date | None = None, computed: dict[str, Any] | None = None
) -> dict[str, dict[str, Any] | None]:
    """`computed` supplies facts worked out at export (the scorecard's count). A fact with `max_age_days` that has
    aged past it is marked stale and its `expect` is not tested: a falsifier on a frozen series would hold for ever."""
    today = today or date.today()
    out = {
        k: (dict(computed[v["computed"]]) if "computed" in v else fact(s, v, today))
        if "computed" not in v or (computed or {}).get(v["computed"], {}).get("value") is not None
        else None
        for k, v in spec["facts"].items()
    }
    values = {k: (f["value"] if f else None) for k, f in out.items()}
    for k, f in out.items():
        if not f:
            continue
        v = spec["facts"][k]
        f["holds"] = _holds(v.get("expect"), f["value"], values)
        if "max_age_days" in v and f["as_of"]:
            age = _age(s, date.fromisoformat(f["as_of"]), today, v.get("fetched_from"))
            if age > v["max_age_days"]:
                f["stale"], f["holds"] = True, None
    return out


def clocks(s: Store, spec: dict[str, Any]) -> dict[str, Any]:
    c = spec["clocks"]
    start = str(c["start"])
    drawn, listed = [], []
    for link in c["links"]:
        ind = next(i for i in s.seed.indicators if i.id == link["id"])
        # a disputed reading (METR's above its suite's ceiling, say) never sets a line's shape
        mine = [
            p for p in s.headline(ind) if fnmatch(p["series_key"], link["series"]) and not p.get("disputed")
        ]
        pts = [p for p in mine if p["as_of"] >= start]
        if link.get("frontier"):  # the running best, starting from the best reading before the start date
            before = [p for p in mine if p["as_of"] < start]
            best: list[dict[str, Any]] = [max(before, key=lambda p: p["value"])] if before else []
            for p in pts:
                if not best or p["value"] > best[-1]["value"]:
                    best.append(p)
            pts = best
        if len(pts) < 3 or pts[0]["value"] is None or pts[0]["value"] <= 0:
            listed.append(link["id"])
            continue
        first, last = pts[0], pts[-1]
        drawn.append(
            {
                **link,
                "name": ind.name,
                "unit": ind.unit,
                "from": first["as_of"],
                "series": [{"as_of": p["as_of"], "value": p["value"], "obs_ids": p["obs_ids"]} for p in pts],
                "multiple": {
                    "value": last["value"] / first["value"],
                    "unit": "ratio",
                    "as_of": last["as_of"],
                    "obs_ids": first["obs_ids"] + last["obs_ids"],
                    "href": f"/indicators/{ind.id}",
                },
            }
        )
    mult = {d["id"]: d["multiple"]["value"] for d in drawn}
    a, b = c.get("expect", {}).get("gt", [None, None])
    holds = mult[a] > mult[b] if a in mult and b in mult else None
    return {
        "start": start,
        "drawn": drawn,
        "listed": listed,
        "holds": holds,
        "chart": _lay_clocks(s, drawn) if drawn else None,
        "chart_sources": s._chart_sources([i for d in drawn for p in d["series"] for i in p["obs_ids"]]),
    }


def _lay_clocks(s: Store, drawn: list[dict[str, Any]]) -> dict[str, Any]:
    """Every line as a multiple of its own first reading, on one log axis whose dates cover every point (a line
    that starts from the best reading before the start date starts where its first point is, not off the axis).
    Positions and the end labels' places are written onto the series; labels are nudged apart, never overlapped."""
    from . import chart

    when = [date.fromisoformat(p["as_of"]) for d in drawn for p in d["series"]]
    xa = chart.time_axis(when)
    for d in drawn:
        for p in d["series"]:
            p["multiple"] = p["value"] / d["series"][0]["value"]
    ya = chart.axis([p["multiple"] for d in drawn for p in d["series"]] + [1.0], "ratio", log=True)
    for d in drawn:
        for p in d["series"]:
            p["x"], p["y"] = (
                chart.x(date.fromisoformat(p["as_of"]), xa["lo"], xa["hi"]),
                chart.y(p["multiple"], ya),
            )
            p["href"] = s.href_of(p["obs_ids"])
        d["stamp"] = s.stamp_of([i for p in d["series"] for i in p["obs_ids"]])
    ends = sorted(drawn, key=lambda d: d["series"][-1]["y"])
    for d, y in zip(ends, chart.spread([d["series"][-1]["y"] for d in ends], 10.0)):
        d["label_y"] = y
    return {
        "x": {"ticks": xa["ticks"]},
        "y": {
            **{k: ya[k] for k in ("ticks", "log")},
            "unit": "multiple of its first reading",
            "chars": max(len(t["label"]) for t in ya["ticks"]),
        },
    }


# Perez's two halves, and the phases inside them. When the finer phase cannot be told apart, the half is shown.
HALF = {"irruption": "installation", "frenzy": "installation", "installation": "installation",
        "turning_point": "turning_point", "synergy": "deployment", "maturity": "deployment",
        "deployment": "deployment", "untestable": "untestable"}


def _raw_phase(capex: float, fin: float | None, fin_year_ago: float | None, after_frenzy: bool = False) -> str:
    """Spending per dollar of measured AI revenue, and seller-funded deals in the trailing year against the year
    before. Frenzy when spending runs ahead and those deals are growing; once a frenzy has been confirmed, a cooling
    reads as the turning point, never back to irruption. Synergy and maturity need a revenue-growth reading the site
    does not yet hold, so deployment is shown as the half."""
    if fin is None:
        return "untestable"
    if capex >= 1:
        if fin_year_ago is None:
            return "installation"
        if fin > fin_year_ago:
            return "frenzy"
        return "turning_point" if after_frenzy else "irruption"
    if capex < 0.5 and fin_year_ago is not None and fin <= fin_year_ago:
        return "deployment"
    return "turning_point"


def phase(s: Store, spec: dict[str, Any]) -> dict[str, Any]:
    p = spec["phase"]
    capex = s.derived_for(p["capex"])
    fin = {d.as_of_date: d for d in s.derived_for(p["financing"])}
    searched = date.fromisoformat(str(p["financing_searched_from"])) if p.get("financing_searched_from") else None

    def fin_at(day: date) -> Any:
        """The flow read at that quarter end, else the latest reading inside the quarter."""
        return fin.get(day) or max(
            (d for k, d in fin.items() if day - timedelta(days=92) < k <= day),
            key=lambda d: d.as_of_date,
            default=None,
        )

    history: list[dict[str, Any]] = []
    state = None
    for c in capex:
        ago = c.as_of_date.replace(year=c.as_of_date.year - 1)
        f = fin_at(c.as_of_date)
        # a year-ago flow counts only when the whole year behind it was searched
        f0 = fin_at(ago) if searched is None or ago.replace(year=ago.year - 1) + timedelta(days=1) >= searched else None
        raw = _raw_phase(c.value, f.value if f else None, f0.value if f0 else None,
                         after_frenzy=any(h["state"] == "frenzy" for h in history))
        if state is None or (raw != state and history and history[-1]["raw"] == raw):
            state = raw
        history.append({"as_of": c.as_of_date.isoformat(), "raw": raw, "state": state})
    ids = (capex[-1].input_observation_ids if capex else []) + (
        max(fin.values(), key=lambda d: d.as_of_date).input_observation_ids if fin else []
    )
    cs = s._chart_sources(ids)
    if not capex or not fin:
        return {
            "state": "untestable",
            "half": "untestable",
            "rule": p["rule"],
            "as_of": None,
            "history": history,
            "chart_sources": cs,
        }
    return {
        "state": state,
        "half": HALF[state],
        "rule": p["rule"],
        "as_of": history[-1]["as_of"],
        "history": history,
        "chart_sources": cs,
    }


def exits(spec: dict[str, Any]) -> list[dict[str, Any]]:
    from .store import DATA, read_jsonl

    states = {v["id"]: v.get("state") for v in read_jsonl(DATA / "thesis.jsonl")}
    return [
        {
            "monitor": e["monitor"],
            "label": e.get("label"),
            "text": e["text"],
            "state": states.get(e["monitor"]),
        }
        for e in spec["exits"]
    ]


def headlines(spec: dict[str, Any], fast: set[str] | None = None) -> dict[str, dict[str, Any]]:
    """Each lens page's headline: the claim its monitor's current state supports, in the words the seed gives.
    `fast` holds the buckets with a published indicator reading faster than normal: a claim may name its bucket in
    `when_fast`, so a page whose cards show fast capability never reads as if nothing were fast."""
    from .store import DATA, read_jsonl

    states = {v["id"]: v.get("state") for v in read_jsonl(DATA / "thesis.jsonl")}
    out = {}
    for page, h in spec["headlines"].items():
        state = states.get(h["monitor"]) or "untestable"
        claim = h["claims"].get(state) or h["claims"]["untestable"]
        for bucket, alt in (h.get("when_fast") or {}).get(state, {}).items():
            if bucket in (fast or set()):
                claim = alt
        out[page] = {"monitor": h["monitor"], "state": state, "claim": claim}
    return out


def essay_shape(text: str) -> list[str]:
    """What the page renderer needs: a title, a lede, then folios each opened by one label and one claim."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    bad = []
    if not blocks or not blocks[0].startswith("# "):
        bad.append("does not open with a '# ' title")
    folio = None
    for b in blocks[2:]:
        if b.startswith("### "):
            if folio is not None and not folio["claim"]:
                bad.append(f"folio '{folio['label']}' has no '## ' claim")
            folio = {"label": b[4:], "claim": False}
        elif b.startswith("## "):
            if folio is None:
                bad.append("a '## ' claim comes before any '### ' folio label")
            elif folio["claim"]:
                bad.append(f"folio '{folio['label']}' has two '## ' claims")
            else:
                folio["claim"] = True
        elif folio is None:
            bad.append("text between the lede and the first folio would be dropped")
    if folio is not None and not folio["claim"]:
        bad.append(f"folio '{folio['label']}' has no '## ' claim")
    return bad


def _age(s: Store, as_of: date, today: date, fetched_from: str | None = None) -> int:
    """Whole days since a reading was current. A series of change points (a price list) is as fresh as its source's
    last successful fetch, not as old as the last change."""
    ok = [x.finished_at.date() for x in s.fetchlog if fetched_from and x.source_id == fetched_from and x.ok]
    return max(0, (today - max([as_of, *ok])).days)


def _worst_grade(s: Store, ids: list[str]) -> str:
    from .store import _grade

    rows = s.con.execute(
        "SELECT DISTINCT tier, audited_vs_reported FROM observations WHERE id IN (SELECT unnest(?))", [ids]
    ).fetchall()
    return max((_grade({"tier": t, "audited_vs_reported": b}) for t, b in rows), default="D")


def scorecard(s: Store, today: date) -> dict[str, Any]:
    """The tightness scorecard: every gauge's newest metric reading, scored by analysis/tightness.py."""
    from .analysis.tightness import half_up, score_input

    spec = yaml.safe_load(TIGHTNESS.read_text())
    rules, inputs, all_ids, newest = spec["rules"], [], set(), []
    for inp in spec["inputs"]:
        readings, shown = {}, {}
        for g in inp.get("gauges") or []:
            rows = s.derived_for(g["metric"], g.get("dims")) if "metric" in g else []
            if not rows:
                continue
            d = rows[-1]
            age = _age(s, d.as_of_date, today, g.get("fetched_from"))
            grade = _worst_grade(s, d.input_observation_ids)
            readings[g["id"]] = {"x": d.value, "age": age, "grade": grade}
            shown[g["id"]] = {
                "reading": {
                    "value": d.value,
                    "unit": s.metric_spec(g["metric"]).get("unit"),
                    "as_of": min(d.as_of_date, today).isoformat(),
                    "obs_ids": d.input_observation_ids,
                    "derived_id": d.id,
                    "href": _metric_href(s, g["metric"]),
                },
                "age_days": age,
                "grade": grade,
            }
        r = score_input(inp, readings, rules)
        used = {g["id"] for g in r["gauges"] if g["points"] is not None}
        ids = sorted({i for k in used for i in shown[k]["reading"]["obs_ids"]})
        unfed = [g["unfed"] for g in inp.get("gauges") or [] if "unfed" in g]
        if r["withheld"] is None:
            why = None
            all_ids.update(ids)
            newest += [shown[k]["reading"]["as_of"] for k in used]
        elif "withheld" in inp:
            why = inp["withheld"]
        elif unfed and len(unfed) == len(inp["gauges"]):  # no gauge here has a metric: the seed's own reasons
            why = {"kind": unfed[0]["kind"], "because": " ".join(u["because"] for u in unfed)}
        else:
            why = {"kind": "stale_or_thin", "because": rules["reasons"][r["withheld"]]}
        gauges = []
        for g, row in zip(inp.get("gauges") or [], r["gauges"]):
            gauges.append(
                {
                    **{
                        k: g.get(k)
                        for k in (
                            "id",
                            "label",
                            "weight",
                            "max_age_days",
                            "knots",
                            "scale_rationale",
                            "unfed",
                        )
                    },
                    "required": bool(g.get("required")),
                    "log10": bool(g.get("log10")),
                    "unit": s.metric_spec(g.get("metric")).get("unit"),
                    "reading": None,
                    "age_days": None,
                    "grade": None,
                    **shown.get(g["id"], {}),
                    "points": None if row["points"] is None else half_up(row["points"]),
                    "pinned": row["pinned"],
                    "unavailable": row["unavailable"],
                }
            )
        inputs.append(
            {
                **{
                    k: inp.get(k)
                    for k in ("id", "n", "name", "kind", "what", "reads", "ceiling", "ceiling_rationale")
                },
                **{
                    k: r[k]
                    for k in (
                        "score",
                        "word",
                        "confidence",
                        "at_ceiling",
                        "hatched",
                        "used",
                        "defined",
                        "factors",
                    )
                },
                "obs_ids": ids if r["withheld"] is None else [],
                "withheld": why,
                "gauges": gauges,
            }
        )
    n = sum(1 for i in inputs if i["score"] is not None)
    return {
        "kinds": spec["kinds"],
        "inputs": inputs,
        "scored": {
            "value": n or None,  # no score anywhere is a gap, never a zero with nothing behind it
            "unit": "count",
            "as_of": max(newest, default=None),
            "obs_ids": sorted(all_ids),
            "href": "/methodology#tightness",
        },
        "total": len(inputs),
        # the one rule the methodology page prints as a percentage, worded here so the page computes nothing
        "method": {**rules, "min_coverage_label": f"{rules['min_coverage']:.0%}"},
        "chart_sources": s._chart_sources(sorted(all_ids)),
    }


def predictions(block: dict[str, Any], f: dict[str, dict[str, Any] | None]) -> list[dict[str, Any]]:
    """Each prediction carries its own test, a fact and one operator; one with no test says what would prove it wrong."""
    values = {k: (x["value"] if x else None) for k, x in f.items()}
    out = []
    for p in block["predictions"]:
        t = p.get("test")
        tested = f.get(t["fact"]) if t else None
        holds = None
        if tested and not tested.get("stale"):
            holds = _holds({k: v for k, v in t.items() if k != "fact"}, tested["value"], values)
        state = "untestable" if holds is None else "holding" if holds else "failing"
        out.append(
            {
                **{k: p[k] for k in ("id", "when", "claim", "text")},
                "fact": t["fact"] if t else None,
                "state": state,
            }
        )
    return out


def _decimal_year(d: date) -> float:
    start, end = date(d.year, 1, 1), date(d.year + 1, 1, 1)
    return round(d.year + (d - start).days / (end - start).days, 3)


def strip(block: dict[str, Any], today: date) -> dict[str, Any]:
    """The record of where the bottleneck has sat. Years and levels are this site's reading of dated events, each
    with its reason; a span still running ends at today, so no solid ink passes the now line."""
    st, now = block["strip"], _decimal_year(today)
    held = {p["row"] for p in block["predictions"] if p.get("row")}
    rows = [
        {
            "id": r["id"],
            "label": r["label"],
            "predicted": r["id"] in held,
            "spans": [
                {**sp, "to": min(sp["to"] or now, now), "running": sp["to"] is None} for sp in r["spans"]
            ],
        }
        for r in st["rows"]
    ]
    span = st["to"] - st["from"]

    def pct(year: float) -> float:
        return round(100 * (year - st["from"]) / span, 2)

    for r in rows:  # each span's place on its track, and the anchor of its row in the table
        for i, sp in enumerate(r["spans"]):
            sp.update(
                left=pct(sp["from"]),
                width=round(pct(sp["to"]) - pct(sp["from"]), 2),
                anchor=f"span-{r['id']}-{i}",
            )
    ticks = [
        {"x": pct(y), "label": str(y), "minor": i % 2 == 1}
        for i, y in enumerate(range(st["from"], st["to"] + 1, 2))
    ]
    return {"from": st["from"], "to": st["to"], "now": now, "now_x": pct(now), "ticks": ticks, "rows": rows}


def migration(s: Store, spec: dict[str, Any], today: date) -> dict[str, Any]:
    from . import migration_figures

    block = spec["migration"]
    card = scorecard(s, today)
    f = facts(s, block, today, computed={"scored": card["scored"]})
    preds = predictions(block, f)
    return {
        "as_of": min(
            max((x["as_of"] for x in f.values() if x and x["as_of"]), default=today.isoformat()),
            today.isoformat(),
        ),
        "facts": f,
        "scorecard": card,
        "strip": strip(block, today),
        "predictions": preds,
        "tally": {k: sum(1 for p in preds if p["state"] == k) for k in STATES},
        "sources": block["sources"],
        "figures": migration_figures.build(s, block, card, yaml.safe_load(TIGHTNESS.read_text()), today, f.get("lab_deals_4q")),
    }


def tightness_problems(s: Store, today: date) -> tuple[list[str], list[str]]:
    spec = yaml.safe_load(TIGHTNESS.read_text())
    errors, notes = [], []
    kinds = {k["id"] for k in spec["kinds"]}
    for inp in spec["inputs"]:
        where = f"tightness: {inp['id']}"
        if inp["kind"] not in kinds:
            errors.append(f"{where} has an unknown kind")
        if not inp.get("gauges") and len((inp.get("withheld") or {}).get("because", "")) < 40:
            errors.append(f"{where} has no gauges and no sentence saying why it is withheld")
        if any("metric" in g for g in inp.get("gauges") or []) and len(inp.get("ceiling_rationale", "")) < 40:
            errors.append(f"{where} scores without a ceiling rationale")
        for g in inp.get("gauges") or []:
            if not 0 < g["weight"] <= 1:
                errors.append(f"{where}.{g['id']} has a weight outside (0, 1]")
            if "unfed" in g:
                if len(g["unfed"].get("because", "")) < 40:
                    errors.append(f"{where}.{g['id']} is unfed without a sentence saying why")
                continue
            if not s.metric_spec(g["metric"]):
                errors.append(f"{where}.{g['id']} names unknown metric {g['metric']}")
            xs, ps = [k[0] for k in g["knots"]], [k[1] for k in g["knots"]]
            rising, falling = ps == sorted(ps), ps == sorted(ps, reverse=True)
            if (
                len(xs) < 3
                or xs != sorted(set(xs))
                or not (rising or falling)
                or not all(0 <= p <= 100 for p in ps)
            ):
                errors.append(f"{where}.{g['id']} has a malformed scale")
            if len(g.get("scale_rationale", "")) < 40:
                errors.append(f"{where}.{g['id']} has no scale rationale")
    if errors:
        return errors, []
    lost = []
    for i in scorecard(s, today)["inputs"]:
        fed = [g for g in i["gauges"] if g["unfed"] is None]
        if i["score"] is None and fed:
            why = [f"{g['id']} {g['unavailable']}" for g in fed if g["unavailable"]]
            lost.append(i["id"] + (f" ({', '.join(why)})" if why else ""))
        for g in fed if i["score"] is not None else []:
            if g["unavailable"] is None and g["age_days"] > 0.9 * g["max_age_days"]:
                last = today + timedelta(days=g["max_age_days"] - g["age_days"])
                notes.append(f"tightness: {i['id']}.{g['id']} passes its age limit after {last.isoformat()}")
    if (
        lost
    ):  # one line however many: after a publisher's quiet spell this would otherwise print nightly per input
        notes.append("tightness: inputs with a gauge and no score: " + "; ".join(lost))
    return [], notes


def record() -> list[dict[str, str]]:
    """The note's "**Title.** text" paragraphs, before its source list."""
    body = RECORD.read_text().split("## Sources")[0]
    return [{"title": m[1], "text": m[2].strip()} for m in re.finditer(r"^\*\*(.+?)\.\*\* (.+)$", body, re.M)]


def _x(v: float, lo: float, hi: float) -> float:
    return round(100 * (v - lo) / (hi - lo), 2)


def _held(s: Store, ind: Any, value: float, scored: bool) -> list[str]:
    """Why a number that falls inside a range is not scored there, by the evaluator's own checks in its own order:
    its interval spans two ranges, else it sits on a line; its best evidence is a company describing itself; it rests
    on one source that is not a primary one. A status a person wrote for another reason reads `reason`."""
    from .analysis.bands import _band, _on_edge
    from .cli import _single_non_primary  # the two-source rule lives with `evaluate`
    from .schema import Tier

    n, f, x = ind.normal_band, ind.fast_band, ind.falsifying_band
    lo, hi = s.band_interval(ind)
    why = []
    if lo is not None and hi is not None and _band(lo, n, f, x) != _band(hi, n, f, x):
        why.append("interval")
    elif _on_edge(value, n, f, x):
        why.append("edge")
    if s.band_input(ind)[3] == Tier.ACTOR_STATEMENT:
        why.append("tier")
    if _single_non_primary(s, ind):
        why.append("single")
    return why or ([] if scored else ["reason"])


def _readings(s: Store, spec: dict[str, Any]) -> dict[str, Any]:
    """The five slow variables against the rule that grades each. A ranged one is drawn to scale on its own axis from
    zero past the fast range's edge; its mark sits inside a range only when the status says that range, on the line
    when the evaluator reads it as on the edge, and outside with its reasons when it is held. A directed one draws
    the window its rule compares, with the dead band round the window's first reading."""
    from .analysis.bands import EDGE, _band, _on_edge
    from .analysis.direction import window

    zone_of = {"consistent_with_normal": "normal", "faster_than_normal": "fast", "emerging": "between"}
    ranged, directed = [], []
    for v in spec["slow_variables"]:
        ind = next(i for i in s.seed.indicators if i.id == v["id"])
        cur = s.current(ind.id)
        card = s._card(ind)
        row = {"id": ind.id, "label": v["label"], "status": cur.new_status if cur else None, "grade": card["grade"],
               "href": f"/indicators/{ind.id}"}  # fmt: skip
        if ind.direction_rule:
            pts = {p["as_of"]: p for p in s.headline(ind) if p["value"] is not None}
            win = window([(a, p["value"]) for a, p in pts.items()], ind.direction_rule)
            if len(win) < 2:
                continue
            (a0, v0), (a1, v1) = win[0], win[-1]
            band = ind.direction_rule.dead_band
            # a share is drawn on the whole of the thing it is a share of; anything else from zero to a little past
            lo, hi = min(0.0, v0 - band, v1), 1.0 if ind.unit == "share" else max(v0 + band, v1) * 1.15
            x0, x1 = _x(v0, lo, hi), _x(v1, lo, hi)
            directed.append(row | {
                "unit": ind.unit, "higher_is": ind.direction_rule.higher_is, "periods": ind.direction_rule.periods,
                "start": {"as_of": a0, "value": v0, "obs_ids": pts[a0]["obs_ids"], "x": _x(v0, lo, hi)},
                "end": {"as_of": a1, "value": v1, "obs_ids": pts[a1]["obs_ids"], "x": _x(v1, lo, hi)},
                "move": {"x": min(x0, x1), "w": round(abs(x1 - x0), 2)},
                "dead": {"x": _x(v0 - band, lo, hi), "w": round(_x(v0 + band, lo, hi) - _x(v0 - band, lo, hi), 2),
                         "band": band},
                # a mark that is not wholly a filed or surveyed count is hatched: a grade C reading, or a share whose
                # total includes an estimate (the seed's own sentence says which)
                "estimate": card["grade"] in ("C", "D") or "estimate" in v["sentence"],
            })  # fmt: skip
            continue
        n, f = ind.normal_band, ind.fast_band
        value, as_of, ids, _ = s.band_input(ind)
        if value is None or n is None or f is None or n.hi is None or f.lo is None or f.lo <= n.hi:
            raise ValueError(f"argument: {ind.id} has no reading or no normal range below a fast one to draw")
        lo, hi = min(0.0, value), max(value, f.lo) + (f.lo - n.hi)
        edges = [_x(n.hi, lo, hi), _x(f.lo, lo, hi)]
        falls = zone_of[_band(value, n, f, ind.falsifying_band).value]
        scored = zone_of.get(row["status"] or "") == falls and falls != "between"
        x, lane, held = _x(value, lo, hi), "inside" if scored else "between" if falls == "between" else "outside", []
        if _on_edge(value, n, f, ind.falsifying_band):
            near = [e for e, b in zip(edges, (n.hi, f.lo)) if abs(value - b) <= EDGE * abs(b)]
            x, lane = (near[0] if near else x), "line"
        if lane in ("outside", "line"):
            held = _held(s, ind, value, scored)
        ranged.append(row | {
            "unit": s.band_unit(ind), "value": value, "as_of": as_of.isoformat(), "obs_ids": ids, "x": x, "lane": lane,
            "falls": falls, "held": held,
            "zones": [{"key": "normal", "x": 0, "w": edges[0]},
                      {"key": "between", "x": edges[0], "w": round(edges[1] - edges[0], 2)},
                      {"key": "fast", "x": edges[1], "w": round(100 - edges[1], 2)}],
            # a rule's line, from the seed's published range: `at`, not `value`, since no observation stands behind it
            "edges": [{"x": edges[0], "at": n.hi}, {"x": edges[1], "at": f.lo}],
            "zero": _x(0.0, lo, hi),
        })  # fmt: skip
    return {"ranged": ranged, "directed": directed}


def figures(s: Store, spec: dict[str, Any], exits_: list[dict[str, Any]], phase_: dict[str, Any]) -> dict[str, Any]:
    """What the three figures on /argument draw (Part 45i), read off the seed, the essay's own headings, tonight's
    statuses and the thesis monitor's rows. Nothing here changes a status, a reading or a state."""
    from .store import DATA, read_jsonl

    readings = _readings(s, spec)
    status = {r["id"]: r["status"] for r in readings["ranged"] + readings["directed"]}
    labels = {v["id"]: v["label"] for v in spec["slow_variables"]}
    by = {e["monitor"]: e for e in exits_}
    heads = re.findall(r"^### (Folio [IVX]+ · (.+))\n\n## (.+)$", ESSAYS["full"].read_text(), re.M)
    claim = {folio: (label, text) for label, folio, text in heads}
    rows = [
        {
            "folio": m["folio"],
            "label": claim[m["folio"]][0],
            "claim": claim[m["folio"]][1],
            "watches": [{"id": i, "label": labels[i], "status": status.get(i)} for i in m.get("watches") or []],
            "phase": phase_["state"] if m.get("phase") else None,
            "exits": [{k: by[e][k] for k in ("monitor", "label", "state")} for e in m.get("exits") or []],
        }
        for m in spec["map"]
    ]
    thesis = {v["id"]: v for v in read_jsonl(DATA / "thesis.jsonl")}
    drawn = []
    for e, x in zip(spec["exits"], exits_):
        v = thesis.get(e["monitor"]) or {"conds": [], "counter": []}
        conds = [
            {**{k: c[k] for k in ("text", "detail", "holds", "obs_ids")}, "label": w["label"],
             "either": bool(w.get("either")), "counter": i >= len(v["conds"])}
            for i, (c, w) in enumerate(zip(v["conds"] + v["counter"], e["conditions"]))
        ]  # fmt: skip
        mine = [c for c in conds if not c["counter"]]
        drawn.append({"monitor": e["monitor"], "label": x["label"], "state": x["state"], "conds": conds,
                      "n": len(mine), "met": len([c for c in mine if c["holds"] is True])})  # fmt: skip
    counts = {"exits": len(drawn)} | {
        k: len([r for r in drawn if r["state"] == st_])
        for k, st_ in (("met", "supported"), ("unsupported", "unsupported"), ("contradicted", "contradicted"),
                       ("untestable", "untestable"))  # fmt: skip
    }
    return {"map": rows, "readings": readings, "exits": {"rows": drawn, "counts": counts}}


def build(s: Store, today: date | None = None) -> dict[str, Any]:
    spec = load()
    f = facts(s, spec)
    today = today or date.today()
    ph, ex = phase(s, spec), exits(spec)
    return {
        "figures": figures(s, spec, ex, ph),
        "migration": migration(s, spec, today),
        "as_of": max((x["as_of"] for x in f.values() if x), default=None),
        "essay": {k: p.read_text() for k, p in ESSAYS.items()},
        "facts": f,
        "slow_variables": spec["slow_variables"],
        "clocks": clocks(s, spec),
        "phase": ph,
        "exits": ex,
        "headlines": headlines(
            spec,
            {
                i.bucket_id
                for i in s.seed.indicators
                if i.published and i.bucket_id and (e := s.current(i.id)) and e.new_status == "faster_than_normal"
            },
        ),
        "sources": spec["sources"],
        "record": record(),
    }


def problems(s: Store) -> tuple[list[str], list[str]]:
    """Errors for anything that cannot resolve (CI catches them); attention for sentences the data stopped backing."""
    spec = load()
    errors: list[str] = []
    ids = {i.id for i in s.seed.indicators}
    published = {i.id for i in s.seed.indicators if i.published}
    for k, v in spec["facts"].items():
        if "indicator" in v and v["indicator"] not in ids or "metric" in v and not s.metric_spec(v["metric"]):
            errors.append(f"argument: fact {k} names an unknown indicator or metric")
        if bad := _bad_test(v.get("expect"), spec["facts"]):
            errors.append(f"argument: fact {k} {bad}")
    for x in spec["slow_variables"] + spec["clocks"]["links"]:
        if x["id"] not in published:
            errors.append(f"argument: {x['id']} is not a published indicator")
    for x in (spec.get("sources") or []) + ((spec.get("migration") or {}).get("sources") or []):
        if bad := unfetched(x):
            errors.append(f"argument: source {x['url']} {bad}")
    from .thesis import RULES

    monitors = {r.__name__ for r in RULES}
    for e in spec["exits"]:
        if e["monitor"] not in monitors or not e.get("label"):
            errors.append(f"argument: exit {e['monitor']} names an unknown monitor or has no label")
    slow, folios = {x["id"] for x in spec["slow_variables"]}, set(re.findall(r"· (.+)$", ESSAYS["full"].read_text(), re.M))
    for m in spec.get("map") or []:
        if m["folio"] not in folios or not set(m.get("watches") or []) <= slow:
            errors.append(f"argument: map row {m['folio']} names an unknown folio or slow variable")
        if not {e for e in m.get("exits") or []} <= {e["monitor"] for e in spec["exits"]}:
            errors.append(f"argument: map row {m['folio']} names an unknown exit")
    for page, h in spec["headlines"].items():
        if h["monitor"] not in monitors or "untestable" not in h["claims"]:
            errors.append(f"argument: {page} headline names an unknown monitor or has no untestable claim")
        buckets = {b.id for b in s.seed.buckets}
        for state, alts in (h.get("when_fast") or {}).items():
            if state not in h["claims"] or not set(alts) <= buckets:
                errors.append(f"argument: {page} headline's when_fast names an unknown state or bucket")
    block = spec["migration"]
    for k, v in block["facts"].items():
        if "indicator" in v and v["indicator"] not in ids or "metric" in v and not s.metric_spec(v["metric"]):
            errors.append(f"argument: migration fact {k} names an unknown indicator or metric")
        if not any(x in v for x in ("metric", "indicator", "series", "computed")):
            errors.append(
                f"argument: migration fact {k} names no metric, indicator, series or computed value"
            )
        if bad := _bad_test(v.get("expect"), block["facts"]):
            errors.append(f"argument: migration fact {k} {bad}")
        if v.get("expect") and "computed" not in v and "max_age_days" not in v:
            errors.append(f"argument: migration fact {k} has an expect and no max_age_days")
    tight = yaml.safe_load(TIGHTNESS.read_text())
    card_ids, words = {i["id"] for i in tight["inputs"]}, {w for _, w in tight["rules"]["words"]}
    rows = {r["id"] for r in block["strip"]["rows"]}
    for p in block["predictions"]:
        t = p.get("test")
        if t and t.get("fact") not in block["facts"] or not t and len(p.get("text", "")) < 40:
            errors.append(f"argument: prediction {p['id']} names an unknown fact, or has no test and no text")
        ops = {k: v for k, v in (t or {}).items() if k != "fact"}
        if t and (bad := _bad_test(ops, block["facts"]) if ops else "needs exactly one of gt, gte, lt, lte"):
            errors.append(f"argument: prediction {p['id']}'s test {bad}")
        if p.get("expect_state") not in STATES or p.get("when") not in ("now", "next", "watch"):
            errors.append(f"argument: prediction {p['id']} has an unknown expect_state or when")
        if p.get("row") and p["row"] not in rows:
            errors.append(f"argument: prediction {p['id']} names an unknown strip row")
    errors += [f"argument: says names unknown input {k}" for k in block["says"] if k not in card_ids]
    errors += [
        f"argument: says calls {k} an unknown word {w}"
        for k, ws in block["says"].items()
        for w in ws
        if w not in words
    ]
    if errors:
        return errors, []
    errors += [  # the strip plate prints a span's reason as plain text, so a token there would show as written
        f"argument: strip row {r['id']} has a token in a span's reason, which the plate cannot render"
        for r in block["strip"]["rows"]
        for sp in r["spans"]
        if TOKEN.search(sp["because"])
    ]
    seed_text = " ".join(p["claim"] + " " + p["text"] for p in block["predictions"])
    for name, path in ESSAYS.items():
        text = path.read_text() if path.exists() else ""
        if not text:
            errors.append(f"argument: {path} is missing")
        errors += [f"argument: {path} {b}" for b in essay_shape(text)] if text else []
        known = block["facts"] if name == "migration" else spec["facts"]
        for kind, key in TOKEN.findall(text + (seed_text if name == "migration" else "")):
            if kind == "fact" and key not in known or kind == "plate" and key not in PLATES[name]:
                errors.append(f"argument: {path} has an unknown [{kind}:{key}]")
    if errors:
        return errors, []
    notes: list[str] = []
    for k, f in facts(s, spec).items():
        if f is None:
            notes.append(f"argument: fact {k} has no reading; the essay shows a gap there")
        elif f["holds"] is False:
            notes.append(
                f"argument: fact {k} no longer meets {spec['facts'][k]['expect']}; rewrite the sentence that leans on it"
            )
    if clocks(s, spec)["holds"] is False:
        notes.append(
            "argument: the clocks plate's caption (capability outpacing the work) no longer holds; rewrite it"
        )
    # the essays also assert states in words ("installation", "contradicted"): re-test those too
    got = {e["monitor"]: e["state"] for e in exits(spec)}
    want = {e["monitor"]: e["expect"] for e in spec["exits"] if e.get("expect")}
    if spec["phase"].get("expect"):
        got["phase"], want["phase"] = phase(s, spec)["state"], spec["phase"]["expect"]
        if HALF.get(got["phase"]) == want["phase"]:  # the essays name the half; a finer phase inside it agrees
            got["phase"] = want["phase"]
    for k, w in want.items():
        if got.get(k) != w:
            notes.append(
                f"argument: the essays say {k} reads {w}, but it now reads {got.get(k)}; rewrite them"
            )
    today = date.today()
    t_errors, t_notes = tightness_problems(s, today)
    errors += t_errors
    notes += t_notes
    if t_errors:
        return errors, notes
    m = migration(s, spec, today)
    for k, f in m["facts"].items():
        if f is None:
            notes.append(f"argument: migration fact {k} has no reading; the essay shows a gap there")
        elif f.get("stale"):
            notes.append(
                f"argument: migration fact {k} is older than its limit; its sentence is no longer tested"
            )
        elif f["holds"] is False:
            notes.append(
                f"argument: migration fact {k} no longer meets {block['facts'][k]['expect']}; rewrite its sentence"
            )
    want_state = {p["id"]: p["expect_state"] for p in block["predictions"]}
    for p in m["predictions"]:
        if p["state"] != want_state[p["id"]]:
            notes.append(
                f"argument: prediction {p['id']} now reads {p['state']}, not {want_state[p['id']]}; the page says so, check the essay"
            )
    words = {i["id"]: i["word"] for i in m["scorecard"]["inputs"]}
    for k, allowed in block["says"].items():
        if words.get(k) not in allowed:
            notes.append(
                f"argument: the essay calls {k} {' or '.join(allowed)}, but it now reads {words.get(k)}"
            )
    sites = (m["facts"].get("dc_sites") or {}).get("value")
    if sites is not None and sites < 25:
        notes.append(
            f"argument: only {sites:.0f} data-centre sites compare; under twenty the gap has no reading"
        )
    return errors, notes
