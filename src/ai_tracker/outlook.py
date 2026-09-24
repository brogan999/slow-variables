"""What happens from here (Part 11, section D; seed/outlook.yaml): named writers' positions on each crux, the claims
they imply, and tonight's reading of each claim. A claim's test is a fact and one operator, as on the migration page.
A claim with a rival test reads "both" when the rival's test holds too: tonight's reading cannot tell the sides apart.
A scenario cell is consistent with tonight's readings unless one of its signposts is failing its test.

The state logic is pure and tested on made-up facts; `build` resolves the facts from the store."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from .argument import OPS, _bad_test, _holds, facts, unfetched

SPEC = Path(__file__).resolve().parents[2] / "seed" / "outlook.yaml"
ESSAY = Path(__file__).resolve().parents[2] / "docs" / "argument" / "outlook.md"
STATES = ("holding", "failing", "both", "untestable")
FOLIOS = ("capability", "products", "adoption", "reorganisation", "value")
ATTRIBUTIONS = ("author", "extension", "site")
TOKEN = re.compile(r"\[(fact|cite|test|plate):([a-z0-9_]+)\]")
PLATES = ("frontier", "reliability", "adoption", "stack", "scenarios", "board")
QUOTED = re.compile(r"[\"“]([^\"”]+)[\"”]")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def _run(test: dict[str, Any] | None, f: dict[str, dict[str, Any] | None]) -> bool | None:
    """A test's verdict tonight: None when it has no test, no reading, or a reading gone stale on either side."""
    if not test:
        return None
    reading = f.get(test["fact"])
    if not reading or reading.get("stale") or reading.get("value") is None:
        return None
    values = {k: (x["value"] if x and not x.get("stale") else None) for k, x in f.items()}
    return _holds({k: v for k, v in test.items() if k != "fact"}, reading["value"], values)


def _on(d: Any) -> date:
    return d if isinstance(d, date) else date.fromisoformat(str(d))


def state(claim: dict[str, Any], f: dict[str, dict[str, Any] | None], today: date | None = None) -> str:
    """A claim with a `due` date is about reaching a level by then: short of it, it cannot be tested until the date has
    passed on the reading's own clock. A rival test stops applying on `rival_until`, on the same clock. The clock is
    the newest reading's date (a quarterly figure is published weeks after its quarter ends), or, for a running record
    that only moves when it is broken, the calendar plus `grace_days` for results to be published. While a rival test
    applies but cannot run, the claim cannot claim a win. A rival's date and a `due` date are read alike, so a
    reading dated on the last day both sides counted reads the same way for both."""
    today = today or date.today()
    own = _run(claim.get("test"), f)
    if own is None:
        return "untestable"
    reading = f.get(claim["test"]["fact"]) or {}
    grace = claim.get("grace_days")
    clock = (
        (today - timedelta(days=grace))
        if grace is not None
        else _on(reading.get("newest") or reading.get("as_of") or today)
    )
    rt = (
        claim.get("rival_test")
        if not claim.get("rival_until") or clock < _on(claim["rival_until"])
        else None
    )
    rival = _run(rt, f)
    if rt and rival is None and own:
        return "untestable"  # a win needs the rival's reading too
    if own and rival:
        return "both"  # the reading both sides expect settles nothing
    due = claim.get("due")
    if not own and due and clock < _on(due):
        return "untestable"
    return "holding" if own else "failing"


def claims(
    spec: dict[str, Any], f: dict[str, dict[str, Any] | None], today: date | None = None
) -> list[dict[str, Any]]:
    positions = {p["id"]: p for p in spec.get("positions") or []}
    out = []
    for c in spec.get("claims") or []:
        p = positions[c["position"]]
        s = state(c, f, today)
        who = c.get("attribution") or p["attribution"]  # a claim can be this site's own reading of an author's position
        out.append(
            {
                **{k: c[k] for k in ("id", "position", "text", "falsifier") if k in c},
                "row": c.get("row"),
                "stage": c.get("stage"),
                "horizon_years": c.get("horizon_years"),
                "due": str(c["due"]) if c.get("due") else None,
                "rival_until": str(c["rival_until"]) if c.get("rival_until") else None,
                "grace_days": c.get("grace_days"),
                "test": c.get("test"),
                "rival_test": c.get("rival_test"),
                "fact": (c.get("test") or {}).get("fact"),
                "rival": p.get("rival"),
                "folio": p["folio"],
                "holders": [] if who == "site" else c.get("holders") or p["holders"],
                "attribution": who,
                "state": s,
                "expected": c.get("expect_state"),
            }
        )
    return out


