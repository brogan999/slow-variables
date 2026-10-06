"""The bottleneck map (Part 11, section C; seed/map.yaml): the chain's inputs and the frictions outside it, laid
against the four stages of diffusion. Today's reading sits once per row: an input's tightness score from the
migration scorecard, or, for a friction, the statuses of the published indicators that read it. A cell carries
marks, never a colour: the row acts on that stage (with the reason), whether anything the site reads measures the
row, whether the stage is the site's placement or an author's, and which named writers expect the row to bind. The
site's own predictions and the outlook's claims are the writers.

`build` is pure: everything it reads is passed in, so it is tested without a Store. `from_store` gathers the inputs."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

SEED = Path(__file__).resolve().parents[2] / "seed" / "map.yaml"
STAGE_OF_BUCKET = {  # the stock each family is drawn at: Narayanan and Kapoor's upstream limits sit where AI is made
    "methods": "methods",
    "return_arrow": "methods",
    "products": "products",
    "early_adoption": "early_adoption",
    "adaptation": "adaptation",
}
FAST, NORMAL = {"faster_than_normal"}, {"consistent_with_normal", "slower_than_normal"}
SITE = "This site"
LEDGERS = ("ai_evaluation_market", "insurer_ai_exclusions", "agent_access_fences")  # what ledger_events_12m counts


def load() -> dict[str, Any]:
    return yaml.safe_load(SEED.read_text())


def _tally(statuses: list[str | None]) -> dict[str, int]:
    return {
        "instruments": len(statuses),
        "fast": sum(s in FAST for s in statuses),
        "normal": sum(s in NORMAL for s in statuses),
        "other": sum(s not in FAST | NORMAL for s in statuses),
    }


def build(
    spec: dict[str, Any],
    scorecard: dict[str, Any],
    predictions: list[dict[str, Any]],
    bottlenecks: dict[str, Any],
    cards: dict[str, dict[str, Any]],
    readings: dict[str, dict[str, Any]],
    names: dict[str, str],
    bets: list[dict[str, Any]],
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    stages = [s["id"] for s in spec["stages"]]
    inputs = {i["id"]: i for i in scorecard["inputs"]}
    said = {p["id"]: p for p in predictions}
    by_cell: dict[tuple[str, str], list[dict[str, Any]]] = {}
    by_row: dict[str, list[dict[str, Any]]] = {}
    for link in spec.get("predictions") or []:
        p = said.get(link["id"])
        if not p:
            continue
        claim = {
            "who": SITE,
            "text": p["claim"],
            "state": p["state"],
            "href": "/argument/migration#predictions",
        }
        for row, stage in (link.get("cells") or {}).items():
            by_cell.setdefault((row, stage), []).append(claim)
            by_row.setdefault(row, []).append(claim)
        for row in link.get("rows") or []:  # a prediction that the row does not bind: listed, never marked
            by_row.setdefault(row, []).append(claim)
    for c in claims or []:  # the outlook's claims: a row and a stage mark the cell; a row alone lists it
        claim = {k: c[k] for k in ("who", "text", "state", "href")}
        if c.get("stage"):
            by_cell.setdefault((c["row"], c["stage"]), []).append(claim)
        by_row.setdefault(c["row"], []).append(claim)

    def cells(row: str, bites: dict[str, str], measured: bool, site: set[str] | None = None) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for st in stages:
            writers = by_cell.get((row, st), [])
            if st not in bites and not writers:
                continue
            out[st] = {
                "bites": st in bites,
                "measured": measured and st in bites,
                "why": bites.get(st),
                "site": st in (site or set()),  # a stage this site chose, where a published writer gave none
                "writers": writers,
            }
        return out

    def extra(ids: list[str]) -> list[dict[str, Any]]:
        return [readings[i] for i in ids if i in readings]

    chain = []
    for r in spec["chain"]:
        i = inputs[r["input"]]
        scored = i["score"] is not None
        chain.append(
            {
                "id": r["input"],
                "name": i["name"],
                "what": i["what"],
                "note": r.get("note"),  # where two claims on this row read one tally differently
                "reads": i.get("reads"),
                "layer": {"id": r["layer"], "name": names[r["layer"]]},
                "sublayer": {"id": r["sublayer"], "name": names[r["sublayer"]]} if r.get("sublayer") else None,
                "reading": (
                    {
                        "kind": "scored",
                        "score": i["score"],
                        "word": i["word"],
                        "confidence": i["confidence"],
                        "hatched": i["hatched"],
                        "kind_of_tight": i["kind"],
                        "obs_ids": i["obs_ids"],
                    }
                    if scored
                    else {
                        "kind": "withheld",
                        "because": (i["withheld"] or {}).get("because"),
                        "tag": (i["withheld"] or {}).get("kind"),
                        "kind_of_tight": i["kind"],
                    }
                ),
                "cells": cells(r["input"], r["bites"], scored),
                "instruments": [
                    {"label": g["label"], "href": (g.get("reading") or {}).get("href")}
                    for g in i.get("gauges") or []
                    if g.get("reading")
                ],
                "claims": by_row.get(r["input"], []),
                "href": f"/argument/migration#input-{r['input']}",
            }
        )

    sections = {s["name"]: s for s in bottlenecks["sections"]}
    grid = {g["name"]: g["cells"] for g in bottlenecks["grid"]}
    outside = []
    for k, f in enumerate(spec["families"]):
        related = {r["id"]: r for b in bottlenecks["items"] if b["section"] == f["name"] for r in b["related"]}
        for i in f.get("indicators") or []:  # a gauge that reads the whole family, not one of its items
            if i in cards and i not in related:
                related[i] = {"id": i, "name": cards[i]["name"], "published": cards[i]["published"], "status": cards[i]["status"]}
        linked = sorted(related.values(), key=lambda r: (not r["published"], r["name"]))
        tally = _tally([r["status"] for r in linked if r["published"]])
        more = extra([_fact_key(x) for x in f.get("facts") or []])
        stage = STAGE_OF_BUCKET[sections[f["name"]]["bucket_id"]]
        bites = {stage: f["why"]} | {st: a["why"] for st, a in (f.get("also") or {}).items()}
        site = ({stage} if f["placed"] == "site" else set()) | {
            st for st, a in (f.get("also") or {}).items() if a["by"] == "site"
        }
        outside.append(
            {
                "id": f"family_{k}",
                "name": f["label"],
                "family": f["name"],
                "reading": {"kind": "tally", **tally, "readings": len(more)},
                "cells": cells(f"family_{k}", bites, tally["instruments"] > 0 or bool(more), site),
                "instruments": [
                    {
                        "label": r["name"],
                        "href": f"/indicators/{r['id']}" if r["published"] else f"/indicators#{r['id']}",
                        "status": r["status"] if r["published"] else None,
                        "unpublished": not r["published"],
                    }
                    for r in linked
                ],
                "readings": more,
                "domains": {d: ids for d, ids in grid[f["name"]].items() if ids},
                "claims": by_row.get(f"family_{k}", []),
                "href": f"#s-{list(sections).index(f['name'])}",
            }
        )
    for r in spec["nber"]:
        linked = [cards[i] | {"id": i} for i in r.get("indicators") or [] if i in cards]
        tally = _tally([c["status"] for c in linked if c["published"]])
        more = extra(
            [f"ledger:{t}:{s}" for t in r.get("ledgers") or [] for s in ("for", "against")]
            + [f"series:{x['key']}" for x in r.get("series") or []]
        )
        outside.append(
            {
                "id": r["id"],
                "name": r["label"],
                "what": r["what"],
                "reading": {"kind": "tally", **tally, "readings": len(more)},
                "cells": cells(r["id"], r["bites"], tally["instruments"] > 0 or bool(more)),
                "instruments": [
                    {
                        "label": c["name"],
                        "href": f"/indicators/{c['id']}" if c["published"] else f"/indicators#{c['id']}",
                        "status": c["status"] if c["published"] else None,
                        "unpublished": not c["published"],
                    }
                    for c in linked
                ],
                "readings": more,
                "claims": by_row.get(r["id"], []),
                "source": "The Economics of Transformative AI, a volume of the National Bureau of Economic Research (2026)",
                "href": None,
            }
        )
    for r in chain + outside:  # the filter "what binds now or is expected to": a word from the export, never the page's
        now = r["reading"].get("word") in ("tight", "severe")
        predicted = any(c["writers"] for c in r["cells"].values())
        r["focus"] = "both" if now and predicted else "now" if now else "predicted" if predicted else None
    return {
        "stages": [{**s, "n": k} for k, s in enumerate(spec["stages"], 1)],
        "groups": [
            {
                "id": "chain",
                "label": "Inside the chain",
                "sections": [  # by capture layer, in the order the layers first appear in the seed
                    {"id": lay, "name": names[lay], "rows": [r for r in chain if r["layer"]["id"] == lay]}
                    for lay in dict.fromkeys(r["layer"]["id"] for r in chain)
                ],
            },
            {
                "id": "outside",
                "label": "Outside the chain",
                "sections": [
                    {
                        "id": "families",
                        "name": "Narayanan and Kapoor's families",
                        "rows": [r for r in outside if r["id"].startswith("family_")],
                    },
                    {
                        "id": "nber",
                        "name": "Added by the NBER volume",
                        "rows": [r for r in outside if not r["id"].startswith("family_")],
                    },
                ],
            },
        ],
        "bets": bets,
    }


def _fact_key(x: dict[str, Any]) -> str:
    return f"fact:{x['metric']}:" + ",".join(f"{k}={v}" for k, v in sorted((x.get("dims") or {}).items()))


def problems(
    spec: dict[str, Any],
    inputs: set[str],
    families: set[str],
    indicators: set[str],
    names: set[str],
    predictions: set[str],
    buckets: set[str] | None = None,
    metrics: set[str] | None = None,
) -> list[str]:
    """Errors for a map seed that cannot resolve; CI catches them before the export trips on them."""
    stages = {s["id"] for s in spec["stages"]}
    errors = []
    seen = [r["input"] for r in spec["chain"]]
    errors += [f"map: no scorecard input {i}" for i in seen if i not in inputs]
    errors += [f"map: scorecard input {i} is not on the map" for i in sorted(inputs - set(seen))]
    for r in spec["chain"]:
        for n in (r["layer"], r.get("sublayer"), *(r.get("also_sublayers") or [])):
            if n and n not in names:
                errors.append(f"map: {r['input']} names no layer or sub-layer {n}")
        errors += [f"map: {r['input']} bites at an unknown stage {st}" for st in r["bites"] if st not in stages]
    for f in spec["families"]:
        for x in f.get("facts") or []:
            if metrics is not None and x.get("metric") not in metrics or not x.get("label"):
                errors.append(f"map: family {f['name']} reads an unknown metric or has no label: {x}")
    listed = {f["name"] for f in spec["families"]}
    errors += [f"map: no family {n}" for n in sorted(listed - families)]
    errors += [f"map: family {n} is not on the map" for n in sorted(families - listed)]
    for f in spec["families"]:
        if f.get("placed") not in ("author", "site") or len(f.get("why") or "") < 20:
            errors.append(f"map: family {f['name']} needs who placed it and why")
        for st, a in (f.get("also") or {}).items():
            if st not in stages or a.get("by") not in ("author", "site") or not a.get("why"):
                errors.append(f"map: family {f['name']} adds stage {st} without a known stage, a credit and a reason")
    for b in sorted((buckets or set()) - set(STAGE_OF_BUCKET)):
        errors.append(f"map: bucket {b} is drawn at no stage")
    rows = set(seen) | {f"family_{k}" for k in range(len(spec["families"]))} | {r["id"] for r in spec["nber"]}
    for r in spec["nber"]:
        errors += [f"map: {r['id']} names an unknown indicator {i}" for i in r.get("indicators") or [] if i not in indicators]
        errors += [f"map: {r['id']} names an unknown ledger {t}" for t in r.get("ledgers") or [] if t not in LEDGERS]
        errors += [f"map: {r['id']} bites at an unknown stage {st}" for st in r["bites"] if st not in stages]
    for p in spec.get("predictions") or []:
        if p["id"] not in predictions:
            errors.append(f"map: no prediction {p['id']}")
        for row, st in (p.get("cells") or {}).items():
            if row not in rows:
                errors.append(f"map: prediction {p['id']} marks an unknown row {row}")
            if st not in stages:
                errors.append(f"map: prediction {p['id']} marks an unknown stage {st}")
        errors += [f"map: prediction {p['id']} lists an unknown row {r}" for r in p.get("rows") or [] if r not in rows]
    return errors


def _plain(text: str, tests: dict[str, dict[str, Any]]) -> str:
    """A claim's sentence as plain text for the map: its threshold written in, its citation marks dropped."""
    from .format import fmt_line

    text = re.sub(r"\s*\[cite:[a-z0-9_]+\]", "", text)
    return re.sub(r"\[test:([a-z0-9_]+)\]", lambda m: fmt_line(tests[m[1]]["line"], tests[m[1]]["unit"]) if m[1] in tests else "", text)


