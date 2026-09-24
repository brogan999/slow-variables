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


CATEGORY_NAMES = {
    "space": "Space travel and habitats", "computing_ai": "Computing, AI and virtual worlds",
    "communication_media": "Communication, media and displays", "robotics_automation": "Robotics and automation",
    "medicine_biotech": "Medicine, biotech and longevity", "mind_neurotech": "Mind and neurotechnology",
    "transport": "Transport and mobility", "energy": "Energy and power",
    "materials_manufacturing": "Materials, manufacturing and construction", "weapons_warfare": "Weapons and warfare",
    "surveillance_identity": "Surveillance, identity and control", "food_environment": "Food, agriculture and environment",
    "home_everyday": "Home and everyday life", "exotic_physics": "Exotic physics", "society_economy": "Society and economy",
}
TIER_WORDS = {"none": "competed away", "thin": "thin", "moderate": "moderate", "fat": "fat", "monopoly_like": "monopoly-like"}
POOLS_WORDS = {"innovator": "the maker", "incumbents": "incumbent firms", "platforms": "platforms",
               "regulators_licensees": "licence holders", "users": "users (competed away)"}
EARLY = 1850  # everything imagined before this decade shares one bucket
IMAGES = ROOT / "seed" / "futures" / "images.yaml"
CREDITS = ROOT / "seed" / "futures" / "credits.yaml"


def imagined_key(year: int) -> str:
    return "before-1850" if year < EARLY else f"{year // 10 * 10}s"


def _arrival(a: dict[str, Any]) -> str:
    when = str(a.get("year") or f"the {a['decade']}s" if a.get("decade") else "")
    if a["state"] == "marked_built":
        lag = f"{a['lag_years']} years after" if "lag_years" in a else f"{a['lag_decades']} decades after"
        return f"arrived {when}, {lag}"
    return {"already_existed": f"already existed ({when})", "marked_built_date_unclear": "arrived, date unclear",
            "not_marked_built": "not yet built"}[a["state"]]


def _when(w: dict[str, Any]) -> str:
    k = w["kind"]
    if k == "year":
        return str(w["year"])
    if k == "by":
        return f"by {w['year']}"
    if k == "decade":
        return f"the {w['low']}s"
    return f"{w['low']} to {w['high']}" if w.get("high") else f"from {w['low']}"


def expected_key(r: dict[str, Any]) -> str:
    """The decade a forecast or an unbuilt idea is expected in; for a stated range, its first year."""
    if "when" in r:
        y = r["when"].get("year") or r["when"]["low"]
        return "after-2100" if y > 2100 else f"{y // 10 * 10}s"
    d = r["arrival_decade"]
    return {"after_2100": "after-2100", "not_physically_possible": "impossible", "cannot_judge": "cannot-judge"}.get(d, d)


EXPECTED_LABELS = {"after-2100": "after 2100", "impossible": "not physically possible", "cannot-judge": "cannot judge"}