def scenarios(spec: dict[str, Any], cl: list[dict[str, Any]]) -> dict[str, Any]:
    states = {c["id"]: c["state"] for c in cl}
    sc = spec.get("scenarios") or {}
    cells = []
    for c in sc.get("cells") or []:
        signs = [{"claim": k, "state": states[k]} for k in c.get("signposts") or []]
        cells.append(
            {
                **c,
                "signposts": signs,
                "tested": any(x["state"] != "untestable" for x in signs),
                "consistent": all(x["state"] != "failing" for x in signs),
            }
        )
    return {**sc, "cells": cells}


def strings(spec: dict[str, Any]) -> list[str]:
    """Every sentence the ledger puts in front of a reader, for the tests that keep figures and advice out."""
    out = [
        p[k]
        for p in spec.get("positions") or []
        for k in ("title", "mechanism", "case", "kill_shot")
        if p.get(k)
    ]
    out += [c[k] for c in spec.get("claims") or [] for k in ("text", "falsifier") if c.get(k)]
    sc = spec.get("scenarios") or {}
    out += [x["label"] for axis in ("progress", "rules") for x in sc.get(axis) or []]
    out += [c[k] for c in sc.get("cells") or [] for k in ("says", "paid") if c.get(k)]
    out += [a[k] for a in sc.get("anchors") or [] for k in ("text",) if a.get(k)]
    out += [a[k] for a in spec.get("agree") or [] for k in ("text", "dissent_text") if a.get(k)]
    return out


def essay_problems(text: str, spec: dict[str, Any]) -> list[str]:
    """Tokens that do not resolve, and quoted words that are not a source's one checked quote."""
    sources = {x["id"] for x in spec.get("sources") or []}
    numeric = {
        c["id"]
        for c in spec.get("claims") or []
        for k, v in (c.get("test") or {}).items()
        if k in OPS and not isinstance(v, str)
    }
    known = {"fact": set(spec.get("facts") or {}), "cite": sources, "test": numeric, "plate": set(PLATES)}
    errors = [f"outlook: [{k}:{v}] does not resolve" for k, v in TOKEN.findall(text) if v not in known[k]]
    quotes = {x["quote"].rstrip(".").strip(): x["id"] for x in spec.get("sources") or [] if x.get("quote")}
    seen: dict[str, int] = {}
    for sentence in re.split(r"(?<=[.!?])\s+(?=[A-Z\[\"“])", " ".join([text, *strings(spec)])):
        for q in QUOTED.findall(sentence):
            k = quotes.get(q.rstrip(".,").strip())
            if not k:
                errors.append(f"outlook: quoted words that are no source's checked quote: {q[:50]}")
            elif f"[cite:{k}]" not in sentence:
                errors.append(f"outlook: a quote from {k} sits in a sentence that does not cite it")
            seen[k or ""] = seen.get(k or "", 0) + 1
    errors += [f"outlook: source {k} is quoted more than once" for k, n in seen.items() if k and n > 1]
    return errors


def _numbered(sources: list[dict[str, Any]], essay: str) -> list[dict[str, Any]]:
    """Sources numbered in the order the essay first cites them, then the rest in ledger order."""
    first = list(dict.fromkeys(v for k, v in TOKEN.findall(essay) if k == "cite"))
    order = sorted(sources, key=lambda x: first.index(x["id"]) if x["id"] in first else len(first))
    return [{**x, "n": n} for n, x in enumerate(order, 1)]


def _thresholds(
    s: Any, spec: dict[str, Any], f: dict[str, dict[str, Any] | None]
) -> dict[str, dict[str, Any]]:
    """The number each [test:] token prints: a claim's threshold, in its fact's unit."""
    out = {}
    for c in spec.get("claims") or []:
        t = c.get("test") or {}
        rhs = next((v for k, v in t.items() if k in OPS), None)
        if isinstance(rhs, str) or rhs is None:
            continue
        fact = f.get(t["fact"]) or {}
        unit = fact.get("unit") or (s.metric_spec(spec["facts"][t["fact"]].get("metric", "")) or {}).get(
            "unit"
        )
        if unit:
            out[c["id"]] = {"line": rhs, "unit": unit}
    return out


