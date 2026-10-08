"""The value-chain atlas (plan Part 48): a call on each business that could be built, and what each future does to it.

seed/chain_atlas.yaml holds a model's judgements in words, made the way seed/judgements.yaml is (Part 39): a call, a
take and the one thing that would undo each business, and an effect with a reason for each future on the outlook's grid
that changes it. Nothing here is a reading or a status, and no evaluator, metric, tally or query tool reads it. The
export lays out every business in every future, so the page switches between states and computes nothing.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .board import FIGURE, YEAR

SPEC = Path(__file__).resolve().parents[2] / "seed" / "chain_atlas.yaml"
MOVES = ("stronger", "weaker", "breaks")
ORDER = ("slack", "easing", "moderate", "tight", "severe")  # the tightness scorecard's words, loosest first
STEP = {"tightens": 1, "eases": -1}
WHEN = ("now", "transition", "mature")
TIGHTNESS = Path(__file__).resolve().parents[2] / "seed" / "tightness.yaml"
ARGUMENT = Path(__file__).resolve().parents[2] / "seed" / "argument.yaml"


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def _cells(outlook: dict[str, Any]) -> list[dict[str, Any]]:
    return (outlook.get("scenarios") or {}).get("cells") or []


def _future_ids(spec: dict[str, Any], outlook: dict[str, Any]) -> set[str]:
    """Every future a judgement may name: the grid's filled cells and the ownership futures the file defines."""
    return {f"{c['progress']}/{c['rules']}" for c in _cells(outlook)} | {f"owners/{o.get('id')}" for o in spec.get("ownership") or []}


def _futures(spec: dict[str, Any], outlook: dict[str, Any], texts: dict[str, str]) -> list[dict[str, Any]]:
    """The dial, in order: the grid's cells a writer argues, then the ownership futures, each with who argues it and
    the outlook's claims that bear on it."""
    sc = outlook.get("scenarios") or {}
    label = {a["id"]: a["label"] for k in ("progress", "rules") for a in sc.get(k) or []}
    sources = {x["id"]: x for x in outlook.get("sources") or []}
    claims = {c["id"] for c in outlook.get("claims") or []}

    def who(ids: list[str]) -> list[dict[str, str]]:
        """Each writer by name and by what they study, as the outlook's own source record has them."""
        return [{"who": sources[i]["who"], "field": sources[i].get("field") or "", "href": f"/outlook#source-{i}"} for i in ids if i in sources]

    def bears(ids: list[str]) -> list[dict[str, str]]:
        """A claim the outlook tests, in the outlook's own resolved words (`texts`), never a title of ours."""
        return [{"text": texts[i], "href": f"/outlook#claim-{i}"} for i in dict.fromkeys(ids) if i in claims and i in texts]

    grid = [
        {
            "id": f"{c['progress']}/{c['rules']}",
            "key": f"{c['progress']}-{c['rules']}",
            "group": "grid",
            "name": f"{label[c['progress']]}, {label[c['rules']][:1].lower()}{label[c['rules']][1:]}",
            "says": c.get("says") or "",
            "argued_by": who(c.get("argued_by") or []),
            "bears_for": bears(c.get("signposts") or []),
            "bears_against": [],
        }
        for c in _cells(outlook)
    ]
    owners = [
        {
            "id": f"owners/{o['id']}",
            "key": f"owners-{o['id']}",
            "group": "owners",
            "name": o["name"],
            "says": o["says"],
            "argued_by": who(o.get("argued_by") or []),
            "bears_for": bears(o.get("bears_for") or []),
            "bears_against": bears(o.get("bears_against") or []),
        }
        for o in spec.get("ownership") or []
    ]
    return [*grid, *owners]


def _in_scope(map_doc: dict[str, Any]) -> list[dict[str, Any]]:
    """The map's categories a path is owed for, from the seed or from the export: numbered, in scope, not the outcomes row."""
    cats = map_doc.get("categories") or [c for layer in map_doc.get("layers") or [] for c in layer.get("categories") or []]
    return [c for c in cats if not c.get("out_of_scope") and "." in str(c.get("number") or "")]


def _figure(text: str) -> bool:
    return bool(FIGURE.search(YEAR.sub("", text)))