def _byline(names: Any) -> str:
    s = "; ".join(dict.fromkeys(names))
    return s[:1].upper() + s[1:]


# The outlook's hand-kept ledgers, by what an event on each side of them is.
LEDGER_NAMES = {
    ("ai_evaluation_market", "for"): "Checking AI's work sold as its own category",
    ("insurer_ai_exclusions", "for"): "Insurers writing AI's mistakes out of standard policies",
    ("agent_access_fences", "for"): "Platforms fencing outside agents out",
    ("agent_access_fences", "against"): "Platforms letting outside agents in",
}


def _whose(c: dict[str, Any], pos: dict[str, Any], who: dict[str, str]) -> str:
    """Who a claim is credited to: this site, this site carrying an author further, or the author; a claim that
    names its own makers (a bet's parties, one author of a pair) is theirs outright."""
    if c["attribution"] == "site":
        return SITE
    names = _byline(who[h] for h in c["holders"])
    own = c["holders"] != pos.get(c.get("position"), {}).get("holders")
    return f"This site, extending {names}" if c["attribution"] == "extension" and not own else names


def outlook_claims(outlook: dict[str, Any]) -> list[dict[str, Any]]:
    """The outlook's claims that name a map row, with who makes each and a link to it."""
    who = {x["id"]: x.get("short") or x["who"] for x in outlook.get("sources") or []}  # a long author list, shortened
    pos = {p["id"]: p for p in outlook.get("positions") or []}
    return [
        {
            "row": c["row"],
            "stage": c.get("stage"),
            "who": _whose(c, pos, who),
            "text": _plain(c["text"], outlook.get("tests") or {}),
            "state": c["state"],
            "href": f"/outlook#claim-{c['id']}",
        }
        for c in outlook.get("claims") or []
        if c.get("row")
    ]