def build(s: Any, today: date | None = None) -> dict[str, Any]:
    spec = load()
    if not spec:
        return {}
    today = today or date.today()
    f = facts(s, spec, today)
    cl = claims(spec, f, today)
    essay = ESSAY.read_text() if ESSAY.exists() else ""
    return {
        "as_of": min(
            max((x["as_of"] for x in f.values() if x and x["as_of"]), default=today.isoformat()),
            today.isoformat(),
        ),
        "essay": essay,
        "facts": f,
        "sources": _numbered(spec["sources"], essay),
        "tests": _thresholds(s, spec, f),
        "folios": [
            {"id": k, "kicker": m}
            for k, m in zip(FOLIOS, re.findall(r"^### Folio [IVX]+ · (.+)$", essay, re.M))
        ],
        "positions": spec["positions"],
        "claims": cl,
        "tally": {k: sum(1 for c in cl if c["state"] == k) for k in STATES},
        "scenarios": scenarios(spec, cl),
        "agree": spec.get("agree") or [],
    }


def source_problems(sources: list[dict[str, Any]], where: str) -> list[str]:
    """A cited work needs its credits and a fetch record, and may carry one quote of under fifteen words."""
    errors = []
    for x in sources:
        for k in ("who", "field", "finding", "work", "year", "url"):
            if not x.get(k):
                errors.append(f"{where}: source {x['id']} has no {k}")
        if bad := unfetched(x):
            errors.append(f"{where}: source {x['id']} {bad}")
        q = x.get("quote")
        if q and len(q.split()) >= 15:
            errors.append(f"{where}: source {x['id']} quotes fifteen words or more")
    return errors


def problems(
    spec: dict[str, Any], known_facts: dict[str, Any], rows: set[str], stages: set[str]
) -> list[str]:
    """Errors for a ledger that cannot resolve: CI catches them before a page names a claim it cannot test."""
    if not spec:
        return []
    errors = []
    sources = {x["id"] for x in spec.get("sources") or []}
    positions = {p["id"]: p for p in spec.get("positions") or []}
    errors += source_problems(spec.get("sources") or [], "outlook")
    for p in positions.values():
        where = f"outlook: position {p['id']}"
        if p.get("folio") not in FOLIOS:
            errors.append(f"{where} names an unknown folio")
        if p.get("attribution") not in ATTRIBUTIONS:
            errors.append(f"{where} needs an attribution of author, extension or site")
        errors += [f"{where} names unknown source {h}" for h in p.get("holders") or [] if h not in sources]
        if p.get("attribution") in ("author", "extension") and not p.get("holders"):
            errors.append(f"{where} is credited to an author but names none")
        if p.get("attribution") == "site" and p.get("holders"):
            errors.append(f"{where} is marked as this site's own but names holders")
        if p.get("rival") not in positions:
            errors.append(f"{where} has no rival position")
    for c in spec.get("claims") or []:
        where = f"outlook: claim {c['id']}"
        if c.get("position") not in positions:
            errors.append(f"{where} names an unknown position")
        errors += [f"{where} names unknown source {h}" for h in c.get("holders") or [] if h not in sources]
        if c.get("attribution") and c["attribution"] not in ATTRIBUTIONS:
            errors.append(f"{where} has an unknown attribution")
        if c.get("attribution") == "site" and c.get("holders"):
            errors.append(f"{where} is this site's own reading but names holders")
        if c.get("row") and c["row"] not in rows:
            errors.append(f"{where} names an unknown map row {c['row']}")
        if c.get("stage") and c["stage"] not in stages:
            errors.append(f"{where} names an unknown stage {c['stage']}")
        if c.get("stage") and not c.get("row"):
            errors.append(f"{where} names a stage but no map row, so the map cannot mark it")
        for key in ("test", "rival_test"):
            t = c.get(key)
            if t and t.get("fact") not in known_facts:
                errors.append(f"{where}: {key} reads unknown fact {t.get('fact')}")
            elif t and (bad := _bad_test({k: v for k, v in t.items() if k != "fact"}, known_facts)):
                errors.append(f"{where}: {key} {bad}")
        if not c.get("test") and not c.get("falsifier"):
            errors.append(f"{where} has neither a test nor the outcome that would prove it wrong")
        if c.get("test") and c.get("expect_state") not in STATES:
            errors.append(f"{where} has a test but no expect_state for the sentence the page was written for")
        for key in ("due", "rival_until"):
            try:
                _on(c[key]) if c.get(key) else None
            except ValueError:
                errors.append(f"{where}: {key} is not a date")
        if c.get("rival_until") and not c.get("rival_test"):
            errors.append(f"{where} has rival_until but no rival_test")
        if c.get("expect_state") and c["expect_state"] not in STATES:
            errors.append(f"{where} expects an unknown state")
    claim_ids = {c["id"] for c in spec.get("claims") or []}
    sc = spec.get("scenarios") or {}
    axes = {a: {x["id"] for x in sc.get(a) or []} for a in ("progress", "rules")}
    for c in sc.get("cells") or []:
        where = f"outlook: scenario {c.get('progress')} x {c.get('rules')}"
        if c.get("progress") not in axes["progress"] or c.get("rules") not in axes["rules"]:
            errors.append(f"{where} names an unknown row or column")
        if not c.get("argued_by"):
            errors.append(f"{where} is filled but names nobody who argues it")
        errors += [f"{where} names unknown source {h}" for h in c.get("argued_by") or [] if h not in sources]
        errors += [f"{where} reads unknown claim {k}" for k in c.get("signposts") or [] if k not in claim_ids]
        errors += [
            f"{where} names an unknown map row {r}" for r in c.get("binds_next") or [] if r not in rows
        ]
    for a in sc.get("anchors") or []:
        if a.get("source") not in sources or not a.get("date"):
            errors.append(f"outlook: anchor {a.get('text', '')[:30]} needs a known source and a date")
    for a in spec.get("agree") or []:
        errors += [
            f"outlook: agreement {a.get('id')} names unknown source {h}"
            for h in [*(a.get("holders") or []), *(a.get("dissent") or [])]
            if h not in sources
        ]
    return errors


