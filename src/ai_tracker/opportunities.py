"""Businesses that could be built on the market map (Part 33, Stage 2).

Each record is the company that would turn one of the site's layer readings into a lasting profit: it names the
categories it sits in (seed/market_map.yaml), the readings it builds on (outlook positions and claims), the rent
rubric's inputs as the owner judges them and the Helmer powers it would build. Pool and tier come from the rubric's
fixed rules, and example companies come from the map's placements, so the page computes nothing. A record is shown
only when `published` is true; a blank field shows as not yet written.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .value_chain import POWER_GLOSS, POWERS, RUBRIC, stray_digits

SPEC = Path(__file__).resolve().parents[2] / "seed" / "opportunities.yaml"
TEXT = ("name", "customer", "bottleneck", "wedge", "unit_sold", "why_not_bundled", "durable_asset", "rent_reason",
        "falsifier", "prerequisites", "acquirers", "next_action")
REQUIRED = ("name", "bottleneck", "wedge", "durable_asset", "falsifier", "rent_reason")
STAGES = ("now", "next", "later", "endgame")
EXAMPLES = 6  # map companies named on a record before the rest are counted


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def _cited(ref: str) -> tuple[str, str]:
    kind, _, rid = ref.partition(":")
    return kind, rid


def problems(spec: dict[str, Any], map_spec: dict[str, Any], outlook: dict[str, Any], rubric: dict[str, Any]) -> list[str]:
    out: list[str] = []
    cats = {c["id"] for c in map_spec.get("categories") or []}
    positions = {p["id"] for p in outlook.get("positions") or []}
    claims = {c["id"] for c in outlook.get("claims") or []}
    inputs = rubric.get("inputs") or {}
    recs = spec.get("opportunities") or []
    ids = [o.get("id") for o in recs]
    for d in sorted({i for i in ids if ids.count(i) > 1}):
        out.append(f"opportunities: id {d} is used twice")
    for o in recs:
        w = f"opportunities: {o.get('id')}"
        for k in REQUIRED:
            if not str(o.get(k) or "").strip():
                out.append(f"{w} has no {k}")
        for c in [o.get("primary"), *(o.get("adjacent") or [])]:
            if c not in cats:
                out.append(f"{w} names unknown category {c}")
        if o.get("primary") in (o.get("adjacent") or []):
            out.append(f"{w} lists its primary category as adjacent too")
        for ref in o.get("builds_on") or []:
            kind, rid = _cited(ref)
            if kind == "pos" and rid not in positions:
                out.append(f"{w} builds on unknown position {rid}")
            elif kind == "claim" and rid not in claims:
                out.append(f"{w} builds on unknown claim {rid}")
            elif kind not in ("pos", "claim"):
                out.append(f"{w} cites {ref}, which is neither pos: nor claim:")
        if not o.get("builds_on"):
            out.append(f"{w} builds on none of the site's readings")
        for p in o.get("powers") or []:
            if p not in POWERS:
                out.append(f"{w} names unknown power {p}")
        rent = o.get("rent") or {}
        for k in RUBRIC:
            if rent.get(k) not in (inputs.get(k) or []):
                out.append(f"{w} has rent input {k}={rent.get(k)}, which the rubric does not know")
        if o.get("see_also") and o["see_also"] not in ids:
            out.append(f"{w} points to unknown record {o['see_also']}")
        for k in TEXT:
            for d in stray_digits(str(o.get(k) or "")):
                out.append(f"{w} {k} types a figure: {d}")
    published = {o.get("id") for o in recs if o.get("published")}
    for o in recs:
        if o.get("published") and o.get("see_also") in ids and o["see_also"] not in published:
            out.append(f"opportunities: {o.get('id')} points to unpublished record {o['see_also']}")
    stages = [s.get("stage") for s in spec.get("sequence") or []]
    if [x for x in STAGES if x in stages] != stages:
        out.append(f"opportunities: sequence stages must each appear once, in the order {', '.join(STAGES)}")
    for s in spec.get("sequence") or []:
        if s.get("stage") not in STAGES:
            out.append(f"opportunities: sequence stage {s.get('stage')} is not one of {', '.join(STAGES)}")
        if s.get("opportunity") not in ids:
            out.append(f"opportunities: sequence names unknown record {s.get('opportunity')}")
        elif s.get("opportunity") not in published:
            out.append(f"opportunities: sequence names unpublished record {s.get('opportunity')}")
        for d in stray_digits(str(s.get("gate") or "")):
            out.append(f"opportunities: sequence gate types a figure: {d}")
    return out


def build(spec: dict[str, Any], map_doc: dict[str, Any], outlook: dict[str, Any], rubric: dict[str, Any]) -> dict[str, Any]:
    """The records as the page shows them. `map_doc` is market_map.build's export, so categories carry their names,
    numbers and placed companies exactly as the map shows them."""
    from .futures import TIER_WORDS, pools, profit, profit_text, tier

    cats = {c["id"]: c for L in map_doc.get("layers") or [] for c in L["categories"]}
    pos = {p["id"]: p for p in outlook.get("positions") or []}
    claims = {c["id"]: c for c in outlook.get("claims") or []}
    recs = [o for o in spec.get("opportunities") or [] if o.get("published")]
    names = {o["id"]: o["name"] for o in recs}

    def cat(cid: str) -> dict[str, Any]:
        c = cats.get(cid) or {}
        return {"id": cid, "number": c.get("number"), "name": c.get("name", cid), "n_entities": c.get("n_entities", 0)}

    def cite(ref: str) -> dict[str, Any]:
        kind, rid = _cited(ref)
        if kind == "pos":
            p = pos.get(rid) or {}
            href = f"/layers/{p['layer']}#assessment-{rid}" if p.get("layer") else f"/outlook#position-{rid}"
            return {"ref": ref, "title": p.get("title", rid), "href": href}
        c = claims.get(rid) or {}
        return {"ref": ref, "title": c.get("text", rid), "href": f"/outlook#claim-{rid}"}

    out = []
    for o in recs:
        answers = {k: o["rent"][k] for k in RUBRIC}
        p, t = pools(answers, rubric), tier(answers, rubric)
        c = cats.get(o["primary"]) or {}
        live: list[str] = []
        for e in c.get("entities", []):  # already sorted verified first, then by name
            if not e.get("ownership") and e["name"] not in live:
                live.append(e["name"])
        reads = profit_text({"pools": p, "tier": t})
        out.append({
            **{k: o.get(k) or "" for k in ("id",) + TEXT},
            "primary": cat(o["primary"]),
            "adjacent": [cat(a) for a in o.get("adjacent") or []],
            "powers": [POWERS[x] for x in o.get("powers") or []],
            "builds_on": [cite(r) for r in o.get("builds_on") or []],
            "rent": {**answers, "pools": p, "tier": t, "profit": profit({"pools": p, "tier": t}), "reads": reads,
                     "verdict": reads[:1].upper() + reads[1:]},
            "examples": live[:EXAMPLES],
            "n_more_examples": max(0, len(live) - EXAMPLES),
            # unmapped means the tracker has placed nobody here; a category holding only acquired or closed
            # companies is mapped, it just has no independent company left to name
            "unmapped": not c.get("n_entities"),
            "none_independent": bool(c.get("n_entities")) and not live,
            "see_also": {"id": o["see_also"], "name": names[o["see_also"]]} if o.get("see_also") in names else None,
            "blank": [k.replace("_", " ") for k in ("customer", "prerequisites", "acquirers", "next_action") if not o.get(k)],
        })
    seq = [s for s in spec.get("sequence") or [] if s.get("opportunity") in names]
    sequence = [{**s, "name": names[s["opportunity"]], "label": "Needs" if i == len(seq) - 1 else "Opens the next stage when"}
                for i, s in enumerate(seq)]
    used = sorted({x for o in out for x in o["powers"]}, key=list(POWERS.values()).index)
    tiers = ("monopoly_like", "fat", "moderate", "thin", "none")
    by_tier = [{"tier": TIER_WORDS[t] if t != "none" else "no lasting profit", "n": n}
               for t in tiers if (n := sum(1 for o in out if o["rent"]["tier"] == t))]
    return {
        "reviewed_by": spec.get("reviewed_by"), "reviewed": str(spec.get("reviewed") or ""),
        "opportunities": out,
        "sequence": sequence,
        "powers": {k: POWER_GLOSS[k] for k in used},
        "counts": {"records": len(out), "unmapped": sum(1 for o in out if o["unmapped"]),
                   "by_tier": by_tier,
                   "kept_by_incumbents": sum(1 for o in out if o["rent"]["pools"] == "incumbents" and o["rent"]["tier"] != "none")},
    }