def from_store(
    s: Any,
    cards: dict[str, dict[str, Any]],
    bottlenecks: dict[str, Any],
    argument: dict[str, Any],
    outlook: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Gather the map's inputs from the store: the scorecard and predictions already built for argument.json, the
    ledgers' latest counts and the series the NBER rows name, layer names, and the startup money under each
    sub-layer the chain rows sit in, read at the latest quarter end on or before today, never a sub-layer's last
    non-empty figure (compute is paid for with capital spending and debt, which startup rounds miss)."""
    from .argument import fact

    spec = load()
    today = date.today()
    names = {x.id: x.name for x in [*s.seed.layers, *s.seed.sublayers]}
    readings: dict[str, dict[str, Any]] = {}
    for d in s.derived_for("ledger_events_12m"):
        if d.as_of_date <= today:  # rows arrive in date order, so the last kept is the latest
            key = f"ledger:{d.dims['target']}:{d.dims['stance']}"
            readings[key] = {
                "label": f"{LEDGER_NAMES.get((d.dims['target'], d.dims['stance']), d.dims['target'].replace('_', ' '))}, events in the latest twelve months:",
                "value": d.value,
                "unit": "count",
                "as_of": d.as_of_date.isoformat(),
                "obs_ids": d.input_observation_ids,
                "href": s._derived_href(d),
            }
    for r in spec["nber"]:
        for x in r.get("series") or []:
            if f := fact(s, {"series": x["key"]}, today):
                readings[f"series:{x['key']}"] = {**f, "label": x["label"]}
    for fam in spec["families"]:
        for x in fam.get("facts") or []:
            if f := fact(s, {"metric": x["metric"], "dims": x.get("dims")}, today):
                readings[_fact_key(x)] = {**f, "label": x["label"]}
    firms = dict(
        s.con.execute(
            "SELECT sublayer_id, count(DISTINCT entity_id) FROM entity_membership WHERE to_date IS NULL AND is_primary GROUP BY 1"
        ).fetchall()
    )
    subs: dict[str, list[str]] = {}
    for r in spec["chain"]:
        for sub in [r.get("sublayer"), *(r.get("also_sublayers") or [])]:
            if sub:
                subs.setdefault(sub, []).append(r["input"])
    rows = [d for d in s.derived_for("venture_dollars_4q") if d.as_of_date <= today]
    latest = max((d.as_of_date for d in rows), default=None)
    bets = []
    for sub, held in subs.items():
        v = next((d for d in rows if d.as_of_date == latest and d.dims.get("sublayer_id") == sub), None)
        bets.append(
            {
                "sublayer": {"id": sub, "name": names[sub]},
                "rows": held,
                "firms": firms.get(sub, 0),
                "as_of": latest.isoformat() if latest else None,
                "venture": {
                    "value": v.value,
                    "unit": "USD",
                    "as_of": v.as_of_date.isoformat(),
                    "obs_ids": v.input_observation_ids,
                    "href": s._derived_href(v),
                }
                if v
                else None,
            }
        )
    m = argument["migration"]
    return build(spec, m["scorecard"], m["predictions"], bottlenecks, cards, readings, names, bets, outlook_claims(outlook or {}))


# How a row is drawn when the map is counted (Part 45h). Inside the chain a scored row keeps its tightness word, cut
# where the map's own filter cuts it; a friction outside the chain is read on another scale and never joins that one.
ROW_CLASSES = ("tight", "moderate", "easing", "unscored", "friction", "friction_unread")
CLAIM_STATES = ("holding", "failing", "both", "untestable")
BARRIER_ORDER = ("read", "still_binds", "easing", "largely_lifted", "blank")  # like squares sit together in a family's row


def _row_class(r: dict[str, Any]) -> str:
    reading = r["reading"]
    if reading["kind"] == "tally":
        return "friction" if reading["instruments"] or reading["readings"] else "friction_unread"
    if reading["kind"] == "withheld":
        return "unscored"
    return "tight" if reading["word"] in ("tight", "severe") else "moderate" if reading["word"] == "moderate" else "easing"


def _bar(parts: list[tuple[str, int]]) -> list[dict[str, Any]]:
    """Segments of one whole bar, in percent from its left edge."""
    total, x, out = sum(n for _, n in parts), 0.0, []
    for key, n in parts:
        w = 100 * n / total if total else 0.0
        out.append({"key": key, "n": n, "x": x, "w": w})
        x += w
    return out


def _counts(us: list[dict[str, Any]]) -> dict[str, int]:
    return {c: sum(u["cls"] == c for u in us) for c in dict.fromkeys(u["cls"] for u in us)}


def figures(doc: dict[str, Any], bottlenecks: dict[str, Any], judged: dict[str, Any]) -> dict[str, Any]:
    """Everything the figures on /bottlenecks draw, counted and placed here from the map, the barriers list and the
    model's judgements, none of which it changes. Pure, so the file on disk can be rebuilt and compared."""
    from . import chart

    rows = [r for g in doc["groups"] for s in g["sections"] for r in s["rows"]]

    def units(rs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # low: a score the scorecard itself marks as low in confidence, hatched wherever it is drawn
        us = [{"id": r["id"], "name": r["name"], "cls": _row_class(r), "low": bool(r["reading"].get("hatched")), "href": f"#why-{r['id']}"} for r in rs]
        return sorted(us, key=lambda u: ROW_CLASSES.index(u["cls"]))

    stages = []
    for st in doc["stages"]:
        us = units([r for r in rows if r["cells"].get(st["id"], {}).get("bites")])
        stages.append(
            {
                **st,
                "units": us,
                "total": len(us),
                "counts": _counts(us),
                # rows on the tightness scale at all: a stage with none is unmeasured on it, which is not free
                "scored": sum(u["cls"] in ("tight", "moderate", "easing") for u in us),
                "now": [{"id": u["id"], "name": u["name"], "href": u["href"], "low": u["low"]} for u in us if u["cls"] == "tight"],
                "expected": [
                    {
                        "id": r["id"],
                        "name": r["name"],
                        "href": f"#why-{r['id']}",
                        "acts": bool(c.get("bites")),  # false: a writer places the row here and the map does not
                        "writers": [{"who": who, "state": state} for who, state in dict.fromkeys((w["who"], w["state"]) for w in c["writers"])],
                    }
                    for r in rows
                    if (c := r["cells"].get(st["id"], {})).get("writers")
                ],
            }
        )
    sections = [
        {"id": f"{g['id']}-{s['id']}", "group": g["label"], "name": s["name"], "units": (us := units(s["rows"])), "total": len(us), "counts": _counts(us)}
        for g in doc["groups"]
        for s in g["sections"]
        if s["rows"]
    ]
    chain = [r for r in rows if r["reading"]["kind"] != "tally"]
    kinds = [
        {"id": k, "units": (us := units([r for r in chain if r["reading"]["kind_of_tight"] == k])), "total": len(us), "counts": _counts(us)}
        for k in dict.fromkeys(r["reading"]["kind_of_tight"] for r in chain)
    ]

    tight = (judged.get("surfaces") or {}).get("tightness") or {}
    words = (judged.get("surfaces") or {}).get("barriers") or {}
    scored = [r for r in chain if r["reading"]["kind"] == "scored"]
    withheld = [r for r in chain if r["reading"]["kind"] == "withheld"]
    stood_in = sum(r["id"] in tight for r in withheld)
    outside = [r for r in rows if r["reading"]["kind"] == "tally"]
    low = sum(bool(r["reading"].get("hatched")) for r in scored)
    status = sum(r["reading"]["instruments"] > 0 for r in outside)  # an indicator with a status stands behind the row
    plain = sum(not r["reading"]["instruments"] and r["reading"]["readings"] > 0 for r in outside)  # figures only

    def barrier(b: dict[str, Any]) -> dict[str, Any]:
        j = None if b["related"] else words.get(str(b["id"]))
        cls = "read" if b["related"] else j["word"] if j else "blank"
        return {"id": b["id"], "title": b["title"], "cls": cls, "label": j["label"] if j else None, "href": f"#b{b['id']}"}

    families = []
    for r in rows:
        if r.get("family"):
            us = [barrier(b) for b in bottlenecks["items"] if b["section"] == r["family"]]
            us.sort(key=lambda u: BARRIER_ORDER.index(u["cls"]) if u["cls"] in BARRIER_ORDER else len(BARRIER_ORDER))
            families.append({"id": r["id"], "name": r["name"], "href": f"#why-{r['id']}", "units": us, "total": len(us), "counts": _counts(us)})
    drawn = [u for f in families for u in f["units"]]
    judged_words: dict[str, dict[str, Any]] = {}
    for u in drawn:
        if u["label"]:
            judged_words.setdefault(u["cls"], {"id": u["cls"], "label": u["label"], "n": 0})["n"] += 1
    n_read, n_judged = sum(u["cls"] == "read" for u in drawn), sum(bool(u["label"]) for u in drawn)
    def bar(reading: int, low: int, plain: int, judged_n: int, total: int) -> list[dict[str, Any]]:
        return _bar([("reading", reading), ("low", low), ("plain", plain), ("judged", judged_n), ("blank", total - reading - low - plain - judged_n)])

    firm = [
        {"id": "chain", "total": len(chain), "segs": bar(len(scored) - low, low, 0, stood_in, len(chain))},
        {"id": "outside", "total": len(outside), "segs": bar(status, 0, plain, 0, len(outside))},
        {"id": "barriers", "total": len(drawn), "segs": bar(n_read, 0, 0, n_judged, len(drawn))},
    ]

    claimed = [r for r in rows if r["claims"]]
    distinct = {(w["who"], w["text"], w["href"]): w for r in claimed for w in r["claims"]}  # a claim under two rows is one claim
    claims = {
        "states": list(CLAIM_STATES),
        "rows": [
            {
                "id": r["id"],
                "name": r["name"],
                "href": f"#why-{r['id']}",
                "cells": {
                    s: [{"who": w["who"], "text": w["text"], "href": w["href"], "site": w["who"].startswith(SITE)} for w in r["claims"] if w["state"] == s]
                    for s in CLAIM_STATES
                },
            }
            for r in claimed
        ],
        "tally": {s: sum(w["state"] == s for w in distinct.values()) for s in CLAIM_STATES},
        "total": len(distinct),
        "marks": sum(len(r["claims"]) for r in claimed),
        "site": sum(w["who"].startswith(SITE) for w in distinct.values()),
    }

    names = {r["id"]: r["name"] for r in rows}
    paid = [b["venture"]["value"] for b in doc["bets"] if b["venture"]]
    ax = chart.axis(paid, "USD", log=True) if paid else None  # a dot on a ratio scale: the amounts differ a thousandfold
    gaps = [b["y"] - a["y"] for a, b in zip(ax["ticks"], ax["ticks"][1:], strict=False)] if ax else []
    even = lambda g: all(abs(x - g[0]) < 0.05 for x in g)  # noqa: E731
    money = {
        # what the page may say of the labelled lines: each the same multiple of the last, all but the closing one, or not
        "steps": "even" if even(gaps) else "even_but_last" if len(gaps) > 2 and even(gaps[:-1]) else "uneven",
        "as_of": next((b["as_of"] for b in doc["bets"] if b["as_of"]), None),
        "ticks": [{"x": 100 - t["y"], "label": t["label"]} for t in ax["ticks"]] if ax else [],
        "rows": [
            {
                "id": b["sublayer"]["id"],
                "name": b["sublayer"]["name"],
                "inputs": [names.get(i, i) for i in b["rows"]],
                "firms": b["firms"],
                "venture": b["venture"],
                "x": 100 - chart.y(b["venture"]["value"], ax) if b["venture"] and ax else None,
            }
            for b in doc["bets"]
        ],
    }
    for r in money["rows"]:  # a dot near the right edge carries its label on its left, so the label stays in the plot
        r["flip"] = r["x"] is not None and r["x"] > 60
    tally = {c: sum(_row_class(r) == c for r in rows) for c in ROW_CLASSES}
    return {
        "rows": len(rows),
        "tally": tally,
        "stages": stages,
        "sections": sections,
        "kinds": kinds,
        "firm": firm,
        "families": families,
        "judged_words": (top := sorted(judged_words.values(), key=lambda w: -w["n"])),
        "judged_mostly": 2 * n_judged > len(drawn),  # the foot says "most" only while these hold
        "judged_top_mostly": bool(top) and 2 * top[0]["n"] > n_judged,
        "made_by": judged.get("made_by"),
        "claims": claims,
        "money": money,
    }
