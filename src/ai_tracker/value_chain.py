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
