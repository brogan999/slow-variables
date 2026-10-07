"""The granular value-chain market map (Part 33): Alex's taxonomy of categories and leaves, with the tracker's entities placed in it.

Every sub-layer has one default category. An entity sits in its primary sub-layer's default unless its own `places` say
otherwise, and each place names the source and section label it came from. Excluded entities are off the map only; they
stay in the tracker. The map types no figure: counts are made here and exported, never in the browser.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

import yaml

from .schema import Entity

SPEC = Path(__file__).resolve().parents[2] / "seed" / "market_map.yaml"
CHIPS = 14  # company chips shown on a card before "+N"


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def _primary(e: Entity, today: date) -> str | None:
    live = [m for m in e.memberships if m.sublayer_id and (m.to_date is None or m.to_date > today)]
    live = live or [m for m in e.memberships if m.sublayer_id]  # an acquired company stays on the map, marked as such
    first = next((m for m in live if m.is_primary), live[0] if live else None)
    return first.sublayer_id if first else None


SUFFIX = re.compile(r"(,? Inc\.?| Corp(oration)?\.?| Group N\.V\.| N\.V\.| plc| Ltd\.?)$")


def display(e: Entity) -> str:
    """A filer's short name as readers know it (NVIDIA, not NVIDIA Corp); the legal name stays in `name`. Only SEC filers carry
    legal names, and only an alias that starts the name or spells its initials qualifies, so an old name kept as an alias
    after a rename, or a product name, is never shown."""
    if not e.cik:
        return e.name
    initials = "".join(w[0] for w in re.findall(r"[A-Za-z]+", e.name)).upper()
    ok = [a for a in e.aliases if len(a) < len(e.name) and (e.name.startswith(a) or a.upper() == initials)]
    return ok[0] if ok else SUFFIX.sub("", e.name)


def day(d: str | None) -> str | None:
    """A read date as the site's prose writes dates: 28 Sep 2026."""
    return date.fromisoformat(d).strftime("%-d %b %Y") if d else None


def placements(spec: dict[str, Any], entities: Iterable[Entity], today: date) -> list[dict[str, Any]]:
    """One row per (entity, category, leaf): its own places, else its primary sub-layer's default category."""
    excluded = spec.get("excluded") or {}
    default = spec.get("sublayers") or {}
    rows: list[dict[str, Any]] = []
    for e in entities:
        if e.id in excluded:
            continue
        if e.places:
            rows += [{"entity": e.id, "cat": p.cat, "leaf": p.leaf, "source": p.source, "label": p.label,
                      "read": p.read.isoformat() if p.read else None, "default": False} for p in e.places]
        elif (sub := _primary(e, today)) and sub in default:
            rows.append({"entity": e.id, "cat": default[sub], "leaf": None, "source": "tracker", "label": sub,
                         "read": None, "default": True})
    return rows


def problems(spec: dict[str, Any], entities: list[Entity], sublayer_ids: set[str], indicator_ids: set[str]) -> list[str]:
    out: list[str] = []
    layers = {x["id"] for x in spec.get("layers") or []}
    cats = {c["id"]: c for c in spec.get("categories") or []}
    ids = {e.id for e in entities}
    for c in cats.values():
        if c.get("layer") not in layers:
            out.append(f"market map: category {c['id']} names unknown layer {c.get('layer')}")
    default = spec.get("sublayers") or {}
    for s in sorted(sublayer_ids - set(default)):
        out.append(f"market map: sub-layer {s} has no default category")
    for s, c in default.items():
        if s not in sublayer_ids:
            out.append(f"market map: {s} is not a sub-layer")
        if c not in cats:
            out.append(f"market map: sub-layer {s} defaults to unknown category {c}")
    for eid in spec.get("excluded") or {}:
        if eid not in ids:
            out.append(f"market map: excluded entity {eid} does not exist")
    for e in entities:
        if e.places and e.id in (spec.get("excluded") or {}):
            out.append(f"market map: {e.id} is excluded but has places")
        for p in e.places:
            c = cats.get(p.cat)
            if not c:
                out.append(f"market map: {e.id} placed in unknown category {p.cat}")
            elif p.leaf and p.leaf not in c.get("leaves", []):
                out.append(f"market map: {e.id} placed in unknown leaf '{p.leaf}' of {p.cat}")
            elif c.get("out_of_scope"):
                out.append(f"market map: {e.id} placed in {p.cat}, which is out of scope")
            if not p.label.strip():
                out.append(f"market map: {e.id} has a place with no label")
    for i, c in (spec.get("indicators") or {}).items():
        if i not in indicator_ids:
            out.append(f"market map: indicator {i} does not exist")
        if c not in cats:
            out.append(f"market map: indicator {i} placed in unknown category {c}")
    return out