def _extra_problems(spec: dict[str, Any], published: set[str]) -> list[str]:
    """Chains, builds and the planning assumptions (Part 48d)."""
    out: list[str] = []
    predictions = [p["id"] for p in (yaml.safe_load(ARGUMENT.read_text()).get("migration") or {}).get("predictions") or []]
    cats = set(spec.get("categories") or {})
    chains = spec.get("chains") or []
    for missing in [p for p in predictions if p not in [c.get("id") for c in chains]]:
        out.append(f"chain atlas: migration prediction {missing} has no chain")
    ids = [c.get("id") for c in chains]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"chain atlas: chain {dup} is given twice")
    for c in chains:
        w = f"chain atlas: chain {c.get('id')}"
        if c.get("id") not in predictions:
            out.append(f"{w} is not a migration prediction on the site")
        for part in c.get("parts") or []:
            if part not in cats:
                out.append(f"{w} names {part}, which is not a part with a path")
        for b in c.get("businesses") or []:
            if b not in published:
                out.append(f"{w} names {b}, which is not a published business")
        says = str(c.get("says") or "").strip()
        if not says:
            out.append(f"{w} says nothing")
        elif _figure(says):
            out.append(f"{w} types a figure, a size word or an address")
    listed = [p.get("id") for p in spec.get("primitives") or []]
    for dup in sorted({i for i in listed if listed.count(i) > 1}):
        out.append(f"chain atlas: lasting thing {dup} is given twice")
    for p in spec.get("primitives") or []:
        for k in ("name", "what", "why"):
            if not str(p.get(k) or "").strip():
                out.append(f"chain atlas: lasting thing {p.get('id')} has no {k}")
            elif _figure(str(p[k])):
                out.append(f"chain atlas: lasting thing {p.get('id')} types a figure, a size word or an address")
    pages = Path(__file__).resolve().parents[2] / "web" / "src" / "app"
    for g in spec.get("priors") or []:
        for a in g.get("assumptions") or []:
            after = a.get("after")
            if after and (not after.get("who") or not (pages / str(after.get("href") or "").split("#")[0].strip("/")).is_dir()):
                out.append(f"chain atlas: an assumption follows {after.get('who')} at {after.get('href')}, which is not a page that introduces them")
    prims = set(listed)
    for bid, built in (spec.get("builds") or {}).items():
        if bid not in published:
            out.append(f"chain atlas: builds names {bid}, which is not a published business")
        if not built:
            out.append(f"chain atlas: {bid} is listed as building nothing; leave it out")
        for i in built or []:
            if i not in prims:
                out.append(f"chain atlas: {bid} builds {i}, which is not one of the durable things the file defines")
    if spec.get("priors") and not str(spec.get("priors_by") or "").strip():
        out.append("chain atlas: the planning assumptions do not say whose they are")
    for g in spec.get("priors") or []:
        for a in g.get("assumptions") or []:
            if not str(a.get("text") or "").strip() or not str(a.get("weakened_by") or "").strip():
                out.append(f"chain atlas: an assumption {g.get('id')} holds has a text and says what would weaken it")
            if _figure(" ".join(str(a.get(k) or "") for k in ("text", "exception", "weakened_by"))):
                out.append(f"chain atlas: an assumption in {g.get('id')} types a figure, a size word or an address")
    return out


