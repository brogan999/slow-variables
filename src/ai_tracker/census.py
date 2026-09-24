"""The Automatability Census (plan Part 21): a snapshot bundle built in a separate project and imported as published.

The site never recomputes a verdict, share or band. It checks the bundle against its own manifest, loads its tables for
SQL, and writes web/data/census/ by selecting, sorting and joining. Every "can go" figure travels with the part all
three scorers agree on (`agreed3`); where a version of the bundle does not report it, the field is None and the page
says so rather than printing a zero."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from .argument import unfetched

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "seed" / "census.yaml"
FETCHES = ROOT / "seed" / "census_fetches.yaml"
DATA = ROOT / "data" / "census"
TABLES = {
    "census_tasks": "tasks.csv",
    "census_roles": "roles.csv",
    "census_role_industry": "role_industry.csv",
    "census_industries": "industries.csv",
    "census_functions": "functions.csv",
}
TEXT_COLUMNS = {"occ", "naics", "occ_title", "naics_title", "title", "function", "task", "why"}
METHOD = ["gates", "adjudication", "placebo", "stability", "channel", "sigma"]  # sigma is modelled; shown only here


def load() -> dict[str, Any]:
    spec = yaml.safe_load(SEED.read_text()) if SEED.exists() else {}
    if spec:
        spec["version"] = str(spec["version"])  # YAML reads an unquoted date as a date
    return spec


def fetches() -> dict[str, Any]:
    return yaml.safe_load(FETCHES.read_text()) if FETCHES.exists() else {}


def bundle(spec: dict[str, Any]) -> Path:
    return DATA / str(spec["version"])


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def num(x: str | None) -> float | None:
    return float(x) if x not in (None, "") else None


def truth(x: str) -> bool:
    return x == "True"


def problems(spec: dict[str, Any], fetched: dict[str, Any]) -> list[str]:
    """The bundle is the one its manifest describes, every table sums to the headline, and every source link was
    fetched."""
    if not spec:
        return []
    d = bundle(spec)
    if not (d / "manifest.json").exists():
        return [f"census: version {spec['version']} is not in data/census/"]
    errors = []
    m = json.loads((d / "manifest.json").read_text())
    for name, meta in m["files"].items():
        p = d / name
        if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest() != meta["sha256"]:
            errors.append(f"census: {name} does not match the manifest")
        elif meta["rows"] is not None and len(rows(p)) != meta["rows"]:
            errors.append(f"census: {name} has the wrong number of rows")
    if errors:
        return errors
    head = m["headline"]["freed_usd"]
    sums = {"tasks.csv": sum(num(r["task_payroll_usd"]) or 0 for r in rows(d / "tasks.csv") if truth(r["goes"]))}
    sums |= {f: sum(num(r["freed"]) or 0 for r in rows(d / f)) for f in TABLES.values() if f != "tasks.csv"}
    errors += [f"census: {f} sums to {v:.0f}, not the headline" for f, v in sums.items() if abs(v - head) > 1]
    cited = {x["cited_as"]: x for x in fetched.get("fetches") or []}
    for card in json.loads((d / "deal_sheets.json").read_text())["cards"]:
        for u in card["sources"]:
            why = unfetched(cited[u]) if u in cited else "has no fetch record"
            if why:
                errors.append(f"census: deal-sheet source {u} {why}")
    return errors


def create_tables(con: Any, spec: dict[str, Any]) -> None:
    """Load the pinned version's CSVs into `con` as the census_* tables, codes and names typed as text."""
    d = bundle(spec)
    for table, name in TABLES.items():
        with (d / name).open(newline="") as f:
            header = next(csv.reader(f))
        types = {c: "VARCHAR" for c in header if c in TEXT_COLUMNS}
        con.execute(
            f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv(?, header = true, types = {types!r})",
            [str(d / name)],
        )


def build_headline(spec: dict[str, Any]) -> dict[str, float]:
    """The manifest's headline figures, for citing as [census:headline]."""
    if not spec or not (bundle(spec) / "manifest.json").exists():
        return {}
    return json.loads((bundle(spec) / "manifest.json").read_text())["headline"]


def ref(spec: dict[str, Any], file: str, key: str) -> str:
    return f"census:{spec['version']}/{file}#{key}"


