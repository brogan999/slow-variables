"""What happens to each kind of firm (/firm/kinds). An archetype is a kind of firm tied to the census industries
behind it. Its figures are the census bundle's, summed here and laid out for the page's bars and pyramids; its roll-up
count is the trades list's. What the page says about the future is seed text, labelled as judgement.

Pure functions over the seed, the bundle and the exported trades list; nothing here reads the store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from . import census

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "firm_kinds.yaml"
TRADES = ROOT / "web" / "data" / "census" / "trades.json"
PARTS = ("passes", "waits_on_check", "held", "outside")
# the occupation code's major groups, gathered into the four layers the page draws
TIERS = {"managers": ("11",), "sales": ("41",), "support": ("43",)}
TIER_ORDER = ("managers", "professionals", "sales", "support")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def trades() -> dict[str, Any]:
    """The roll-up trades list as last exported; the export passes its own, fresh one."""
    return json.loads(TRADES.read_text()) if TRADES.exists() else {"trades": []}


def strings(spec: dict[str, Any]) -> list[str]:
    """The page's own words, for the tests that keep figures out of them."""
    out: list[str] = []

    def walk(x: Any) -> None:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in ("id", "naics", "trade", "sources", "opportunities", "kinds", "rung"):
                    walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk({k: v for k, v in spec.items() if k != "stages_order"})
    return out


def _tier(occ: str) -> str:
    return next((t for t, codes in TIERS.items() if occ[:2] in codes), "professionals")


def problems(spec: dict[str, Any], cspec: dict[str, Any], trades_doc: dict[str, Any]) -> list[str]:
    if not spec:
        return []
    errors: list[str] = []
    known = {r["naics"] for r in census.rows(census.bundle(cspec) / "industries.csv")}
    keys = {t["key"] for t in trades_doc.get("trades") or []}
    seen: set[str] = set()
    for k in spec.get("kinds") or []:
        where = f"firm kinds: {k.get('id')}"
        if k["id"] in seen:
            errors.append(f"{where} is listed twice")
        seen.add(k["id"])
        if not k.get("naics"):
            errors.append(f"{where} names no census industry")
        errors += [f"{where} names unknown census industry {n}" for n in k.get("naics") or [] if n not in known]
        if k.get("trade") and keys and k["trade"] not in keys:
            errors.append(f"{where} names unknown roll-up trade {k['trade']}")
    return errors


def build(spec: dict[str, Any], cspec: dict[str, Any], trades_doc: dict[str, Any]) -> dict[str, Any]:
    if not spec or not cspec:
        return {}
    d = census.bundle(cspec)
    industries = {r["naics"]: r for r in census.rows(d / "industries.csv")}
    by_trade = {t["key"]: t for t in trades_doc.get("trades") or []}
    mix: dict[str, dict[str, dict[str, float]]] = {}
    for r in census.rows(d / "role_industry.csv"):
        t = mix.setdefault(r["naics"], {}).setdefault(_tier(r["occ"]), {"payroll": 0.0, "passes": 0.0})
        t["payroll"] += census.num(r["wage_bill"]) or 0.0
        t["passes"] += census.num(r["passes_usd"]) or 0.0
    kinds = []
    for k in spec.get("kinds") or []:
        rows = [industries[n] for n in k["naics"]]
        total, know = (sum(float(r[c]) for r in rows) for c in ("total", "know"))
        passes, agreed3, waits = (sum(float(r[c]) for r in rows) for c in ("passes_usd", "agreed3_usd", "blocked"))
        parts = {"passes": passes, "waits_on_check": waits, "held": know - passes - waits, "outside": total - know}
        bar, x = [], 0.0
        for p in PARTS:  # the stacked bar, as percentages of the kind's whole payroll
            w = 100 * parts[p] / total
            bar.append({"part": p, "x": x, "w": w if p != PARTS[-1] else 100 - x})
            x += w
        tiers = {t: {"payroll": sum(mix.get(n, {}).get(t, {}).get("payroll", 0.0) for n in k["naics"]),
                     "passes": sum(mix.get(n, {}).get(t, {}).get("passes", 0.0) for n in k["naics"])} for t in TIER_ORDER}
        office = sum(t["payroll"] for t in tiers.values())
        widest = max(t["payroll"] for t in tiers.values())
        trade = by_trade.get(k.get("trade") or "")
        kinds.append({
            **{f: v for f, v in k.items() if f not in ("naics", "trade")},
            "naics": k["naics"],
            "titles": [r["naics_title"] for r in rows],
            "refs": [census.ref(cspec, "industries.csv", n) for n in k["naics"]],
            "payroll": total, "office_payroll": know, "agreed3": agreed3, **parts,
            **{f"share_{p}": parts[p] / total for p in PARTS}, "share_agreed3": agreed3 / total,
            "share_checkable": (passes + waits) / know,  # of the office work: passes, or would but for a check
            "bar": bar,
            "tiers": [{"id": t, "share": v["payroll"] / office, "share_passes": v["passes"] / v["payroll"] if v["payroll"] else 0.0,
                       "w": 100 * v["payroll"] / widest} for t, v in tiers.items()],
            "rollups": {"buyers": trade["rollups"]["n"], "deals": len(trade["deals"]), "obs_ids": [x["obs_id"] for x in trade["deals"]],
                        "trade": trade["name"]} if trade else None,
        })
    return {"version": cspec["version"], **{f: v for f, v in spec.items() if f != "kinds"}, "kinds": kinds}
