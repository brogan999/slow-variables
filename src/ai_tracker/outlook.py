"""What happens from here (Part 11, section D; seed/outlook.yaml): named writers' positions on each crux, the claims
they imply, and tonight's reading of each claim. A claim's test is a fact and one operator, as on the migration page.
A claim with a rival test reads "both" when the rival's test holds too: tonight's reading cannot tell the sides apart.

The state logic is pure and tested on made-up facts; `build` resolves the facts from the store."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any

import yaml

from .argument import OPS, _bad_test, _holds, facts

SPEC = Path(__file__).resolve().parents[2] / "seed" / "outlook.yaml"
ESSAY = Path(__file__).resolve().parents[2] / "docs" / "argument" / "outlook.md"
STATES = ("holding", "failing", "both", "untestable")
FOLIOS = ("capability", "products", "adoption", "reorganisation", "value")
ATTRIBUTIONS = ("author", "extension", "site")
TOKEN = re.compile(r"\[(fact|cite|test|plate):([a-z0-9_]+)\]")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def _run(test: dict[str, Any] | None, f: dict[str, dict[str, Any] | None]) -> bool | None:
    """A test's verdict tonight: None when it has no test, no reading, or a reading gone stale."""
    if not test:
        return None
    reading = f.get(test["fact"])
    if not reading or reading.get("stale") or reading.get("value") is None:
        return None
    values = {k: (x["value"] if x else None) for k, x in f.items()}
    return _holds({k: v for k, v in test.items() if k != "fact"}, reading["value"], values)


def state(claim: dict[str, Any], f: dict[str, dict[str, Any] | None], today: date | None = None) -> str:
    """A claim with a `due` date is one about reaching a level by then: short of it before the date, it cannot be
    tested yet; past the date, it fails."""
    own, rival = _run(claim.get("test"), f), _run(claim.get("rival_test"), f)
    if own is None:
        return "untestable"
    if own and rival:
        return "both"  # the reading both sides expect settles nothing
    due = claim.get("due")
    if not own and due and (today or date.today()) <= date.fromisoformat(str(due)):
        return "untestable"
    return "holding" if own else "failing"


def claims(spec: dict[str, Any], f: dict[str, dict[str, Any] | None], today: date | None = None) -> list[dict[str, Any]]:
    positions = {p["id"]: p for p in spec.get("positions") or []}
    out = []
    for c in spec.get("claims") or []:
        p = positions[c["position"]]
        s = state(c, f, today)
        out.append(
            {
                **{k: c[k] for k in ("id", "position", "text", "falsifier") if k in c},
                "row": c.get("row"),
                "stage": c.get("stage"),
                "horizon_years": c.get("horizon_years"),
                "due": str(c["due"]) if c.get("due") else None,
                "test": c.get("test"),
                "rival_test": c.get("rival_test"),
                "fact": (c.get("test") or {}).get("fact"),
                "rival": p.get("rival"),
                "folio": p["folio"],
                "holders": p["holders"],
                "attribution": p["attribution"],
                "state": s,
                "expected": c.get("expect_state"),
            }
        )
    return out


def build(s: Any, today: date | None = None) -> dict[str, Any]:
    spec = load()
    if not spec:
        return {}
    today = today or date.today()
    f = facts(s, spec, today)
    cl = claims(spec, f, today)
    return {
        "as_of": min(max((x["as_of"] for x in f.values() if x and x["as_of"]), default=today.isoformat()), today.isoformat()),
        "essay": ESSAY.read_text() if ESSAY.exists() else "",
        "facts": f,
        "sources": spec["sources"],
        "positions": spec["positions"],
        "claims": cl,
        "tally": {k: sum(1 for c in cl if c["state"] == k) for k in STATES},
        "scenarios": spec.get("scenarios") or {},
        "agree": spec.get("agree") or [],
    }


def problems(spec: dict[str, Any], known_facts: dict[str, Any], rows: set[str], stages: set[str]) -> list[str]:
    """Errors for a ledger that cannot resolve: CI catches them before a page names a claim it cannot test."""
    if not spec:
        return []
    errors = []
    sources = {x["id"] for x in spec.get("sources") or []}
    positions = {p["id"]: p for p in spec.get("positions") or []}
    for x in spec.get("sources") or []:
        for k in ("who", "field", "finding", "work", "year", "url"):
            if not x.get(k):
                errors.append(f"outlook: source {x['id']} has no {k}")
        q = x.get("quote")
        if q and len(q.split()) >= 15:
            errors.append(f"outlook: source {x['id']} quotes fifteen words or more")
    for p in positions.values():
        where = f"outlook: position {p['id']}"
        if p.get("folio") not in FOLIOS:
            errors.append(f"{where} names an unknown folio")
        if p.get("attribution") not in ATTRIBUTIONS:
            errors.append(f"{where} needs an attribution of author, extension or site")
        errors += [f"{where} names unknown source {h}" for h in p.get("holders") or [] if h not in sources]
        if p.get("attribution") == "author" and not p.get("holders"):
            errors.append(f"{where} is credited to an author but names none")
        if p.get("rival") not in positions:
            errors.append(f"{where} has no rival position")
    for c in spec.get("claims") or []:
        where = f"outlook: claim {c['id']}"
        if c.get("position") not in positions:
            errors.append(f"{where} names an unknown position")
        if c.get("row") and c["row"] not in rows:
            errors.append(f"{where} names an unknown map row {c['row']}")
        if c.get("stage") and c["stage"] not in stages:
            errors.append(f"{where} names an unknown stage {c['stage']}")
        for key in ("test", "rival_test"):
            t = c.get(key)
            if t and t.get("fact") not in known_facts:
                errors.append(f"{where}: {key} reads unknown fact {t.get('fact')}")
            elif t and (bad := _bad_test({k: v for k, v in t.items() if k != "fact"}, known_facts)):
                errors.append(f"{where}: {key} {bad}")
        if not c.get("test") and not c.get("falsifier"):
            errors.append(f"{where} has neither a test nor the outcome that would prove it wrong")
        if c.get("expect_state") and c["expect_state"] not in STATES:
            errors.append(f"{where} expects an unknown state")
    return errors


__all__ = ["OPS", "STATES", "build", "claims", "load", "problems", "state"]
