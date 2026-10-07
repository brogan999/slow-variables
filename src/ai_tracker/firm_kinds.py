"""What happens to each kind of firm (/firm/kinds). An archetype is a kind of firm tied to the census industries
behind it. Its figures are the census bundle's, summed here and laid out for the page's bars and pyramids; its roll-up
count is the trades list's. What the page says about the future is seed text, labelled as judgement.

Pure functions over the seed, the bundle and the exported trades list; nothing here reads the store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from . import census, chart, illustrations

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "firm_kinds.yaml"
TRADES = ROOT / "web" / "data" / "census" / "trades.json"
PARTS = ("passes", "waits_on_check", "needs_body", "held", "outside")
# the occupation code's major groups, gathered into the four layers the page draws
TIERS = {"managers": ("11",), "sales": ("41",), "support": ("43",)}
TIER_ORDER = ("managers", "professionals", "sales", "support")
OPPORTUNITIES = ROOT / "seed" / "opportunities.yaml"
# how a word for a layer's change is drawn against today's width: a drawing rule, stated in the key above the panels
DRAWN = {"gone": 0.0, "much_thinner": 0.35, "thinner": 0.7, "same": 1.0, "wider": 1.25}


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


def placed(spec: dict[str, Any]) -> list[str]:
    """The illustrations the page shows, as the seed names them: the opening one, then one for each kind."""
    return [x["illustration"] for x in [spec.get("anatomy") or {}, *(spec.get("kinds") or [])] if x.get("illustration")]


def _tier(occ: str) -> str:
    return next((t for t, codes in TIERS.items() if occ[:2] in codes), "professionals")


def by_industry(d: Path) -> dict[str, dict[str, float]]:
    """Knowledge-work payroll in each industry split by the bundle's task verdicts, the way census.shape() splits an
    occupational group: each role's task shares applied to that role's payroll in the industry. The same sum gives back
    the bundle's own passes and waits-on-a-check for every industry (tests/test_firm_kinds.py), so it is not an estimate."""
    shares: dict[str, dict[str, float]] = {}
    for t in census.rows(d / "tasks.csv"):
        part = "passes" if census.truth(t["passes"]) else "waits_on_check" if census.truth(t["blocked_by_missing_check"]) else "needs_body" if census.truth(t["physical"]) else "rest"
        role = shares.setdefault(t["occ"], {"passes": 0.0, "waits_on_check": 0.0, "needs_body": 0.0, "rest": 0.0})
        role[part] += census.num(t["task_payroll_usd"]) or 0.0
    out: dict[str, dict[str, float]] = {}
    for r in census.rows(d / "role_industry.csv"):
        role, pay = shares[r["occ"]], census.num(r["wage_bill"]) or 0.0
        whole = sum(role.values())
        row = out.setdefault(r["naics"], {"passes": 0.0, "waits_on_check": 0.0, "needs_body": 0.0})
        for part in row:
            row[part] += pay * role[part] / whole
    return out


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
        t = mix.setdefault(r["naics"], {}).setdefault(_tier(r["occ"]), {"payroll": 0.0, "passes": 0.0, "agreed3": 0.0})
        t["payroll"] += census.num(r["wage_bill"]) or 0.0
        t["passes"] += census.num(r["passes_usd"]) or 0.0
        t["agreed3"] += census.num(r["agreed3_usd"]) or 0.0
    split = by_industry(d)
    kinds = []
    for k in spec.get("kinds") or []:
        rows = [industries[n] for n in k["naics"]]
        total, know = (sum(float(r[c]) for r in rows) for c in ("total", "know"))
        passes, agreed3, waits = (sum(float(r[c]) for r in rows) for c in ("passes_usd", "agreed3_usd", "blocked"))
        body = sum(split[n]["needs_body"] for n in k["naics"])  # physical tasks inside knowledge roles
        parts = {"passes": passes, "waits_on_check": waits, "needs_body": body, "held": know - passes - waits - body, "outside": total - know}
        bar, x = [], 0.0
        for p in PARTS:  # the stacked bar, as percentages of the kind's whole payroll
            w = 100 * parts[p] / total
            bar.append({"part": p, "x": x, "w": w if p != PARTS[-1] else 100 - x})
            x += w
        tiers = {t: {f: sum(mix.get(n, {}).get(t, {}).get(f, 0.0) for n in k["naics"]) for f in ("payroll", "passes", "agreed3")} for t in TIER_ORDER}
        office = sum(t["payroll"] for t in tiers.values())
        widest = max(t["payroll"] for t in tiers.values())
        trade = by_trade.get(k.get("trade") or "")
        kinds.append({
            **{f: v for f, v in k.items() if f not in ("naics", "trade")},
            "naics": k["naics"],
            "illustration": illustrations.card(k.get("illustration")),  # the served file, its alt text and its stage
            "titles": [r["naics_title"] for r in rows],
            "refs": [census.ref(cspec, "industries.csv", n) for n in k["naics"]],
            "payroll": total, "knowledge_payroll": know, "agreed3": agreed3, **parts,
            **{f"share_{p}": parts[p] / total for p in PARTS}, "share_agreed3": agreed3 / total,
            "share_checkable": (passes + waits) / know,  # of the knowledge work: passes, or would but for a check
            "bar": bar, "agreed_w": 100 * agreed3 / total,  # the part all the models pass, drawn inside "passes"
            "tiers": [{"id": t, "share": v["payroll"] / office, "w": 100 * v["payroll"] / widest,
                       **{f"share_{f}": v[f] / v["payroll"] if v["payroll"] else 0.0 for f in ("passes", "agreed3")},
                       "pass_w": 100 * v["passes"] / v["payroll"] if v["payroll"] else 0.0,
                       "agreed_w": 100 * v["agreed3"] / v["payroll"] if v["payroll"] else 0.0} for t, v in tiers.items()],
            "rollups": {"buyers": trade["rollups"]["n"], "deals": len(trade["deals"]), "obs_ids": [x["obs_id"] for x in trade["deals"]],
                        "trade": trade["name"]} if trade else None,
        })
    opps = {o["id"]: o["name"] for o in (yaml.safe_load(OPPORTUNITIES.read_text()) or {}).get("opportunities") or []} if OPPORTUNITIES.exists() else {}
    ax = chart.axis([k["share_checkable"] for k in kinds], "share", zero=True)
    for k in kinds:
        now = k["tiers"]
        staged = [{"stage": "now", "judged": False, "tiers": [{"id": t["id"], "w": t["w"], "inner": t["pass_w"]} for t in now]}]
        # a judged layer carries its word and today's width, so the page can outline what it is drawn against
        for stage in ("next", "later"):
            words = (k.get("shape") or {}).get(stage) or ["same"] * len(now)
            staged.append({"stage": stage, "judged": True,
                           "tiers": [{"id": t["id"], "w": min(100.0, t["w"] * DRAWN[w]), "was": t["w"], "word": w} for t, w in zip(now, words)]})
        k["staged"] = staged
        # across: the share of knowledge-work payroll that passes or waits only on a check
        k["place"] = {"x": 100 - chart.y(k["share_checkable"], ax)}
    most = max([max(k["rollups"]["buyers"], k["rollups"]["deals"]) for k in kinds if k["rollups"]] or [1])
    for k in kinds:  # the roll-up bars share one scale: the largest count on the page is the full width
        if k["rollups"]:
            k["rollups"] |= {"buyers_w": 100 * k["rollups"]["buyers"] / most, "deals_w": 100 * k["rollups"]["deals"] / most}
    used = {w for k in spec.get("kinds") or [] for words in (k.get("shape") or {}).values() for w in words}
    needs = [{**n, "opportunities": [{"id": o, "name": opps.get(o, o), "href": f"/value-chain/opportunities#op-{o}"} for o in n.get("opportunities") or []]}
             for n in spec.get("needs") or []]
    return {
        "version": cspec["version"],
        **{f: v for f, v in spec.items() if f not in ("kinds", "needs", "sources")},
        "anatomy": {**(spec.get("anatomy") or {}), "illustration": illustrations.card((spec.get("anatomy") or {}).get("illustration"))},
        "sources": [{**x, "retrieved_at": str(x["retrieved_at"]), "n": i + 1} for i, x in enumerate(spec.get("sources") or [])],
        "needs": needs,
        "needs_grid": [{"id": n["id"], "cells": [n["id"] in (k.get("needs") or []) for k in kinds]} for n in needs],
        # the key to the judged drawings: each word in use at its drawn width, widest first
        "drawn": [{"word": w, "label": (spec.get("shape_words") or {}).get(w, w), "w": 100 * f} for w, f in sorted(DRAWN.items(), key=lambda x: -x[1]) if w in used],
        # the map: one row for each kind, grouped by the band this site judged and ordered by the measured share
        "map": {"x": {"ticks": [{"x": 100 - t["y"], "label": t["label"]} for t in ax["ticks"]]},
                "bands": [{"id": r, "label": label, "kinds": [k["id"] for k in sorted(kinds, key=lambda k: -k["share_checkable"]) if k.get("rung") == r]}
                          for r, label in (spec.get("rungs") or {}).items()]},
        "kinds": kinds,
    }
