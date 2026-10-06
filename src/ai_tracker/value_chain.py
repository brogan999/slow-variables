"""The value-chain assessment: how each layer's economics move, and profiles of the companies that matter.

A layer's judgement is an outlook position (folio value) that carries a `layer`: it has a rival and claims like any
other. Company profiles live in seed/value_chain.yaml with the primary sources they rest on. Both are this site's
judgement, drafted by a model and marked with who judged and who reviewed it; neither types a figure, since scale comes
only from observations.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .argument import unfetched

SPEC = Path(__file__).resolve().parents[2] / "seed" / "value_chain.yaml"
DIRECTIONS = {"commoditising": "commoditising", "holding": "holding", "tightening": "tightening"}
POWERS = {
    "scale_economies": "scale economies",
    "network_economies": "network economies",
    "counter_positioning": "counter-positioning",
    "switching_costs": "switching costs",
    "branding": "branding",
    "cornered_resource": "a cornered resource",
    "process_power": "process power",
}
# Hamilton Helmer's powers (7 Powers, 2016), glossed as docs/interpretation/helmer-seven-powers.md does
POWER_GLOSS = {
    "scale economies": "unit costs fall as volume grows, and a rival cannot match them without matching the volume",
    "network economies": "each user makes the product more valuable to the others, so the leader's lead feeds itself",
    "counter-positioning": "a newcomer's model the incumbent could copy only by damaging its own business",
    "switching costs": "a customer would lose money, time or work by moving to a rival",
    "branding": "buyers pay more for the same thing because of what they believe about who made it",
    "a cornered resource": "preferential access to something others need: a patent, a licence, a scarce input, a rare team",
    "process power": "a way of working that improves cost or quality and takes a rival years to learn",
}
CONCENTRATION = ("concentrated", "moderate", "diffuse")
ROLES = ("club", "candidate")
UNIT_TEXT = ("title", "mechanism", "case", "kill_shot", "commoditising", "stays_scarce", "converts_if")
PROFILE_TEXT = ("market", "customers")
RUBRIC = ("rent_kind", "appropriability", "complementary_assets", "asset_owner", "durability")
# names that carry digits but are not figures: filings, chips, memory generations, lithography
NAMES = re.compile(r"(?i)^(10-K|10-Q|20-F|[A-Z]{1,3}\d{2,3}[A-Z]?|GB\d{3}|HBM\d?E?|DDR\d|LPDDR\d|GPT-\d|N\d|A\d{2}|3D)$")
STALE_DAYS = 365


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) or {} if SPEC.exists() else {}


def units(outlook: dict[str, Any]) -> list[dict[str, Any]]:
    """The outlook positions that judge a layer of the chain."""
    return [p for p in outlook.get("positions") or [] if p.get("layer")]


def stray_digits(text: str) -> list[str]:
    """Digits other than a year ("2035", "the 2030s") or a product or filing name."""
    words = [re.sub(r"(['’]s)?[.]?$", "", w) for w in re.findall(r"[^\s,;:()/]*\d[^\s,;:()/]*", text)]
    year = r"((early|mid|late)-)?(1[6-9]\d\d|2[0-2]\d\d)s?"
    return [w for w in words if not NAMES.match(w) and not re.fullmatch(year, w)]


def problems(
    spec: dict[str, Any],
    outlook: dict[str, Any],
    layers: set[str],
    sublayers: set[str],
    inputs: set[str],
    entities: set[str],
    rubric: dict[str, Any],
) -> list[str]:
    """Errors for an assessment that cannot resolve: an unknown id or word, a typed figure, an unfetched source."""
    errors = []
    unit_ids = set()
    for u in units(outlook):
        where = f"value chain: unit {u['id']}"
        unit_ids.add(u["id"])
        if u.get("folio") != "value":
            errors.append(f"{where} judges a layer but is not in the value folio")
        if u["layer"] not in layers:
            errors.append(f"{where} names unknown layer {u['layer']}")
        if u.get("sublayer") and u["sublayer"] not in sublayers:
            errors.append(f"{where} names unknown sublayer {u['sublayer']}")
        if u.get("direction") not in DIRECTIONS:
            errors.append(f"{where} needs a direction of commoditising, holding or tightening")
        errors += [f"{where} names unknown power {p}" for p in u.get("powers") or [] if p not in POWERS]
        errors += [f"{where} names unknown bottleneck {b}" for b in u.get("bottlenecks") or [] if b not in inputs]
        for k in UNIT_TEXT:
            if k != "case" and not u.get(k):
                errors.append(f"{where} has no {k}")
            errors += [f"{where}: {k} types {d}" for d in stray_digits(re.sub(r"\[[a-z]+:[a-z0-9_]+\]", "", str(u.get(k) or "")))]
    sources = {s["id"]: s for s in spec.get("sources") or []}
    for u in units(outlook):
        errors += [f"value chain: unit {u['id']} cites unknown source {i}" for i in u.get("sources") or [] if i not in sources]
    for s in sources.values():
        if s.get("entity") not in entities and not s.get("filer"):
            errors.append(f"value chain: source {s['id']} names no known filer")  # a publisher that is not a company names itself
        if bad := unfetched(s):
            errors.append(f"value chain: source {s['id']} {bad}")
    words = rubric["inputs"]
    for c in spec.get("companies") or []:
        where = f"value chain: company {c.get('entity')}"
        if c.get("entity") not in entities:
            errors.append(f"{where} is not an entity")
        if c.get("role") not in ROLES:
            errors.append(f"{where} needs a role of club or candidate")
        errors += [f"{where} sits in unknown unit {u}" for u in c.get("units") or [] if u not in unit_ids]
        if not c.get("units") and not c.get("outside"):
            errors.append(f"{where} sits in no unit and does not say why")
        if c.get("concentration") not in CONCENTRATION:
            errors.append(f"{where} needs a customer concentration of concentrated, moderate or diffuse")
        errors += [f"{where} names unknown power {p.get('power')}" for p in c.get("powers") or [] if p.get("power") not in POWERS]
        errors += [f"{where} depends on unknown input {b}" for b in c.get("depends_on") or [] if b not in inputs]
        for k in RUBRIC:
            if c.get(k) not in words[k]:
                errors.append(f"{where}: {k} is not one of {', '.join(words[k])}")
        if not c.get("must_be_true") or not c.get("would_disprove"):
            errors.append(f"{where} needs what must be true and what would disprove it")
        for k, ids in (c.get("sources") or {}).items():
            errors += [f"{where}: {k} cites unknown source {i}" for i in ids if i not in sources]
        if not (c.get("sources") or {}).get("market"):
            errors.append(f"{where}: its market cites no source")
        text = [str(c.get(k) or "") for k in PROFILE_TEXT + ("outside",)]
        text += [p.get("why", "") for p in c.get("powers") or []] + list(c.get("must_be_true") or []) + list(c.get("would_disprove") or [])
        errors += [f"{where} types {d}" for t in text for d in stray_digits(t)]
        if not c.get("judged_by"):
            errors.append(f"{where} does not say who judged it")
        if c.get("reviewed_by") and not c.get("reviewed"):
            errors.append(f"{where} names who reviewed it but not when")
        if c.get("reviewed") and not c.get("reviewed_by"):
            errors.append(f"{where} dates a review but not who made it")
        if c.get("reviewed_by") and re.search(r"\breviews this profile before\b", c.get("disclosure") or ""):
            errors.append(f"{where}: its disclosure still promises a review it has had")
    return errors


def notes(spec: dict[str, Any], outlook: dict[str, Any], filed: dict[str, date], today: date) -> list[str]:
    """Attention, not errors: a profile read before its company's newest annual filing, or not reviewed in a year,
    or never reviewed; a unit with no named rival."""
    out = []
    for c in spec.get("companies") or []:
        eid, reviewed = c["entity"], c.get("reviewed")
        if not reviewed:
            out.append(f"value chain: profile {eid} has not been reviewed by a person")
        elif eid in filed and filed[eid] > reviewed:
            out.append(f"value chain: profile {eid} predates its annual filing of {filed[eid]}; review it")
        elif (today - reviewed).days > STALE_DAYS:
            out.append(f"value chain: profile {eid} was last reviewed {reviewed}; review it")
    out += [f"value chain: unit {u['id']} has no named rival" for u in units(outlook) if u.get("rival") == "none_found"]
    return out


def build(spec: dict[str, Any], outlook: dict[str, Any], rubric: dict[str, Any], words: dict[str, str]) -> dict[str, Any]:
    """The assessment as the site shows it: units with their words, profiles with where their rent pools."""
    from .futures import POOLS_WORDS, TIER_WORDS, pools, tier

    pos = {p["id"]: p for p in outlook.get("positions") or []}
    out_units = []
    for u in units(outlook):
        r = pos.get(u.get("rival"))
        out_units.append(
            {
                **{k: u.get(k) for k in ("id", "layer", "sublayer", "direction", "bottlenecks") + UNIT_TEXT},
                "powers": [POWERS[p] for p in u.get("powers") or []],
                "binding": [{"id": b, "word": words.get(b)} for b in u.get("bottlenecks") or []],
                "rival": {"id": r["id"], "title": r["title"]} if r else None,
            }
        )
    companies = []
    for c in spec.get("companies") or []:
        answers = {k: c[k] for k in RUBRIC}
        p, t = pools(answers, rubric), tier(answers, rubric)
        companies.append(
            {
                **{k: c.get(k) for k in ("entity", "role", "units", "outside", "market", "customers", "concentration", "must_be_true", "would_disprove", "judged_by", "reviewed_by", "reviewed", "disclosure")},
                "powers": [{"power": POWERS[x["power"]], "why": x.get("why")} for x in c.get("powers") or []],
                "depends_on": [{"id": b, "word": words.get(b)} for b in c.get("depends_on") or []],
                "rent": {**answers, "pools": p, "tier": t, "reads": _reads(p, t, TIER_WORDS, POOLS_WORDS)},
                "sources": c.get("sources") or {},
            }
        )
    return {"units": out_units, "companies": companies, "sources": spec.get("sources") or []}


def _reads(p: str, t: str, tiers: dict[str, str], pools_words: dict[str, str]) -> str:
    if p == "users":
        return "competed away to users"
    if t == "none":
        return "no lasting profit"
    return f"a {tiers[t]} profit, kept by {'the company itself' if p == 'innovator' else pools_words[p]}"


# What each direction means, in the page's own words: the label every drawn direction carries.
DIRECTION_MEANS = {
    "tightening": "getting scarcer, so whoever owns it can charge more",
    "holding": "its profit is steady for now",
    "commoditising": "becoming cheap and interchangeable, so the gain passes to buyers",
}
# The rent rule's steps as questions, one for each rule in seed/futures/rubric.yaml's `pools`, in its order (first match
# wins). The words restate the rubric's own rationale (after Teece); a test keeps the count level with the rules.
RENT_STEPS = [
    {"question": "Can the company stop others copying what it sells?",
     "why": "A patent, a secret or know-how that takes years to learn holds imitators off.",
     "keeps": "The company itself keeps the profit"},
    {"question": "If it can be copied: does the company itself own something scarce that customers need in order to use it?",
     "why": "Factories, a sales network, a licence or a base of users that a copier would also have to build.",
     "keeps": "The company itself keeps the profit"},
    {"question": "If it does not: does somebody else own that scarce thing?",
     "why": "When copying is easy, whoever owns what customers need to use the product collects instead of its maker.",
     "keeps": "The owner of the scarce thing keeps the profit"},
    {"question": "Otherwise: it is easy to copy and needs nothing scarce to reach customers.",
     "why": "Rivals enter and cut prices until nothing above the cost of staying in business is left.",
     "keeps": "Competition passes the gain to buyers"},
]


def figures(doc: dict[str, Any], layers: list[Any], sublayers: list[Any], primary: dict[str, str | None],
            rubric: dict[str, Any], short: dict[str, str] | None = None) -> dict[str, Any]:
    """The page's figures (Part 45g), laid out here so the web places and never counts. `primary` is every company on
    the market map with the sub-layer the tracker files it under. The chain: companies by layer beside each unit's
    judged direction. The grid: units against the powers they and their profiled companies name. The rent rule: which
    of its steps each profiled company stops at. Nothing in `doc` is changed."""
    from .futures import POOLS_WORDS, TIER_WORDS

    # the name readers know (NVIDIA, not NVIDIA Corp) where the caller has one
    known = {c["entity"]: (short or {}).get(c["entity"], c["name"]) for c in doc["companies"]}
    per_sub: dict[str | None, int] = {}
    for sub in primary.values():
        per_sub[sub] = per_sub.get(sub, 0) + 1
    subs = sorted(sublayers, key=lambda s: s.order)
    ordered = sorted(layers, key=lambda x: x.order)
    name = {s.id: s.name for s in subs} | {x.id: x.name for x in ordered}
    count = {x.id: sum(per_sub.get(s.id, 0) for s in subs if s.layer_id == x.id) for x in ordered}
    top = max(count.values(), default=0) or 1
    chain_layers = []
    for x in ordered:
        mine = [u for u in doc["units"] if u["layer"] == x.id]
        judged = {u["sublayer"]: u for u in mine}
        parts = [{"id": s.id, "name": s.name, "n": per_sub.get(s.id, 0),
                  "unit": (judged.get(s.id) or {}).get("id"), "direction": (judged.get(s.id) or {}).get("direction")}
                 for s in subs if s.layer_id == x.id]
        marks = {d: [{"unit": u["id"], "name": name[u["sublayer"] or x.id], "title": u["title"],
                      "href": f"/layers/{x.id}#assessment-{u['id']}"} for u in mine if u["direction"] == d] for d in DIRECTIONS}
        chain_layers.append({
            "id": x.id, "name": x.name, "n": count[x.id], "h": round(100 * count[x.id] / top, 1), "parts": parts,
            "marks": marks, "tally": {d: len(marks[d]) for d in DIRECTIONS},
            "unjudged": [{"id": p["id"], "name": p["name"], "n": p["n"]} for p in parts if not p["unit"]],
        })
    chain = {
        "layers": chain_layers, "n_companies": len(primary), "n_unfiled": per_sub.get(None, 0),
        "n_unjudged_companies": sum(p["n"] for x in chain_layers for p in x["unjudged"]),
        "n_unjudged_parts": sum(len(x["unjudged"]) for x in chain_layers),
        "tally": {d: sum(x["tally"][d] for x in chain_layers) for d in DIRECTIONS},
        "means": DIRECTION_MEANS,
    }
    cols = list(POWERS.values())
    rows = []
    for u in doc["units"]:
        cells = []
        for p in cols:
            held = [known[c["entity"]] for c in doc["companies"] if u["id"] in c["units"] and p in [x["power"] for x in c["powers"]]]
            cells.append({"power": p, "named": p in u["powers"], "companies": held, "n": len(held)})
        rows.append({"unit": u["id"], "layer": u["layer"], "layer_name": name[u["layer"]], "name": name[u["sublayer"] or u["layer"]],
                     "direction": u["direction"], "href": f"/layers/{u['layer']}#assessment-{u['id']}", "cells": cells,
                     "n_profiles": sum(1 for c in doc["companies"] if u["id"] in c["units"])})
    powers = {"cols": cols, "rows": rows, "n_units": len(rows), "n_units_naming": sum(1 for u in doc["units"] if u["powers"]),
              "n_profiles": len(doc["companies"])}
    rules = rubric["pools"]["rules"]
    steps = [{**RENT_STEPS[i], "companies": []} for i in range(len(rules))]
    for c in doc["companies"]:
        a = c["rent"]
        i = next(i for i, r in enumerate(rules) if all(a.get(k) == v for k, v in r["when"].items()))
        steps[i]["companies"].append({
            "entity": c["entity"], "name": known[c["entity"]], "reads": a["reads"], "tier": TIER_WORDS[a["tier"]],
            "kept_by": None if a["pools"] in ("users", "innovator") else POOLS_WORDS[a["pools"]],
        })
    for s in steps:
        s["n"] = len(s["companies"])
    return {"chain": chain, "powers": powers, "rent": {"steps": steps, "n": len(doc["companies"])}}
