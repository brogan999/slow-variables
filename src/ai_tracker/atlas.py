"""The Singularity Atlas (plan Part 18): how each part of life is expected to change as AI becomes transformative,
domain by domain and era by era, under each of the site's four worlds. The expectations are writers' views in the
site's words, each credited to a source the site has fetched; they are unscored and stay off the predictions board,
because most name no date and no test. The map counts sourced works, never a pressure or a probability, and each
domain reads the public series that bear on it tonight."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from . import argument, singularity
from .outlook import source_problems

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "atlas.yaml"
PLATES = ROOT / "web" / "public" / "atlas"
DOMAINS = ["economy", "work", "culture", "politics", "security", "technology", "health", "daily_life"]
ERAS = ["now", "first_decade", "long_run"]
# sourced works at which a cell's tint steps up: fixed, so every world's map reads the same way
LEVELS = (1, 2, 4, 7)
WIDTHS = (480, 768, 1024)
FILTER_SHARE = 1 / 3  # the world filter ships only if this share of entries names specific worlds


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def level(n: int) -> int:
    return sum(n >= t for t in LEVELS)


def cells(expectations: list[dict[str, Any]], worlds: list[str]) -> dict[tuple[str, str], dict[str, int]]:
    """Distinct sourced works per domain and era, overall and per world. A work that expects the change whichever
    way things go counts in every world; two lines from one work count once."""
    seen: dict[tuple[str, str], dict[str, set[str]]] = {}
    for e in expectations:
        c = seen.setdefault((e["domain"], e["era"]), {k: set() for k in ["all", *worlds]})
        c["all"].add(e["source"])
        for w in worlds if e["worlds"] == ["any"] else e["worlds"]:
            c[w].add(e["source"])
    return {k: {w: len(v) for w, v in c.items()} for k, c in seen.items()}


def srcset(file: str) -> str:
    return ", ".join(f"/atlas/{file}-{w}.webp {w}w" for w in WIDTHS)


def _plate(p: dict[str, Any]) -> dict[str, Any]:
    return {**p, "src": f"/atlas/{p['file']}-{WIDTHS[-1]}.webp", "srcset": srcset(p["file"])}


def _sources(spec: dict[str, Any], outlook_spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sing = singularity.load()
    return {
        x["id"]: x
        for x in [
            *(outlook_spec.get("sources") or []),
            *(sing.get("sources") or []),
            *(spec.get("sources") or []),
        ]
    }


def build(
    s: Any,
    today: date | None = None,
    outlook: dict[str, Any] | None = None,
    board_doc: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = load()
    if not spec:
        return {}
    today = today or date.today()
    from .outlook import load as load_outlook

    sing = singularity.load()
    srcs = _sources(spec, load_outlook())
    worlds = [
        {"id": w["id"], "label": w["label"], "short": w.get("short") or w["label"]} for w in sing["worlds"]
    ]
    wids = [w["id"] for w in worlds]
    wlabel = {w["id"]: w["short"] for w in worlds}
    facts = {
        **((outlook or {}).get("facts") or {}),
        **argument.facts(s, {"facts": spec.get("facts") or {}}, today),
    }
    board_rows = [r for f in (board_doc or {}).get("folios") or [] for r in f["rows"]]
    rows = {r["id"]: r for r in board_rows}
    eras = {e["id"]: e for e in spec["eras"]}
    doms = {d["id"]: d for d in spec["domains"]}

    def entry(e: dict[str, Any]) -> dict[str, Any]:
        x = srcs[e["source"]]
        r = rows.get(e.get("prediction") or "")
        return {
            "id": e["id"],
            "domain": e["domain"],
            "era": e["era"],
            "line": e["line"],
            "who": e.get("who") or x.get("short") or x["who"],
            "work": x["work"],
            "year": x["year"],
            "url": x["url"],
            "source": x["id"],
            "worlds": wids if e["worlds"] == ["any"] else e["worlds"],
            "any": e["worlds"] == ["any"],
            "world_labels": [] if e["worlds"] == ["any"] else [wlabel[w] for w in e["worlds"]],
            "reads": [
                {"id": k, "reading": singularity.reading(s, k, facts, today)} for k in e.get("reads") or []
            ],
            "prediction": {"word": r["word"], "href": r["href"]} if r else None,
        }

    entries = [entry(e) for e in spec["expectations"]]
    counts = cells(spec["expectations"], wids)
    fic_urls = {x["id"]: x["url"] for x in sing.get("sources") or []}
    specific = sum(1 for e in spec["expectations"] if e["worlds"] != ["any"])
    domains, map_rows = [], []
    for i, did in enumerate(DOMAINS):
        d = doms[did]
        mine = [e for e in entries if e["domain"] == did]
        readings = [
            {"id": k, "label": v, "reading": (r := singularity.reading(s, k, facts, today))}
            | {"year": r["as_of"][:4] if r else None}  # annual series read "Latest, 2025", never "tonight"
            for k, v in (d.get("readings") or {}).items()
        ]
        inds = {k for k in d.get("readings") or {} if k not in facts}
        leaning = [
            {"id": r["id"], "line": r["line"], "who": r["who"], "word": r["word"], "href": r["href"]}
            for r in board_rows
            if inds & set(r.get("indicators") or [])
        ][:6]
        names = {e["id"]: e["who"] for e in mine}
        dis = d.get("disagreement")
        domains.append(
            {
                "id": did,
                "n": i + 1,
                "name": d["name"],
                "thesis": d["thesis"],
                "thesis_from": sorted({names[k] for k in d["thesis_from"]}),
                "plate": _plate(spec["plates"][did]),
                "readings": readings,
                "eras": [{**eras[era], "entries": [e for e in mine if e["era"] == era]} for era in ERAS],
                "disagreement": dis
                and {
                    "question": dis["question"],
                    "sides": [
                        {"view": dis[k]["view"], "who": sorted({names[x] for x in dis[k]["entries"]})}
                        for k in ("side_a", "side_b")
                    ],
                },
                "fiction": [
                    {
                        "title": f["title"],
                        "author": f["author"],
                        "year": f["year_written"],
                        "line": f["line"],
                        "url": fic_urls.get(f["source"]),
                        "href": f"/singularity#fic-{f['source']}",
                    }
                    for f in sing.get("fiction") or []
                    if did in (f.get("domains") or [])
                ],
                "leaning": leaning,
                "sources": sorted(
                    {
                        e["source"]: {k: srcs[e["source"]][k] for k in ("id", "who", "work", "year", "url")}
                        for e in mine
                    }.values(),
                    key=lambda x: (x["year"], x["who"]),
                ),
                "prev": DOMAINS[i - 1] if i else None,
                "next": DOMAINS[i + 1] if i + 1 < len(DOMAINS) else None,
            }
        )
        head = next((r for r in readings if r["reading"]), None)
        map_rows.append(
            {
                "id": did,
                "name": d["name"],
                "href": f"/singularity/atlas/{did}",
                "plate": _plate(spec["plates"][did]),
                "headline": head,
                "cells": [
                    {
                        "era": era,
                        "href": f"/singularity/atlas/{did}#{era}",
                        "counts": [  # "all" first, then each world; the page shows one set at a time
                            {
                                "world": w,
                                "n": n,
                                "level": level(n),
                                "label": f"{d['name']}, {eras[era]['label'].lower()}"
                                + ("" if w == "all" else f", {wlabel[w].lower()}")
                                + f": {n} sourced {'work' if n == 1 else 'works'}",
                            }
                            for w, n in (counts.get((did, era)) or dict.fromkeys(["all", *wids], 0)).items()
                        ],
                    }
                    for era in ERAS
                ],
            }
        )
    return {
        "as_of": today.isoformat(),
        "intro": spec["intro"],
        "provenance": spec["provenance"],
        "hero": _plate(spec["plates"]["hero"]),
        "eras": [eras[e] for e in ERAS],
        "worlds": worlds,
        "levels": list(LEVELS),
        "filter": specific >= FILTER_SHARE * len(entries),
        "map": map_rows,
        "domains": domains,
        "count": {"expectations": len(entries), "sources": len({e["source"] for e in entries})},
    }


def problems(
    spec: dict[str, Any],
    outlook_spec: dict[str, Any],
    known_facts: set[str],
    indicator_ids: set[str],
    prediction_ids: set[str],
) -> list[str]:
    """Errors CI catches before a page names a source, reading or plate it cannot resolve."""
    if not spec:
        return []
    errors = source_problems(spec.get("sources") or [], "atlas")
    sing = singularity.load()
    mine = [x["url"] for x in spec.get("sources") or []]
    elsewhere = {x["url"] for f in (sing, outlook_spec) for x in f.get("sources") or []}
    errors += [f"atlas: source url {u} is listed twice" for u in {u for u in mine if mine.count(u) > 1}]
    errors += [
        f"atlas: source url {u} is already a singularity or outlook source" for u in set(mine) & elsewhere
    ]
    srcs = _sources(spec, outlook_spec)
    worlds = {w["id"] for w in sing.get("worlds") or []}
    readable = known_facts | set(spec.get("facts") or {}) | indicator_ids
    exp = {e["id"]: e for e in spec.get("expectations") or []}
    if len(exp) != len(spec.get("expectations") or []):
        errors.append("atlas: two expectations share an id")
    for e in exp.values():
        where = f"atlas: expectation {e['id']}"
        if e.get("domain") not in DOMAINS:
            errors.append(f"{where} names an unknown domain")
        if e.get("era") not in ERAS:
            errors.append(f"{where} names an unknown era")
        if not e.get("worlds") or (e["worlds"] != ["any"] and not set(e["worlds"]) <= worlds):
            errors.append(f"{where} names worlds outside the four (or [any])")
        if e.get("source") not in srcs:
            errors.append(f"{where} names unknown source {e.get('source')}")
        if not e.get("line"):
            errors.append(f"{where} has no line")
        errors += [
            f"{where} reads {k}, no fact or published indicator"
            for k in e.get("reads") or []
            if k not in readable
        ]
        if e.get("prediction") and e["prediction"] not in prediction_ids:
            errors.append(f"{where} links unknown prediction {e['prediction']}")
    if {d["id"] for d in spec.get("domains") or []} != set(DOMAINS):
        errors.append("atlas: domains must be exactly the eight")
    for d in spec.get("domains") or []:
        where = f"atlas: domain {d['id']}"
        mine = {k for k, e in exp.items() if e.get("domain") == d["id"]}

        def who(k: str) -> str:
            e = exp[k]
            x = srcs.get(e.get("source"), {})
            return e.get("who") or x.get("short") or x.get("who", "")

        tf = d.get("thesis_from") or []
        if not set(tf) <= mine:
            errors.append(f"{where} thesis_from names an expectation outside the domain")
        elif len({who(k) for k in tf}) < 2:
            errors.append(f"{where} thesis rests on fewer than two writers")
        dis = d.get("disagreement")
        if dis:
            a, b = (set(dis[k]["entries"]) for k in ("side_a", "side_b"))
            if not (a | b) <= mine or not a or not b:
                errors.append(f"{where} disagreement names an expectation outside the domain")
            elif {who(k) for k in a} & {who(k) for k in b}:
                errors.append(f"{where} disagreement puts one writer on both sides")
        errors += [
            f"{where} reads {k}, no fact or published indicator"
            for k in d.get("readings") or {}
            if k not in readable
        ]
        if d["id"] not in (spec.get("plates") or {}):
            errors.append(f"{where} has no plate")
    for k, p in (spec.get("plates") or {}).items():
        if not p.get("alt") or not p.get("allegory"):
            errors.append(f"atlas: plate {k} needs alt text and an allegory")
        errors += [
            f"atlas: plate file {p['file']}-{w}.webp is missing"
            for w in WIDTHS
            if not (PLATES / f"{p['file']}-{w}.webp").exists()
        ]
    errors += [
        f"atlas: fiction {f['title']} names an unknown domain"
        for f in sing.get("fiction") or []
        if not set(f.get("domains") or []) <= set(DOMAINS)
    ]
    return errors


def strings(spec: dict[str, Any]) -> list[str]:
    """The site's own sentences, held to the no-digit and no-number-word rules."""
    out = [spec.get("intro") or "", spec.get("provenance") or ""]
    out += [e[k] for e in spec.get("eras") or [] for k in ("label", "definition")]
    out += [d[k] for d in spec.get("domains") or [] for k in ("name", "thesis")]
    out += [(d.get("disagreement") or {}).get("question") or "" for d in spec.get("domains") or []]
    out += [v for d in spec.get("domains") or [] for v in (d.get("readings") or {}).values()]
    out += [
        p[k] for p in (spec.get("plates") or {}).values() for k in ("alt", "allegory", "caption") if p.get(k)
    ]
    out += [w.get("short") or "" for w in singularity.load().get("worlds") or []]
    return [t for t in out if t]


def credited(spec: dict[str, Any]) -> list[str]:
    """Sentences credited to a writer by construction: held to the no-digit rule, and may state a figure in words."""
    out = [e["line"] for e in spec.get("expectations") or []]
    out += [
        d["disagreement"][k]["view"]
        for d in spec.get("domains") or []
        if d.get("disagreement")
        for k in ("side_a", "side_b")
    ]
    return out