def build(spec: dict[str, Any], fetched: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """index.json and one document per role. Selects, sorts and joins; computes no share, band or verdict."""
    if not spec:
        return {}, {}
    d = bundle(spec)
    v = spec["version"]
    m = json.loads((d / "manifest.json").read_text())
    val = json.loads((d / "validation.json").read_text())
    deals = json.loads((d / "deal_sheets.json").read_text())
    tasks = rows(d / "tasks.csv")
    by_occ: dict[str, list[dict[str, str]]] = {}
    for t in tasks:
        by_occ.setdefault(t["occ"], []).append(t)
    staffing: dict[str, list[dict[str, str]]] = {}
    for r in rows(d / "role_industry.csv"):
        staffing.setdefault(r["occ"], []).append(r)
    links = {x["cited_as"]: x["url"] for x in fetched.get("fetches") or []}
    csv_href = lambda f: f"/data/census/{v}/{f}"  # noqa: E731

    roles = []
    docs = {}
    for r in rows(d / "roles.csv"):
        scored3 = any(t["n_scorers"] == "3" for t in by_occ.get(r["occ"], []))
        role = {
            "occ": r["occ"],
            "title": r["title"],
            "function": r["function"],
            "href": f"/census/roles/{r['occ']}",
            "ref": ref(spec, "roles.csv", r["occ"]),
            "emp": num(r["emp"]),
            "wage_bill": num(r["wage_bill"]),
            "share_goes": num(r["share_goes"]),
            "band_lo": num(r["band_lo"]),
            "band_hi": num(r["band_hi"]),
            "freed": num(r["freed"]),
            "agreed3": num(r["freed_agreed3"]) if scored3 else None,
            "scored_by_three": scored3,
            "contested": num(r["freed_contested"]),
            "ai_exposure": num(r["ai_exposure"]),
        }
        roles.append(role)
        ts = sorted(by_occ.get(r["occ"], []), key=lambda t: (-(num(t["time_share"]) or 0), t["task_id"]))
        docs[r["occ"]] = {
            "version": v,
            "role": role,
            "tasks": [
                {
                    "id": t["task_id"],
                    "ref": ref(spec, "tasks.csv", t["task_id"]),
                    "task": t["task"],
                    "goes": truth(t["goes"]),
                    "why": t["why"],
                    "physical": truth(t["physical"]),
                    "contested": truth(t["contested"]),
                    "agreed_all_three": truth(t["agreed_all_three"]),
                    "blocked_by_verifier": truth(t["blocked_by_verifier"]),
                    "n_scorers": int(t["n_scorers"]),
                    "time_share": num(t["time_share"]),
                    "payroll": num(t["task_payroll_usd"]),
                }
                for t in ts
            ],
            "industries": [
                {"naics": x["naics"], "title": x["naics_title"], "emp": num(x["emp"]), "wage_bill": num(x["wage_bill"]), "freed": num(x["freed"]), "agreed3": num(x.get("agreed3"))}
                for x in sorted(staffing.get(r["occ"], []), key=lambda x: (-(num(x["wage_bill"]) or 0), x["naics"]))[:10]
            ],
            "csv": csv_href("tasks.csv"),
        }
    roles.sort(key=lambda x: (x["function"], -(x["freed"] or 0), x["occ"]))

    h = m["headline"]
    index = {
        "version": v,
        "generated_at": m["generated_at"],
        "manifest_sha256": hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest(),
        "sources": m["sources"],
        "scorers": spec["scorers"],
        "prose": {k: spec[k] for k in ("title", "lede", "rule", "agreed", "sections", "caveats")},
        "headline": {
            "freed": h["freed_usd"],
            "agreed3": h["agreed_all_three_usd"],
            "payroll": h["knowledge_payroll_usd"],
            "agreed": h["agreed_usd"],
            "contested": h["contested_usd"],
            "verifier_queue": h["verifier_queue_usd"],
            "without_gemini": h["decided_without_gemini_usd"],
            "physical_removed": h["physical_removed_usd"],
            "ref": ref(spec, "manifest.json", "headline"),
        },
        "dial": [
            {"rule": x["rule"], "freed": x["freed"], "agreed3": x.get("agreed3"), "headline": x["headline"]}
            for x in val["dial"]
        ],
        "functions": sorted(
            (
                {
                    "function": r["function"],
                    "ref": ref(spec, "functions.csv", r["function"]),
                    "payroll": num(r["payroll"]),
                    "freed": num(r["freed"]),
                    "agreed3": num(r.get("agreed3")),
                    "share_goes": num(r["share_goes"]),
                    "band_lo": num(r["lo"]),
                    "band_hi": num(r["hi"]),
                    "verifier_queue": num(r["blocked_by_verifier_usd"]),
                    "roles": int(r["roles"]),
                }
                for r in rows(d / "functions.csv")
            ),
            key=lambda x: (-(x["freed"] or 0), x["function"]),
        ),
        "industries": sorted(
            (
                {
                    "naics": r["naics"],
                    "title": r["naics_title"],
                    "ref": ref(spec, "industries.csv", r["naics"]),
                    "payroll": num(r["total"]),
                    "knowledge_payroll": num(r["know"]),
                    "freed": num(r["freed"]),
                    "agreed3": num(r["agreed3"]),
                    "verifier_queue": num(r["blocked"]),
                    "share_total": num(r["share_total"]),
                }
                for r in rows(d / "industries.csv")
            ),
            key=lambda x: (-(x["freed"] or 0), x["naics"]),
        ),
        "roles": roles,
        "deals": {
            "cards": [
                {
                    **{k: c[k] for k in ("key", "name", "naics", "invoice", "why", "kill", "comps", "scope", "excl", "anchored", "stance", "stance_why")},
                    "sources": [{"cited_as": u, "href": links.get(u, u)} for u in c["sources"]],
                    "payroll": c["ind_payroll"],
                    "freed": c["freed"],
                    "freed_lo": c["freed_lo"],
                    "freed_hi": c["freed_hi"],
                    "agreed3": c.get("agreed3"),
                    "roles": [{"title": x["t"], "wage_bill": x["b"], "share_goes": x["g"], "freed": x["f"], "agreed3": x.get("agreed3")} for x in c["roles"]],
                }
                for c in deals["cards"]
            ],
            "not_carded": deals["not_carded"],
        },
        "method": {k: val[k] for k in METHOD},
        "csv": {f: csv_href(f) for f in (*TABLES.values(),)},
    }
    return index, docs


def strings(spec: dict[str, Any]) -> list[str]:
    """The site's own words on the census pages, for the text-rule tests."""
    if not spec:
        return []
    s = spec["sections"]
    return [spec["title"], spec["lede"], spec["rule"], spec["agreed"], *spec["caveats"], *(x[k] for x in s.values() for k in ("title", "lede"))]