def check(s: Any) -> tuple[list[str], list[str]]:
    """Errors for a ledger or essay that cannot resolve (CI catches them); attention for sentences tonight's data
    stopped backing, so one feed's outage never freezes the nightly."""
    spec = load()
    if not spec:
        return [], []
    from .bottleneck_map import load as load_map

    m = load_map()
    rows = (
        {r["input"] for r in m["chain"]}
        | {r["id"] for r in m["nber"]}
        | {f"family_{k}" for k in range(len(m["families"]))}
    )
    errors = problems(spec, spec["facts"], rows, {x["id"] for x in m["stages"]})
    ids = {i.id for i in s.seed.indicators}
    for k, v in spec["facts"].items():
        if "indicator" in v and v["indicator"] not in ids or "metric" in v and not s.metric_spec(v["metric"]):
            errors.append(f"outlook: fact {k} names an unknown indicator or metric")
        if "series" in v and not s.con.execute(
            "SELECT 1 FROM observations WHERE series_key = ? LIMIT 1", [v["series"]]
        ).fetchone():
            errors.append(f"outlook: fact {k} names a series with no observations")
    errors += essay_problems(ESSAY.read_text() if ESSAY.exists() else "", spec)
    if errors:
        return errors, []
    f = facts(s, spec)
    notes = [f"outlook: fact {k} has no reading" for k, v in f.items() if v is None]
    notes += [
        f"outlook: fact {k} no longer reads as the essay says; rewrite the sentence"
        for k, v in f.items()
        if v and v.get("holds") is False
    ]
    notes += [f"outlook: fact {k} is past its age limit" for k, v in f.items() if v and v.get("stale")]
    for c in claims(spec, f):
        if not c["expected"] or c["state"] == c["expected"]:
            continue
        stale = (f.get(c["fact"]) or {}).get("stale") if c["fact"] else False
        notes.append(
            f"outlook: claim {c['id']} cannot be tested while fact {c['fact']} is past its age limit"
            if stale
            else f"outlook: claim {c['id']} reads {c['state']}; the page was written for {c['expected']}, so rewrite the sentence"
        )
    return errors, notes


__all__ = [
    "OPS",
    "PLATES",
    "STATES",
    "build",
    "check",
    "claims",
    "essay_problems",
    "load",
    "problems",
    "scenarios",
    "state",
    "strings",
]