def problems(spec: dict[str, Any], opps: dict[str, Any], outlook: dict[str, Any], map_doc: dict[str, Any]) -> list[str]:
    out: list[str] = _map_problems(spec, outlook, map_doc)
    out += _extra_problems(spec, {o["id"] for o in opps.get("opportunities") or [] if o.get("published")})
    made = spec.get("made_by") or {}
    for k in ("model", "date", "method", "reviewed_by"):
        if not made.get(k):
            out.append(f"chain atlas: made_by has no {k}")
    calls = {c["id"] for c in spec.get("calls") or []}
    published = {o["id"] for o in opps.get("opportunities") or [] if o.get("published")}
    futures = _future_ids(spec, outlook)
    skipped = spec.get("not_judged") or {}
    for fid in sorted(futures):
        if not re.fullmatch(r"[a-z0-9_]+/[a-z0-9_]+", fid):
            out.append(f"chain atlas: future {fid} cannot name a mark on the page: lower-case letters, digits and underscores only")
    sources = {x["id"] for x in outlook.get("sources") or []}
    claims = {c["id"] for c in outlook.get("claims") or []}
    owned = [o.get("id") for o in spec.get("ownership") or []]
    for dup in sorted({i for i in owned if owned.count(i) > 1}):
        out.append(f"chain atlas: ownership future {dup} is defined twice")
    if owned and [g.get("id") for g in spec.get("future_groups") or []] != ["grid", "owners"]:
        out.append("chain atlas: future_groups must be grid, owners, in that order")
    for o in spec.get("ownership") or []:
        w = f"chain atlas: ownership future {o.get('id')}"
        if not o.get("argued_by"):
            out.append(f"{w}: no named writer argues it, so it cannot be on the dial")
        for i in o.get("argued_by") or []:
            if i not in sources:
                out.append(f"{w} is argued by {i}, which is not a source on the outlook")
        for i in [*(o.get("bears_for") or []), *(o.get("bears_against") or [])]:
            if i not in claims:
                out.append(f"{w} names {i}, which is not a claim on the outlook")
        for k in ("name", "says"):
            if not str(o.get(k) or "").strip():
                out.append(f"{w} has no {k}")
            elif _figure(str(o[k])):
                out.append(f"{w}: its {k} types a figure, a size word or an address")
    for row in spec.get("waiting") or []:
        if not str(row.get("name") or "").strip() or not str(row.get("why") or "").strip():
            out.append("chain atlas: a future that waits has a name and says why")
    for fid, why in skipped.items():
        if fid not in futures:
            out.append(f"chain atlas: not_judged names {fid}, which is not a future on the dial")
        if not str(why or "").strip():
            out.append(f"chain atlas: {fid} is not judged and nothing says why not")
    for c in spec.get("calls") or []:
        if _figure(str(c.get("says") or "")):
            out.append(f"chain atlas: call {c.get('id')} types a figure, a size word or an address")
    businesses = spec.get("businesses") or {}
    for missing in sorted(published - set(businesses)):
        out.append(f"chain atlas: {missing} is published and has no call")
    for bid, b in businesses.items():
        w = f"chain atlas: {bid}"
        if bid not in published:
            out.append(f"{w} is not a published business")
        if b.get("call") not in calls:
            out.append(f"{w} has call {b.get('call')}, outside the calls the file defines")
        for k in ("take", "kills"):
            text = str(b.get(k) or "").strip()
            if not text:
                out.append(f"{w} has no {k}")
            elif _figure(text):
                out.append(f"{w}: its {k} types a figure, a size word or an address")
        for fid, f in (b.get("futures") or {}).items():
            if fid not in futures:
                out.append(f"{w} names {fid}, which is not a future the outlook's grid fills")
            if fid in skipped:
                out.append(f"{w} names {fid}, which the file says is not judged, yet judges it")
            if f.get("effect") not in MOVES:
                out.append(f"{w} in {fid} has effect {f.get('effect')}; leave a future out when it changes nothing")
            reason = str(f.get("reason") or "").strip()
            if not reason:
                out.append(f"{w} in {fid} gives no reason")
            elif _figure(reason):
                out.append(f"{w} in {fid}: its reason types a figure, a size word or an address")
    return out


def _map_problems(spec: dict[str, Any], outlook: dict[str, Any], map_doc: dict[str, Any]) -> list[str]:
    out: list[str] = []
    gauges = {i["id"] for i in yaml.safe_load(TIGHTNESS.read_text())["inputs"]}
    owed = {c["id"] for c in _in_scope(map_doc)}
    cats = spec.get("categories") or {}
    futures = _future_ids(spec, outlook)
    probably = spec.get("scarcity") or {}
    if set(probably) != set(ORDER):
        out.append(f"chain atlas: scarcity must give a judged word for each of {', '.join(ORDER)}")
    for word, shown in probably.items():
        if shown == word:
            out.append(f"chain atlas: scarcity shows the scorecard's own word for a judged {word}")
    if [t.get("id") for t in spec.get("times") or []] != list(WHEN):
        out.append("chain atlas: times must be now, transition, mature, in that order")
    if set(spec.get("moves") or {}) != set(STEP):
        out.append("chain atlas: moves must name tightens and eases")
    if [g.get("id") for g in spec.get("ground") or []] != ["scarcer", "holds", "eases"]:
        out.append("chain atlas: ground must be scarcer, holds, eases, in that order")
    for kind in ("times", "ground"):
        for row in spec.get(kind) or []:
            if _figure(str(row.get("says") or "")):
                out.append(f"chain atlas: {kind} {row.get('id')} types a figure, a size word or an address")
    for missing in sorted(owed - set(cats)):
        out.append(f"chain atlas: {missing} has no path")
    for cid, c in cats.items():
        w = f"chain atlas: {cid}"
        if cid not in owed:
            out.append(f"{w} is not a part of the map in scope")
        for when in WHEN:
            if c.get(when) not in ORDER:
                out.append(f"{w} has word {c.get(when)} for {when}, outside the scorecard's words")
        if c.get("reading") and c["reading"] not in gauges:
            out.append(f"{w} reads {c['reading']}, which is not a tightness gauge")
        for k in ("scarce", "reason"):
            text = str(c.get(k) or "").strip()
            if not text:
                out.append(f"{w} has no {k}")
            elif _figure(text):
                out.append(f"{w}: its {k} types a figure, a size word or an address")
    for fid, moved in (spec.get("shifts") or {}).items():
        if fid not in futures or fid in (spec.get("not_judged") or {}):
            out.append(f"chain atlas: shifts name {fid}, which is not a judged future on the outlook's grid")
        for cid, m in (moved or {}).items():
            w = f"chain atlas: {cid} in {fid}"
            if cid not in cats:
                out.append(f"{w} is not a part with a path")
            if m.get("move") not in STEP:
                out.append(f"{w} has move {m.get('move')}; leave a part out when the future does not move it")
            reason = str(m.get("reason") or "").strip()
            if not reason:
                out.append(f"{w} gives no reason")
            elif _figure(reason):
                out.append(f"{w}: its reason types a figure, a size word or an address")
    return out


