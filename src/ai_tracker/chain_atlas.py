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


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def _cells(outlook: dict[str, Any]) -> list[dict[str, Any]]:
    return (outlook.get("scenarios") or {}).get("cells") or []


def _figure(text: str) -> bool:
    return bool(FIGURE.search(YEAR.sub("", text)))


def problems(spec: dict[str, Any], opps: dict[str, Any], outlook: dict[str, Any]) -> list[str]:
    out: list[str] = []
    made = spec.get("made_by") or {}
    for k in ("model", "date", "method", "reviewed_by"):
        if not made.get(k):
            out.append(f"chain atlas: made_by has no {k}")
    calls = {c["id"] for c in spec.get("calls") or []}
    published = {o["id"] for o in opps.get("opportunities") or [] if o.get("published")}
    futures = {f"{c['progress']}/{c['rules']}" for c in _cells(outlook)}
    skipped = spec.get("not_judged") or {}
    for fid in sorted(futures):
        if not re.fullmatch(r"[a-z0-9_]+/[a-z0-9_]+", fid):
            out.append(f"chain atlas: future {fid} cannot name a mark on the page")
    for fid, why in skipped.items():
        if fid not in futures:
            out.append(f"chain atlas: not_judged names {fid}, which is not a future the outlook's grid fills")
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


def build(spec: dict[str, Any], opps_doc: dict[str, Any], outlook: dict[str, Any]) -> dict[str, Any]:
    """web/data/chain_atlas.json. `opps_doc` is the opportunities export: the records, their numbers and the sequence."""
    sc = outlook.get("scenarios") or {}
    label = {a["id"]: a["label"] for k in ("progress", "rules") for a in sc.get(k) or []}
    skipped = spec.get("not_judged") or {}
    every = [
        {
            "id": f"{c['progress']}/{c['rules']}",
            "key": f"{c['progress']}-{c['rules']}",
            "name": f"{label[c['progress']]}, {label[c['rules']][:1].lower()}{label[c['rules']][1:]}",
            "says": c.get("says") or "",
        }
        for c in _cells(outlook)
    ]
    futures = [f for f in every if f["id"] not in skipped]  # a future nobody judged is no column: it is named apart
    words = spec.get("effects") or {}
    records = {o["id"]: o for o in opps_doc.get("opportunities") or []}
    marks = {m["id"]: m for m in (opps_doc.get("figures") or {}).get("marks") or []}
    stage = {s["opportunity"]: (spec.get("stages") or {}).get(s["stage"]) for s in opps_doc.get("sequence") or []}
    made = spec.get("made_by")

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
        }

    businesses = spec.get("businesses") or {}
    return {
        "made_by": {**made, "date": str(made["date"])} if made else None,
        "futures": futures,
        "not_judged": [{"name": f["name"], "why": skipped[f["id"]]} for f in every if f["id"] in skipped],
        "effects": [{"id": e, "word": words.get(e, e)} for e in (*MOVES, "unchanged")],
        "groups": [
            {**c, "businesses": [row(bid, b) for bid, b in businesses.items() if b.get("call") == c["id"] and bid in records]}
            for c in spec.get("calls") or []
        ],
    }