def build() -> dict[str, Any]:
    """web/data/futures/: counts and bar widths for the two decade strips, and one document per decade and category.
    The web renders; every count, share and label is decided here."""
    every, fcs = ideas(), forecasts()
    if not every:
        return {}
    imgs = {x["stem"]: x for x in (yaml.safe_load(IMAGES.read_text()) or {}).get("images", [])} if IMAGES.exists() else {}
    imgs = {k: x for k, x in imgs.items() if not x.get("withheld")}  # failed review: the category image stands in
    by_idea = {x["idea"]: f"/futures/{x['stem']}" for x in imgs.values() if x.get("idea")}
    works = {s["id"]: s for s in canon_sources()}

    def card(x: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": x["id"], "name": x["name"], "work": x["work"], "author": x["author"], "imagined": x["imagined"],
            "line": x["line"], "category": x["category"], "arrival": _arrival(x["arrival"]),
            "built": x["arrival"]["state"] != "not_marked_built",
            "expected": EXPECTED_LABELS.get(expected_key(x), expected_key(x)) if x["arrival"]["state"] == "not_marked_built" else None,
            "tier": TIER_WORDS.get(x["tier"]) if x["tier"] else None, "pools": POOLS_WORDS.get(x["pools"]) if x["pools"] else None,
            "image": by_idea.get(x["id"]), "shortlist": x["shortlist"],
        }

    def forecast(f: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": f["id"], "who": f["who"], "technology": f["technology"], "line": f["line"], "category": f["category"],
            "when": _when(f["when"]), "odds": f["odds"], "quote": f["quote"],
            "ledger": f"/predictions#{f['ledger_id']}" if f["ledger_id"] else None,
            "works": [{"title": works[w]["title"], "author": works[w]["author"], "year": works[w]["year"], "url": works[w].get("url")} for w in f["works"]],
        }

    def grouped(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for cid, name in CATEGORY_NAMES.items():
            rs = sorted((card(x) for x in rows if x["category"] == cid), key=lambda c: (c["imagined"], c["name"]))
            if rs:
                out.append({"id": cid, "name": name, "n": len(rs), "ideas": rs})
        rest = sorted((card(x) for x in rows if x["category"] not in CATEGORY_NAMES), key=lambda c: (c["imagined"], c["name"]))
        if rest:  # the models could not place these
            out.append({"id": "unclassified", "name": "Not classified", "n": len(rest), "ideas": rest})
        return out

    imagined_keys = ["before-1850"] + [f"{d}s" for d in range(EARLY, 2030, 10)]
    peak = max(sum(1 for x in every if imagined_key(x["imagined"]) == k) for k in imagined_keys)
    imagined, decade_docs = [], {}
    for k in imagined_keys:
        rows = [x for x in every if imagined_key(x["imagined"]) == k]
        built = sum(1 for x in rows if x["arrival"]["state"] != "not_marked_built")
        label = "before 1850" if k == "before-1850" else k
        imagined.append({"key": k, "label": label, "n": len(rows), "built": built, "width": round(100 * len(rows) / peak, 1),
                         "built_width": round(100 * built / peak, 1), "href": f"/futures/imagined/{k}" if rows else None})
        if rows:
            decade_docs[f"imagined/{k}"] = {"kind": "imagined", "key": k, "label": label, "n": len(rows), "built": built, "groups": grouped(rows)}

    unbuilt = [x for x in every if x["arrival"]["state"] == "not_marked_built"]
    keys = sorted({expected_key(x) for x in unbuilt} | {expected_key(f) for f in fcs}, key=lambda k: (k in EXPECTED_LABELS, k))
    judged = {k: [x for x in unbuilt if expected_key(x) == k] for k in keys}
    stated = {k: [f for f in fcs if expected_key(f) == k] for k in keys}
    peak_e = max(max(len(v) for v in judged.values()), max(len(v) for v in stated.values()))
    expected = []
    for k in keys:
        label = EXPECTED_LABELS.get(k, k)
        if k[:4].isdigit() and int(k[:4]) < 2020:
            label += ", passed"
        expected.append({"key": k, "label": label, "judged": len(judged[k]), "stated": len(stated[k]),
                         "judged_width": round(100 * len(judged[k]) / peak_e, 1), "stated_width": round(100 * len(stated[k]) / peak_e, 1),
                         "href": f"/futures/expected/{k}"})
        decade_docs[f"expected/{k}"] = {"kind": "expected", "key": k, "label": label, "judged": len(judged[k]),
                                        "stated": len(stated[k]), "groups": grouped(judged[k]),
                                        "forecasts": sorted((forecast(f) for f in stated[k]), key=lambda f: (f["when"], f["who"]))}

    categories, category_docs = [], {}
    for cid, name in CATEGORY_NAMES.items():
        rows = [x for x in every if x["category"] == cid]
        tiers = {w: sum(1 for x in rows if TIER_WORDS.get(x["tier"]) == w) for w in TIER_WORDS.values()}
        tiers["no rent result"] = sum(1 for x in rows if not x["tier"])
        img = f"/futures/cat-{cid}" if f"cat-{cid}" in imgs else None
        categories.append({"id": cid, "name": name, "n": len(rows), "built": sum(1 for x in rows if x["arrival"]["state"] != "not_marked_built"),
                           "tiers": tiers, "image": img, "href": f"/futures/category/{cid}"})
        category_docs[cid] = {"id": cid, "name": name, "image": img, "n": len(rows), "tiers": tiers,
                              "ideas": sorted((card(x) for x in rows), key=lambda c: (c["imagined"], c["name"])),
                              "forecasts": sorted((forecast(f) for f in fcs if f["category"] == cid), key=lambda f: (f["when"], f["who"]))}
    featured = [card(x) for x in sorted(every, key=lambda x: x["imagined"]) if x["shortlist"] and by_idea.get(x["id"])]
    return {
        "index": {"n_ideas": len(every), "n_forecasts": len(fcs), "n_images": len(imgs), "n_shortlist": sum(x["shortlist"] for x in every),
                  "imagined": imagined, "expected": expected, "categories": categories, "featured": featured,
                  "tier_words": list(TIER_WORDS.values()) + ["no rent result"],
                  "credits": [{"name": c["name"], "url": c["url"]} for c in (yaml.safe_load(CREDITS.read_text()) or {}).get("credits", [])] if CREDITS.exists() else []},
        "decades": decade_docs,
        "categories": category_docs,
    }
