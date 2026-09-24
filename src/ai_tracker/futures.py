"""Futures (plan Part 20): imagined and forecast technologies by decade, each with a rent rubric. The rows come from
Technovelgy's glossary of science-fiction inventions as compiled by Not Boring, and from the singularity canon.
Models answer only the rubric's inputs (seed/futures/rubric.yaml); where the rent pools and its tier are derived
here by fixed rules, and dates are normalised by fixed rules, never judged."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
RUBRIC = ROOT / "seed" / "futures" / "rubric.yaml"
IDEAS = ROOT / "seed" / "futures" / "ideas.jsonl"
FIELDS = [
    "category",
    "rent_kind",
    "appropriability",
    "complementary_assets",
    "asset_owner",
    "durability",
    "arrival_decade",
    "needs",
]
VOTED = ["category", "arrival_decade", "needs"]  # three scorers, majority rule
RENT = [
    "rent_kind",
    "appropriability",
    "complementary_assets",
    "asset_owner",
    "durability",
]  # one scorer, pass two


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


def ideas() -> list[dict[str, Any]]:
    """The scored idea-bank rows (scripts/futures_seed.py), one per line, or none before the seed exists."""
    return [json.loads(line) for line in IDEAS.read_text().splitlines()] if IDEAS.exists() else []


def idea_problems(rows: list[dict[str, Any]], spec: dict[str, Any]) -> list[str]:
    """Every answer is a rubric word (or cannot_judge, or no_majority where three scorers voted); a voted answer is
    the majority of its votes unless an override gives the reason; where the rent pools and its tier are what the
    rules give; the site's lines type no digit."""
    errors: list[str] = []
    words = {
        **spec["inputs"],
        "category": spec["categories"],
        "arrival_decade": spec["arrival"]["decades"],
        "needs": spec["arrival"]["needs"],
    }
    seen: set[str] = set()
    for r in rows:
        rid = r["id"]
        if rid in seen:
            errors.append(f"futures: duplicate id {rid}")
        seen.add(rid)
        if not r.get("line") or re.search(r"\d", r["line"]):
            errors.append(f"futures: {rid} line missing or types a digit")
        if r.get("technology") not in ("yes", "no"):
            errors.append(f"futures: {rid} technology must be yes or no")
        if r.get("market") not in {None, *spec["market"]["words"]}:
            errors.append(f"futures: {rid} market {r.get('market')!r} is not a rubric word")
        unknown = [
            k
            for k in FIELDS
            if r[k] not in {*words[k], "cannot_judge", *(["no_majority"] if k in VOTED else [])}
        ]
        errors += [f"futures: {rid} {k} {r[k]!r} is not a rubric word" for k in unknown]
        overrides = r.get("overrides") or {}
        errors += [
            f"futures: {rid} override of {k} gives no reason" for k, why in overrides.items() if not why
        ]
        for k in VOTED:
            votes = r["votes"][k]
            if k in overrides:
                continue
            if k in (r.get("tiebreak") or []):
                ok = len(votes) == 3 and max(votes.count(v) for v in votes) < 2 and r[k] == votes[0]
            else:
                ok = len(votes) == 3 and (r[k] == "no_majority" or votes.count(r[k]) >= 2)
            if not ok:
                errors.append(f"futures: {rid} {k} is neither the majority of its votes nor a tiebreak")
        if not unknown and (r["pools"], r["tier"]) != judged(r, spec):
            errors.append(f"futures: {rid} pools or tier does not follow the rubric's rules")
    return errors


def judged(r: dict[str, Any], spec: dict[str, Any]) -> tuple[str | None, str | None]:
    """Where the rent pools and its tier from majority answers. A split or cannot_judge blocks a result only where
    the rule needs that answer; exotic physics, anything judged physically impossible, anything that is not a
    technology, and anything with no market of buyers (one_off, banned) get neither."""
    unknown = {"no_majority", "cannot_judge"}
    if (
        r.get("technology") == "no"
        or r.get("market") in ("one_off", "banned", "cannot_judge")
        or r["category"] == "exotic_physics"
        or r["arrival_decade"] == "not_physically_possible"
    ):
        return None, None
    need = ["appropriability"]
    if r["appropriability"] == "weak":
        need.append("complementary_assets")
        if r["complementary_assets"] == "specialised":
            need.append("asset_owner")
    if any(r[k] in unknown for k in need):
        return None, None
    where = pools(r, spec)
    if where == "users":
        return where, "none"
    if {r["rent_kind"], r["durability"]} & unknown:
        return where, None
    return where, tier(r, spec)


FORECASTS = ROOT / "seed" / "futures" / "forecasts.jsonl"
CANON = ROOT / "seed" / "futures" / "canon_sources.yaml"
NAMES = {"GPT-4"}  # a model's name, not a figure
WHEN_KINDS = {"year", "by", "range", "decade"}


def forecasts() -> list[dict[str, Any]]:
    """Dated technology forecasts from the singularity canon (scripts/futures_canon.py), reviewed against their sources."""
    return [json.loads(line) for line in FORECASTS.read_text().splitlines()] if FORECASTS.exists() else []


def canon_sources() -> list[dict[str, Any]]:
    return (yaml.safe_load(CANON.read_text()) or {}).get("sources", []) if CANON.exists() else []


def _stray_digits(text: str) -> list[str]:
    """Digits other than a year ("2027", "the 2030s", "mid-2040s") or a named model ("GPT-4's")."""
    words = [re.sub(r"(['’]s)?[.]?$", "", w) for w in re.findall(r"[^\s,;:()]*\d[^\s,;:()]*", text)]
    year = r"((early|mid|late)-)?(1[6-9]\d\d|2[0-2]\d\d)s?"
    return [w for w in words if w not in NAMES and not re.fullmatch(year, w)]


def forecast_problems(rows: list[dict[str, Any]], sources: list[dict[str, Any]], spec: dict[str, Any], ledger: set[str]) -> list[str]:
    """Each forecast names a known category and work, dates itself as stated, and its words follow the site's rules."""
    from .argument import unfetched

    errors: list[str] = []
    works = {s["id"]: s for s in sources}
    errors += [f"futures canon: source {s['id']} {why}" for s in sources if s.get("url") and (why := unfetched(s))]
    seen: set[str] = set()
    for r in rows:
        rid = r["id"]
        if rid in seen:
            errors.append(f"futures canon: duplicate id {rid}")
        seen.add(rid)
        if r["category"] not in spec["categories"]:
            errors.append(f"futures canon: {rid} category {r['category']!r} is not a rubric category")
        w = r["when"]
        dated = w.get("year") if w.get("kind") in ("year", "by") else w.get("low")
        if w.get("kind") not in WHEN_KINDS or not isinstance(dated, int):
            errors.append(f"futures canon: {rid} has no date as stated")
        if len(r["line"].split()) > 30 or _stray_digits(r["line"]) or _stray_digits(r.get("odds") or ""):
            errors.append(f"futures canon: {rid} line or odds breaks the text rules")
        if r.get("quote") and len(r["quote"].split()) >= 15:
            errors.append(f"futures canon: {rid} quote is fifteen words or more")
        errors += [f"futures canon: {rid} names unknown work {x}" for x in r["works"] if x not in works]
        if r.get("ledger_id") and r["ledger_id"] not in ledger:
            errors.append(f"futures canon: {rid} links unknown ledger entry {r['ledger_id']}")
    return errors