def _map(spec: dict[str, Any], futures: list[dict[str, Any]], map_doc: dict[str, Any], scored: dict[str, dict[str, Any]], on: dict[str, list[int]]) -> dict[str, Any]:
    """Every part of the map in every future at every time. Now is tonight's scored word where the part's gauge has one,
    else the judged word; a future never moves it. Later, a future moves a part one step along the scale, and no further
    than its ends."""
    cats, shifts, probably = spec.get("categories") or {}, spec.get("shifts") or {}, spec.get("scarcity") or {}
    moves = spec.get("moves") or {}

    def state(c: dict[str, Any], when: str, step: int) -> dict[str, Any]:
        read = (scored.get(c.get("reading") or "") or {}) if when == "now" else {}
        measured = read.get("word") in ORDER
        word = read["word"] if measured else ORDER[min(max(ORDER.index(c[when]) + (step if when != "now" else 0), 0), len(ORDER) - 1)]
        return {
            "word": word if measured else probably.get(word, word),
            "level": ORDER.index(word) + 1,
            "measured": measured,
            "hatched": bool(measured and read.get("hatched")),  # a low-confidence score is hatched wherever it is drawn
            "gauge": read.get("name") if measured else None,
        }

    def tile(m: dict[str, Any]) -> dict[str, Any]:
        c = cats[m["id"]]
        moved = [
            {"key": f["key"], "name": f["name"], "move": j["move"], "word": moves.get(j["move"], j["move"]), "reason": j["reason"]}
            for f in futures
            if (j := (shifts.get(f["id"]) or {}).get(m["id"]))
        ]
        step = {x["key"]: STEP[x["move"]] for x in moved}
        return {
            "id": m["id"],
            "number": m["number"],
            "name": m["name"],
            "scarce": c["scarce"],
            "reason": c["reason"],
            "n_entities": m.get("n_entities", 0),
            "href": f"/value-chain#mm-{m['id']}",
            "businesses": on.get(m["id"], []),
            "states": {k: {when: state(c, when, step.get(k, 0)) for when in WHEN} for k in ("none", *(f["key"] for f in futures))},
            "moved": moved,
        }

    layers = [
        {"number": layer.get("number"), "name": layer.get("name"), "categories": [tile(m) for m in _in_scope(layer) if m["id"] in cats]}
        for layer in map_doc.get("layers") or []
    ]
    layers = [layer for layer in layers if layer["categories"]]
    every = [c for layer in layers for c in layer["categories"]]

    def heading(c: dict[str, Any]) -> str:
        diff = c["states"]["none"]["mature"]["level"] - c["states"]["none"]["now"]["level"]
        return "scarcer" if diff > 0 else "eases" if diff < 0 else "holds"

    return {
        "times": spec.get("times") or [],
        "map": {"layers": layers},
        "ground": [{**g, "categories": [c["id"] for c in every if heading(c) == g["id"]]} for g in spec.get("ground") or []],
    }


