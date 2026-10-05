"""Who owns what (/firm): an essay on the firm, argued from the outlook's ledger. Every claim, fact and source on the
page is an outlook record, tested by the outlook's own code; seed/firm.yaml only seats positions under the essay's
folios, holds the rent-or-own table, and names the claims on which the essay says the board's leans disagree with it.

Pure functions over the seed and the built outlook; nothing here reads the store."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .argument import essay_shape
from .outlook import STATES, TOKEN, _numbered, essay_problems

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "firm.yaml"
ESSAY = ROOT / "docs" / "argument" / "firm.md"
PLATES = ("regimes", "shapes", "jobs")
AGAINST = ("leans_false", "likely_false")
FIGURE = re.compile(r"\d")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text()) if SPEC.exists() else {}


def strings(spec: dict[str, Any]) -> list[str]:
    """The page's own words outside the essay, for the tests that keep figures out."""
    r, sh, fi = spec.get("regimes") or {}, spec.get("shapes") or {}, spec.get("fiction") or {}
    shapes = [row.get(k, "") for row in sh.get("rows") or [] for k in ("shape", "who", "goes_first", "stays", "would_show")]
    fiction = [w.get(k, "") for w in fi.get("works") or [] for k in ("author", "title", "shape", "picture")]
    plates = [sh.get("title", ""), sh.get("note", ""), *shapes, fi.get("label", ""), fi.get("note", ""), *fiction]
    return [r.get("title", ""), r.get("note", ""), *(r.get("columns") or []), *(c for row in r.get("rows") or [] for c in row), *plates]


def _folio_words(essay: str) -> set[str]:
    """Each folio's anchor word, as the page makes it: "Folio II · the leak" is seated as `leak`."""
    return {re.sub(r"^the ", "", m).strip().lower() for m in re.findall(r"^### Folio [IVX]+ · (.+)$", essay, re.M)}


def _seated(spec: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys(p for ids in (spec.get("folios") or {}).values() for p in ids))


def problems(spec: dict[str, Any], outlook: dict[str, Any], leans: dict[str, Any], essay: str) -> list[str]:
    if not spec:
        return []
    errors = [f"firm: essay {e}" for e in essay_shape(essay)]
    errors += [e.replace("outlook:", "firm:") for e in essay_problems(essay, outlook, PLATES)]
    known = {p["id"] for p in outlook.get("positions") or []}
    words = _folio_words(essay)
    for folio, ids in (spec.get("folios") or {}).items():
        if folio not in words:
            errors.append(f"firm: folio {folio} is not in the essay")
        errors += [f"firm: folio {folio} seats unknown position {p}" for p in ids if p not in known]
    lean = {j["id"]: j["lean"] for j in leans.get("judgements") or [] if j.get("kind") == "outlook"}
    for c in spec.get("leans_against") or []:
        if c not in lean:
            errors.append(f"firm: claim {c} has no lean on the board, but the essay says the board leans against it")
        elif lean[c] not in AGAINST:
            errors.append(f"firm: claim {c} no longer leans against on the board; rewrite the essay's sentence")
    r = spec.get("regimes") or {}
    for i, row in enumerate(r.get("rows") or []):
        if len(row) != len(r.get("columns") or []):
            errors.append(f"firm: regimes row {i} does not fill every column")
    sources = {x["id"] for x in outlook.get("sources") or []}
    for row in (spec.get("shapes") or {}).get("rows") or []:
        if not row.get("sources"):
            errors.append(f"firm: shape '{row.get('shape')}' credits no source")
        errors += [f"firm: shape '{row.get('shape')}' names unknown source {x}" for x in row.get("sources") or [] if x not in sources]
    if spec.get("fiction") and "not evidence" not in spec["fiction"].get("label", ""):
        errors.append("firm: the fiction lane must be labelled as not evidence")
    errors += [f"firm: the page types a figure: {t[:40]}" for t in strings(spec) if FIGURE.search(t)]
    return errors


def build(spec: dict[str, Any], outlook: dict[str, Any], essay: str, census_cut: dict[str, Any] | None = None) -> dict[str, Any]:
    """The outlook's records this page argues from, cut down to its own positions, with sources numbered in the order
    this essay cites them."""
    if not spec or not outlook:
        return {}
    seated = _seated(spec)
    by_id = {p["id"]: p for p in outlook["positions"]}
    positions = [by_id[p] for p in seated if p in by_id]
    claims = [c for c in outlook["claims"] if c["position"] in seated]
    text = " ".join([essay, *(p.get(k) or "" for p in positions for k in ("mechanism", "case")), *(c.get("text") or "" for c in claims)])
    facts = {v for k, v in TOKEN.findall(text) if k == "fact"}
    for c in claims:
        for t in (c.get("test"), c.get("rival_test")):
            facts |= {v for v in (t or {}).values() if isinstance(v, str)}
    cited = {v for k, v in TOKEN.findall(text) if k == "cite"} | {h for x in [*positions, *claims] for h in x.get("holders") or []}
    cited |= {x for row in (spec.get("shapes") or {}).get("rows") or [] for x in row.get("sources") or []}
    return {
        "as_of": outlook["as_of"],
        "essay": essay,
        "facts": {k: v for k, v in outlook["facts"].items() if k in facts},
        "tests": {k: v for k, v in outlook["tests"].items() if k in {c["id"] for c in claims}},
        "sources": _numbered([{k: v for k, v in x.items() if k != "n"} for x in outlook["sources"] if x["id"] in cited], essay),
        "positions": positions,
        "claims": claims,
        "tally": {k: sum(1 for c in claims if c["state"] == k) for k in STATES},
        "folios": spec.get("folios") or {},
        "regimes": spec.get("regimes") or {},
        "shapes": spec.get("shapes") or {},
        "fiction": spec.get("fiction") or {},
        "census_cut": census_cut or {},
    }