def build(spec: dict[str, Any], entities: list[Entity], indicators: list[dict[str, Any]], venture: set[str],
          today: date) -> dict[str, Any]:
    """The export: layers, each with its categories, their placed entities (with provenance) and indicators, and counts.

    `indicators` are published cards ({id, name, sublayer_id}); `venture` the sub-layers that have a venture file."""
    by_id = {e.id: e for e in entities}
    rows = placements(spec, entities, today)
    default = spec.get("sublayers") or {}
    ind_cat = spec.get("indicators") or {}
    cats_out: dict[str, dict[str, Any]] = {}
    for c in spec.get("categories") or []:
        cats_out[c["id"]] = {
            "id": c["id"], "number": c["number"], "name": c["name"], "layer": c["layer"],
            "out_of_scope": c.get("out_of_scope"),
            "default_of": sorted(s for s, d in default.items() if d == c["id"]),
            "entities": [], "indicators": [], "leaves": [{"name": lf, "n": 0} for lf in c.get("leaves", [])],
        }
    for r in rows:
        e = by_id[r["entity"]]
        ended = [m.to_date.isoformat() for m in e.memberships if m.to_date and m.to_date <= today]
        cats_out[r["cat"]]["entities"].append({
            "id": e.id, "name": display(e), "legal_name": e.name, "verified": e.verified, "leaf": r["leaf"], "source": r["source"],
            "label": r["label"], "read": day(r["read"]), "default": r["default"], "ended": max(ended) if ended else None,
            "ownership": e.ownership or ("acquired" if ended else None), "ownership_note": e.ownership_note,
        })
    for i in indicators:
        cat = ind_cat.get(i["id"]) or default.get(i.get("sublayer_id") or "") or "outcomes"
        if cat in cats_out:
            cats_out[cat]["indicators"].append({"id": i["id"], "name": i["name"]})
    for c in cats_out.values():
        c["entities"].sort(key=lambda x: (not x["verified"], x["name"].lower()))
        ids = {x["id"] for x in c["entities"]}
        c["n_entities"] = len(ids)
        c["n_verified"] = len({x["id"] for x in c["entities"] if x["verified"]})
        for lf in c["leaves"]:
            lf["n"] = len({x["id"] for x in c["entities"] if x["leaf"] == lf["name"]})
        c["leaves_covered"] = sum(1 for lf in c["leaves"] if lf["n"])
        c["from_sublayers"] = sorted({s for x in c["entities"] for s in [_primary(by_id[x["id"]], today)] if s})
        c["venture_sublayers"] = [s for s in c["default_of"] if s in venture]
        order = list(dict.fromkeys(x["id"] for x in c["entities"]))
        c["chips"] = order[:CHIPS]  # the page shows these as chips; the rest are counted here, never in the browser
        c["n_more"] = max(0, len(order) - CHIPS)
        c["n_leaves"] = len(c["leaves"])
        c["n_indicators"] = len(c["indicators"])
    layers = []
    for L in spec.get("layers") or []:
        cs = [c for c in cats_out.values() if c["layer"] == L["id"]]
        layers.append({**L, "categories": cs, "n_categories": len(cs),
                       "n_entities": len({x["id"] for c in cs for x in c["entities"]}),
                       "n_unmapped": 0 if L.get("indicator_only") else sum(1 for c in cs if not c["entities"] and not c["out_of_scope"])})
    mapped = [c for c in cats_out.values() if c["layer"] != "outcomes"]
    return {
        "credit": spec.get("credit"),
        "layers": layers,
        "figures": figures(layers),
        "counts": {
            "layers": len(layers),
            "categories": len(mapped),
            "leaves": sum(len(c["leaves"]) for c in mapped),
            "entities": len({r["entity"] for r in rows}),
            "placements": len(rows),
            "unmapped_categories": sum(1 for c in mapped if not c["entities"] and not c["out_of_scope"]),
            "excluded": len(spec.get("excluded") or {}),
            "indicators": sum(len(c["indicators"]) for c in cats_out.values()),
        },
    }


