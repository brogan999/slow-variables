"""Futures (plan Part 20): imagined and forecast technologies by decade, each with a rent rubric. The rows come from
Technovelgy's glossary of science-fiction inventions as compiled by Not Boring, and from the singularity canon.
Models answer only the rubric's inputs (seed/futures/rubric.yaml); where the rent pools and its tier are derived
here by fixed rules, and dates are normalised by fixed rules, never judged."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
RUBRIC = ROOT / "seed" / "futures" / "rubric.yaml"


def rubric() -> dict[str, Any]:
    return yaml.safe_load(RUBRIC.read_text())


def when(text: str | float | None) -> dict[str, Any]:
    """A date as the sheet gives it. An exact year stays a year, a named decade ("1960s") stays a decade, anything
    coarser or vaguer is unclear, never a midpoint."""
    s = str(text or "").strip()
    if m := re.fullmatch(r"(1[0-9]{3}|20[0-9]{2})(?:\.0)?", s):
        y = int(m[1])
        return {"kind": "year", "year": y, "decade": y // 10 * 10}
    if m := re.fullmatch(r"(1[0-9]{2}|20[0-9])0s", s):
        return {"kind": "decade", "year": None, "decade": int(m[1]) * 10}
    return {"kind": "unclear", "year": None, "decade": None}


def arrival(imagined: int, built: str | None, made: str | None) -> dict[str, Any]:
    """Whether and when a sheet row arrived, as the sheet marks it. A real thing that came before the story is
    'already existed', kept out of arrival counts and lags."""
    if (built or "").strip().lower() != "yes":
        return {"state": "not_marked_built"}
    w = when(made)
    if w["kind"] == "unclear":
        return {"state": "marked_built_date_unclear"}
    first = w["year"] if w["kind"] == "year" else w["decade"]
    if first < imagined // 10 * 10 or (w["kind"] == "year" and first < imagined):
        return {"state": "already_existed", **w}
    out = {"state": "marked_built", **w}
    if w["kind"] == "year":
        out["lag_years"] = w["year"] - imagined
    else:
        out["lag_decades"] = (w["decade"] - imagined // 10 * 10) // 10
    return out


def pools(answers: dict[str, str], spec: dict[str, Any] | None = None) -> str:
    """Where the rent pools (after Teece): the first rule whose conditions the answers meet."""
    for r in (spec or rubric())["pools"]["rules"]:
        if all(answers.get(k) == v for k, v in r["when"].items()):
            return answers["asset_owner"] if r["pools"] == "asset_owner" else r["pools"]
    raise ValueError("no pools rule matched")  # the last rule has no conditions, so this cannot happen


def tier(answers: dict[str, str], spec: dict[str, Any] | None = None) -> str:
    """How large the rent is where it pools: rent kind by durability, and none when it is competed away."""
    spec = spec or rubric()
    if pools(answers, spec) == "users":
        return "none"
    return spec["tiers"]["rules"][answers["rent_kind"]][answers["durability"]]


def problems(spec: dict[str, Any]) -> list[str]:
    """The rubric must be total: every rent kind has a tier for every durability, and every tier is a known word."""
    errors = []
    words = set(spec["tiers"]["words"])
    for kind in spec["inputs"]["rent_kind"]:
        row = spec["tiers"]["rules"].get(kind) or {}
        for d in spec["inputs"]["durability"]:
            if row.get(d) not in words:
                errors.append(f"futures rubric: {kind} x {d} has no known tier")
    if spec["pools"]["rules"][-1]["when"]:
        errors.append("futures rubric: the last pools rule must match everything")
    return errors