def build(spec: dict[str, Any], opps_doc: dict[str, Any], outlook: dict[str, Any], map_doc: dict[str, Any], scored: dict[str, dict[str, Any]], texts: dict[str, str], predictions: list[dict[str, Any]]) -> dict[str, Any]:
    """web/data/chain_atlas.json. `texts` is the outlook export's resolved wording of each claim and `predictions` the migration predictions as the argument export has them tonight. `opps_doc` is the opportunities export (the records, their numbers and the sequence),
    `map_doc` the market map's export and `scored` tonight's scored gauges by id, each with its word, name and whether hatched."""
    skipped = spec.get("not_judged") or {}
    every = _futures(spec, outlook, texts)
    futures = [f for f in every if f["id"] not in skipped]  # a future nobody judged is no column: it is named apart
    words = spec.get("effects") or {}
    records = {o["id"]: o for o in opps_doc.get("opportunities") or []}
    marks = {m["id"]: m for m in (opps_doc.get("figures") or {}).get("marks") or []}
    stage = {s["opportunity"]: (spec.get("stages") or {}).get(s["stage"]) for s in opps_doc.get("sequence") or []}
    made = spec.get("made_by")

    prims, built = spec.get("primitives") or [], spec.get("builds") or {}

    def row(bid: str, b: dict[str, Any]) -> dict[str, Any]:
        o, judged = records[bid], b.get("futures") or {}
        laid = [
            {
                "future": f["id"],
                "key": f["key"],
                "name": f["name"],
                "effect": (j := judged.get(f["id"]) or {}).get("effect", "unchanged"),
                "word": words.get(j.get("effect", "unchanged"), j.get("effect", "unchanged")),
                "label": f"{f['name']}: {words.get(j.get('effect', 'unchanged'), 'unchanged')}",
                "reason": j.get("reason", ""),
            }
            for f in futures
        ]
        effects = {m["effect"] for m in laid}
        return {
            "id": bid,
            "n": marks[bid]["n"],
            "name": o["name"],
            "call": b["call"],
            "take": b["take"],
            "kills": b["kills"],
            "stage": stage.get(bid),
            # some future lifts it and none hurts it; a business no future touches is unjudged, not robust
            "holds": "stronger" in effects and not effects & {"weaker", "breaks"},
            "problem": o["bottleneck"],
            "profit": marks[bid]["verdict"],
            "primary": {"number": o["primary"].get("number"), "name": o["primary"]["name"], "href": f"/value-chain#mm-{o['primary']['id']}"},
            "href": f"/value-chain/opportunities#op-{bid}",
            "marks": laid,
            "moved": [m for m in laid if m["effect"] != "unchanged"],
            "builds": [{"id": p["id"], "name": p["name"]} for p in prims if p["id"] in built.get(bid, [])],
        }

    businesses = spec.get("businesses") or {}
    on: dict[str, list[int]] = {}
    for bid in businesses:
        if bid in records:
            on.setdefault(records[bid]["primary"]["id"], []).append(marks[bid]["n"])
    doc = {
        **_map(spec, futures, map_doc, scored, {k: sorted(v) for k, v in on.items()}),
        "made_by": {**made, "date": str(made["date"])} if made else None,
        "futures": futures,
        "future_groups": spec.get("future_groups") or [],
        "waiting": spec.get("waiting") or [],
        "not_judged": [{"name": f["name"], "why": skipped[f["id"]]} for f in every if f["id"] in skipped],
        "effects": [{"id": e, "word": words.get(e, e)} for e in (*MOVES, "unchanged")],
        "groups": [
            {**c, "businesses": [row(bid, b) for bid, b in businesses.items() if b.get("call") == c["id"] and bid in records]}
            for c in spec.get("calls") or []
        ],
    }
    rows = {b["id"]: b for g in doc["groups"] for b in g["businesses"]}
    names = {c["id"]: c for layer in doc["map"]["layers"] for c in layer["categories"]}
    chain = {c["id"]: c for c in spec.get("chains") or []}
    states, when = spec.get("chain_states") or {}, spec.get("chain_when") or {}
    doc["chains"] = [
        {
            "id": p["id"],
            "when": when.get(p["when"], p["when"]),
            "claim": p["claim"],
            "state": p["state"],
            "state_word": states.get(p["state"], p["state"]),
            "href": "/argument/migration#predictions",
            "says": c["says"],
            "parts": [{"id": i, "number": names[i]["number"], "name": names[i]["name"], "href": f"#ca-g-{i}"} for i in c.get("parts") or [] if i in names],
            "businesses": sorted(({"id": i, "n": rows[i]["n"], "name": rows[i]["name"]} for i in c.get("businesses") or [] if i in rows), key=lambda x: x["n"]),
        }
        for p in predictions
        if (c := chain.get(p["id"]))
    ]
    every_row = list(rows.values())
    doc["primitives"] = [{**p, "businesses": [{"n": b["n"], "name": b["name"]} for b in every_row if p["id"] in built.get(b["id"], [])]} for p in prims]
    doc["priors"], doc["priors_by"] = spec.get("priors") or [], spec.get("priors_by") or ""
    return doc