def primaries(spec: dict[str, Any], entities: Iterable[Entity], today: date) -> dict[str, str | None]:
    """Every entity on the map with the sub-layer the tracker files it under (none where it has no membership)."""
    by_id = {e.id: e for e in entities}
    return {i: _primary(by_id[i], today) for i in sorted({r["entity"] for r in placements(spec, by_id.values(), today)})}


STATES = {None: "independent", "acquired": "bought", "being_acquired": "bought", "defunct": "closed"}
THIN = 5  # a category holding this many companies or fewer is listed as thin: the tracker's reach, not the market's size


def _pct(n: float, of: float) -> float:
    return round(100 * n / of, 1) if of else 0.0


def figures(layers: list[dict[str, Any]]) -> dict[str, Any]:
    """The map's figures (Part 45g), laid out here so the page places and never counts: companies in each category split
    by ownership state on one scale, the share of each layer's companies the tracker has verified, and the parts of
    each layer that hold a company or none. Each company counts once in a category and once in a layer."""
    mapped = [L for L in layers if not L.get("indicator_only")]
    top = max((c["n_entities"] for L in mapped for c in L["categories"]), default=0)
    cat_layers, verified, coverage, thin = [], [], [], []
    totals = {"independent": 0, "bought": 0, "closed": 0}
    everyone: dict[str, bool] = {}
    for L in mapped:
        rows = []
        for c in L["categories"]:
            state = {e["id"]: STATES[e["ownership"]] for e in c["entities"]}
            segs, x, upto = [], 0.0, 0
            for k in totals:
                n = sum(1 for v in state.values() if v == k)
                totals[k] += n
                upto += n
                end = _pct(upto, top)  # each segment ends where the running count does, so rounding never drifts
                segs.append({"state": k, "n": n, "x": x, "w": round(end - x, 1)})
                x = end
            rows.append({"id": c["id"], "number": c["number"], "name": c["name"], "n": c["n_entities"], "w": x,
                         "out_of_scope": bool(c["out_of_scope"]), "segs": segs,
                         "leaves": [{"name": p["name"], "n": p["n"]} for p in c["leaves"]]})
        cat_layers.append({"id": L["id"], "number": L["number"], "name": L["name"], "rows": rows})
        seen = {e["id"]: e["verified"] for c in L["categories"] for e in c["entities"]}
        everyone.update(seen)
        verified.append(_verified(L["id"], L["name"], seen))
        scope = [c for c in L["categories"] if not c["out_of_scope"]]
        n_parts, n_covered = sum(c["n_leaves"] for c in scope), sum(c["leaves_covered"] for c in scope)
        coverage.append({"id": L["id"], "number": L["number"], "name": L["name"], "n_parts": n_parts, "n_covered": n_covered,
                         "n_empty": n_parts - n_covered,
                         "n_unassigned": len({e["id"] for c in scope for e in c["entities"] if e["leaf"] is None})})
        thin += [{"id": c["id"], "number": c["number"], "name": c["name"], "layer": L["name"], "n": c["n_entities"],
                  "n_parts": c["n_leaves"], "n_covered": c["leaves_covered"]} for c in scope if c["n_entities"] <= THIN]
    verified.append(_verified("all", "The whole map", everyone))
    return {
        "categories": {"top": top, "totals": totals, "layers": cat_layers},
        "verified": {"rows": verified},
        "coverage": {"rows": coverage, "n_parts": sum(r["n_parts"] for r in coverage),
                     "n_empty": sum(r["n_empty"] for r in coverage), "thin_at": THIN, "thin": thin},
    }


def _verified(id_: str, name: str, seen: dict[str, bool]) -> dict[str, Any]:
    n, v = len(seen), sum(seen.values())
    w = _pct(v, n)
    return {"id": id_, "name": name, "n": n, "n_verified": v, "n_unverified": n - v, "share_verified": v / n if n else 0.0,
            "segs": [{"state": "verified", "x": 0, "w": w}, {"state": "unverified", "x": w, "w": round(100 - w, 1)}]}
