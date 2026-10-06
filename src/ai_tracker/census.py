"""The Automatability Census (plan Part 21): a snapshot bundle built in a separate project and imported as published.

The site never recomputes a verdict or share. It checks the bundle against its own manifest, loads its tables for SQL,
and writes web/data/census/ by selecting, sorting and joining. A task "passes the structural hand-over screen" under the
census's rule; every "passes" figure travels with the part all three scorers pass (`agreed3`). Where none of a role's
or function's payroll was scored by all three, agreed3 is None and the page says so rather than printing a zero.
Modelled figures (the modelled saving, the substitution sigma) are exported only under keys that say so."""

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
TEXT_COLUMNS = {"occ", "naics", "occ_title", "naics_title", "title", "function", "task", "why", "time_share_basis", "split"}
# `why` phrases reworded: one is shorthand, one speaks of reach (capability); the rest read plainly as given.
PLAIN_WHY = {
    "checkable fast, an existing check settles it, survivable if wrong": "quick to check, an existing check settles it, and a mistake is cheap",
    "physical work — out of reach whatever its structure": "physical work, outside the screen",
}
METHOD = [
    "gates", "validation", "channel", "by_scorer", "rescore_stability", "adjudication", "placebo",
    "stability", "physical_gate", "not_called", "sigma",
]  # sigma is modelled; shown only here


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
    if m.get("draft"):
        errors.append(f"census: {spec['version']} is a draft export")
    if m["reconciliation"].get("verdicts_reproduced_from_published_columns") != 1.0:
        errors.append("census: the published per-scorer columns do not reproduce every verdict")
    tasks = rows(d / "tasks.csv")
    for key, col, keep in (
        ("passes_usd", "passes_usd", lambda t: truth(t["passes"])),
        ("agreed_all_three_usd", "agreed3_usd", lambda t: truth(t["passes"]) and truth(t["agreed_all_three"])),
    ):
        head = m["headline"][key]
        sums = {"tasks.csv": sum(num(t["task_payroll_usd"]) or 0 for t in tasks if keep(t))}
        sums |= {f: sum(num(r[col]) or 0 for r in rows(d / f)) for f in TABLES.values() if f != "tasks.csv"}
        errors += [f"census: {f} {col} sums to {v:.0f}, not the headline" for f, v in sums.items() if abs(v - head) > 1]
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
    """The manifest's measured headline figures, flat, for citing as [census:headline]; modelled ones are not citable."""
    if not spec or not (bundle(spec) / "manifest.json").exists():
        return {}
    out: dict[str, float] = {}
    for k, v in json.loads((bundle(spec) / "manifest.json").read_text())["headline"].items():
        if "modelled" in k:
            continue
        if isinstance(v, dict):
            out |= {f"{k}.{s}": float(x) for s, x in v.items()}
        else:
            out[k] = float(v)
    return out


def ref(spec: dict[str, Any], file: str, key: str) -> str:
    return f"census:{spec['version']}/{file}#{key}"


def _figure(h: dict[str, Any], val: dict[str, Any], scorers: list[str]) -> dict[str, Any]:
    """The payroll that passes, drawn as bars on one dollar axis: all three models, the two-of-three rule, and each
    model alone. Positions are drawing geometry, laid out here so the page computes nothing."""
    from .chart import axis, y

    bars = [
        ("All three models pass", h["agreed_all_three_usd"], "agreed3"),
        ("Passes the screen: two of the three models", h["passes_usd"], "rule"),
        *((f"{val['scorers'][k]['name']} alone", val["by_scorer"][k]["passes_usd"], k) for k in scorers),
    ]
    ax = axis([v for _, v, _ in bars], "USD", zero=True)
    return {
        "ticks": [{"left": round(100 - t["y"], 2), "label": t["label"]} for t in ax["ticks"]],
        "bars": [{"label": lab, "usd": v, "id": i, "width": round(100 - y(v, ax), 2)} for lab, v, i in bars],
    }


def build(spec: dict[str, Any], fetched: dict[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """index.json and one document per role. Selects, sorts and joins; computes no share or verdict."""
    if not spec:
        return {}, {}
    d = bundle(spec)
    v = spec["version"]
    m = json.loads((d / "manifest.json").read_text())
    val = json.loads((d / "validation.json").read_text())
    deals = json.loads((d / "deal_sheets.json").read_text())
    scorers = list(val["scorers"])  # scorer ids in the census's own order
    tasks = rows(d / "tasks.csv")
    by_occ: dict[str, list[dict[str, str]]] = {}
    for t in tasks:
        by_occ.setdefault(t["occ"], []).append(t)
    staffing: dict[str, list[dict[str, str]]] = {}
    for r in rows(d / "role_industry.csv"):
        staffing.setdefault(r["occ"], []).append(r)
    links = {x["cited_as"]: x["url"] for x in fetched.get("fetches") or []}
    csv_href = lambda f: f"/data/census/{v}/{f}"  # noqa: E731
    scored = lambda r: (num(r["payroll_scored_by_three"]) or 0) > 0  # noqa: E731 - none scored by all three: no figure, not $0

    roles = []
    docs = {}
    for r in rows(d / "roles.csv"):
        role = {
            "occ": r["occ"],
            "title": r["title"],
            "function": r["function"],
            "href": f"/census/roles/{r['occ']}",
            "ref": ref(spec, "roles.csv", r["occ"]),
            "emp": num(r["emp"]),
            "wage_bill": num(r["wage_bill"]),
            "share_passes": num(r["share_passes"]),
            "rule_strict": num(r["rule_strict"]),
            "rule_loose": num(r["rule_loose"]),
            "scorer_min": num(r["scorer_min"]),
            "scorer_max": num(r["scorer_max"]),
            "by_scorer": {s: num(r[f"share_{s}"]) for s in scorers},
            "passes": num(r["passes_usd"]),
            "agreed3": num(r["agreed3_usd"]) if scored(r) else None,
            "scored_by_three": scored(r),
            "payroll_scored_by_three": num(r["payroll_scored_by_three"]),
            "contested": num(r["contested_usd"]),
            "not_called": num(r["not_called_usd"]),
            "physical_removed": num(r["physical_removed_usd"]),
            "accountable_removed": num(r["accountable_removed_usd"]),
            "ai_exposure": num(r["ai_exposure"]),
            "n_tasks": int(r["n_tasks"]),
            "n_passes": int(r["n_goes"]),
            "time_share_basis": r["time_share_basis"],
            "split": r["split"],
        }
        roles.append(role)
        ts = sorted(by_occ.get(r["occ"], []), key=lambda t: (-(num(t["time_share"]) or 0), t["task_id"]))
        docs[r["occ"]] = {
            "version": v,
            "role": role,
            "scorers": scorers,
            "tasks": [
                {
                    "id": t["task_id"],
                    "ref": ref(spec, "tasks.csv", t["task_id"]),
                    "task": t["task"],
                    "passes": truth(t["passes"]),
                    "why": PLAIN_WHY.get(t["why"], t["why"]),
                    "physical": truth(t["physical"]),
                    "accountable": truth(t["accountable"]),
                    "not_called": truth(t["not_called"]),
                    "contested": truth(t["contested"]),
                    "agreed_all_three": truth(t["agreed_all_three"]),
                    "blocked_by_missing_check": truth(t["blocked_by_missing_check"]),
                    "passes_by": {s: truth(t[f"passes_by_{s}"]) for s in scorers},
                    "time_share": num(t["time_share"]),
                    "payroll": num(t["task_payroll_usd"]),
                }
                for t in ts
            ],
            "industries": [
                {"naics": x["naics"], "title": x["naics_title"], "emp": num(x["emp"]), "wage_bill": num(x["wage_bill"]), "passes": num(x["passes_usd"]), "agreed3": num(x["agreed3_usd"]) if scored(x) else None}
                for x in sorted(staffing.get(r["occ"], []), key=lambda x: (-(num(x["wage_bill"]) or 0), x["naics"]))[:10]
            ],
            "csv": csv_href("tasks.csv"),
        }
    roles.sort(key=lambda x: (x["function"], x["title"]))  # not ranks: alphabetical within a function

    h = m["headline"]
    index = {
        "version": v,
        "generated_at": m["generated_at"],
        "manifest_sha256": hashlib.sha256((d / "manifest.json").read_bytes()).hexdigest(),
        "sources": m["sources"],
        "scorers": scorers,
        "scorer_names": {k: x["name"] for k, x in val["scorers"].items()},
        "prose": {k: spec[k] for k in ("title", "lede", "rule", "agreed", "sections", "caveats", "method_notes")},
        "headline": {
            "passes": h["passes_usd"],
            "agreed3": h["agreed_all_three_usd"],
            "payroll": h["knowledge_payroll_usd"],
            "contested": h["contested_usd"],
            "blocked_by_missing_check": h["blocked_by_missing_check_usd"],
            "physical_removed": h["physical_removed_usd"],
            "accountable_removed": h["accountable_removed_usd"],
            "not_called": h["not_called_usd"],
            "by_scorer": {s: val["by_scorer"][s]["passes_usd"] for s in scorers},
            "rescore_changed": val["rescore_stability"]["share_verdicts_changed"],
            "fleiss_kappa": val["validation"]["agreement"]["fleiss_verdict"],
            "modelled_saving": h["modelled_saving_usd"],  # modelled: the page labels it so, and Ask cannot cite it
            "ref": ref(spec, "manifest.json", "headline"),
        },
        "figure": {**_figure(h, val, scorers), "ref": ref(spec, "manifest.json", "headline")},
        "dial": [
            {"rule": x["rule"], "passes": x["freed"], "agreed3": x["agreed3"], "alone": x["alone"], "alone_rest": x["alone_rest"], "headline": x["headline"],
             "vh": x["vh"], "g": x["g"], "l": x["l"], "label": (spec.get("dial_labels") or {}).get(f"{x['vh']}-{x['g']}-{x['l']}")}
            for x in val["dial"]
        ],
        "functions": sorted(
            (
                {
                    "function": r["function"],
                    "ref": ref(spec, "functions.csv", r["function"]),
                    "payroll": num(r["payroll"]),
                    "passes": num(r["passes_usd"]),
                    "agreed3": num(r["agreed3_usd"]) if scored(r) else None,
                    "scored_by_three": scored(r),
                    "payroll_scored_by_three": num(r["payroll_scored_by_three"]),
                    "share_passes": num(r["share_passes"]),
                    "rule_strict": num(r["rule_strict"]),
                    "rule_loose": num(r["rule_loose"]),
                    "blocked_by_missing_check": num(r["blocked_by_missing_check_usd"]),
                    "roles": int(r["roles"]),
                }
                for r in rows(d / "functions.csv")
            ),
            key=lambda x: (-(x["passes"] or 0), x["function"]),
        ),
        "industries": sorted(
            (
                {
                    "naics": r["naics"],
                    "title": r["naics_title"],
                    "ref": ref(spec, "industries.csv", r["naics"]),
                    "payroll": num(r["total"]),
                    "knowledge_payroll": num(r["know"]),
                    "passes": num(r["passes_usd"]),
                    "agreed3": num(r["agreed3_usd"]) if scored(r) else None,
                    "blocked_by_missing_check": num(r["blocked"]),
                    "share_total": num(r["share_total"]),
                }
                for r in rows(d / "industries.csv")
            ),
            key=lambda x: (-(x["passes"] or 0), x["naics"]),
        ),
        "roles": roles,
        "deals": {
            "cards": [
                {
                    **{k: c[k] for k in ("key", "name", "naics", "invoice", "why", "kill", "comps", "scope", "excl", "anchored", "stance", "stance_why")},
                    "sources": [{"cited_as": u, "href": links.get(u, u)} for u in c["sources"]],
                    "payroll": c["ind_payroll"],
                    "passes": c["passes_usd"],
                    "passes_strict": c["rule_strict_usd"],
                    "passes_loose": c["rule_loose_usd"],
                    "agreed3": c["agreed3_usd"] if c["payroll_scored_by_three"] > 0 else None,
                    "roles": [
                        {"title": x["title"], "wage_bill": x["wage_bill"], "share_passes": x["share_passes"], "passes": x["passes_usd"], "agreed3": x["agreed3_usd"] if x["payroll_scored_by_three"] > 0 else None}
                        for x in c["roles"]
                    ],
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
    return [spec["title"], spec["lede"], spec["rule"], spec["agreed"], *spec["caveats"], *spec["method_notes"].values(), *(x[k] for x in s.values() for k in ("title", "lede")), *(spec.get("dial_labels") or {}).values(),
            *(spec.get("stances") or {}).values(), *(spec.get("trade_flags") or {}).values(),
            *(x for t in trades_spec().get("trades") or [] for x in (t["name"], t.get("no_figure"), t.get("census_note")) if x)]


TRADES = ROOT / "seed" / "census_trades.yaml"
LAST = ("several", "other")  # catch-all entries close the list whatever their count


def trades_spec() -> dict[str, Any]:
    return (yaml.safe_load(TRADES.read_text()) or {}) if TRADES.exists() else {}


def trades(spec: dict[str, Any], index: dict[str, Any], names: dict[str, str], deals: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """The combined list: for each trade, the roll-ups in it (counted by where the directory places them), how many of
    them the acquisitions sweep covered, what they are on record as having bought, and one census figure: an industry
    row of the bundle, else a deal card's own figure, selected and never summed. `names` maps an entity id to its name;
    `deals` a rollup_acq series key to its stored row. Ordered by roll-ups in the trade, since deals found would rank
    how far the sweep reached. A flag marks where the census's reasoning and the buyers part ways; it settles nothing."""
    rows_by_code = {x["naics"]: x for x in index.get("industries") or []}
    cards = {c["key"]: c for c in (index.get("deals") or {}).get("cards") or []}
    swept = set(spec.get("swept") or [])
    out = []
    for t in spec.get("trades") or []:
        place = {w: t.get("rollups", {}).get(w, []) for w in ("us", "elsewhere", "unstated")}
        ids = [i for w in place.values() for i in w]
        card = cards.get(t.get("card") or "")
        row = rows_by_code.get(t.get("naics") or "")
        if row:
            fig = {"passes": row["passes"], "share": row["share_total"], "ref": row["ref"], "from": "industry", "title": row["title"]}
        elif card:
            fig = {"passes": card["passes"], "share": None, "ref": None, "from": "card", "title": None}
        else:
            fig = None
        flag = None
        if card and card["stance"] == "passes" and ids:
            flag = "buyers_despite_passes"
        elif card and card["stance"] == "keeps" and not ids:
            flag = "keeps_without_buyers"
        out.append({
            "key": t["key"], "name": t["name"], "census": fig, "no_figure": t.get("no_figure"), "census_note": t.get("census_note"),
            "card": t.get("card"), "flag": flag,
            "rollups": {"n": len(ids), **{w: len(v) for w, v in place.items()},
                        "names": [{"id": i, "name": names.get(i, i), "where": w, "swept": i in swept} for w, v in place.items() for i in v]},
            "swept": sum(1 for i in ids if i in swept),
            "deals": sorted(({"key": k, "obs_id": deals[k]["id"], "buyer": names.get(deals[k]["entity_id"], deals[k]["entity_id"]),
                              "text": deals[k]["value_text"], "date": str(deals[k]["as_of_date"])} for k in t.get("deals", []) if k in deals),
                            key=lambda d: (d["date"], d["key"])),
        })  # fmt: skip
    return sorted(out, key=lambda t: (t["key"] in LAST, -t["rollups"]["n"], t["name"]))


MIN_TARGETS = 200  # firms with 20 to 99 staff: fewer and there is not a rollup's worth to buy
MIN_PASSES = 5e8  # payroll passing the screen: less and the saving is too small to pay for the effort
NOT_FOR_SALE = ("813", "92")  # religious, civic and membership organisations, and government, are not bought


def rollup(index: dict[str, Any], small: dict[str, Any], firms: dict[str, Any], limit: int = 20) -> list[dict[str, Any]]:
    """Where a rollup could start: census industries ranked by the share of their payroll that passes the hand-over
    screen times how fragmented they are (the share of employment in firms under 500 staff, from the Census
    Statistics of US Businesses). Joins the census's own figure to a site metric; recomputes no census figure.
    Census industries are six-character codes; one ending in 00 is a four-digit NAICS industry, the level SUSB is read at.
    `small` maps a four-digit code to its derived row, `firms` to its firms-with-20-to-99-staff observation.
    Only industries with enough to buy and enough to gain count: at least MIN_TARGETS firms of 20 to 99 staff and at
    least MIN_PASSES of payroll passing the screen."""
    rows = []
    for x in index.get("industries") or []:
        code = x["naics"]
        if not (code.endswith("00") and code[:4] in small and x.get("share_total")) or code.startswith(NOT_FOR_SALE):
            continue
        d, f = small[code[:4]], firms.get(code[:4])
        if not f or f["value_numeric"] < MIN_TARGETS or (x.get("passes") or 0) < MIN_PASSES:
            continue
        rows.append(
            {
                "naics": code,
                "title": x["title"],
                "ref": x["ref"],
                "share_total": x["share_total"],
                "passes": x["passes"],
                "small_share": {"value": d.value, "derived_id": d.id, "obs_ids": d.input_observation_ids},
                "firms_20_99": {"value": f["value_numeric"], "obs_ids": [f["id"]]},
                "score": x["share_total"] * d.value,
            }
        )
    rows.sort(key=lambda r: (-r["score"], r["naics"]))
    return [{**r, "rank": i + 1} for i, r in enumerate(rows[:limit])]


def shape(spec: dict[str, Any]) -> dict[str, Any]:
    """Payroll by occupational group (the occupation code's major group, named in seed/census.yaml), best paid first,
    split four ways by the bundle's own task verdicts: passes the screen (with the part all three scorers pass beside
    it), waits only on a check, needs a body, and the rest. The bundle has no field for seniority, so this reads kinds of job, not rungs within one."""
    if not spec or not (bundle(spec) / "tasks.csv").exists():
        return {}
    names = spec.get("occupation_groups") or {}
    d = bundle(spec)
    groups: dict[str, dict[str, Any]] = {}
    for r in rows(d / "roles.csv"):
        g = groups.setdefault(r["occ"][:2], {"roles": 0, "emp": 0.0, "payroll": 0.0, "passes": 0.0, "agreed3": 0.0, "waits_on_check": 0.0, "physical": 0.0, "rest": 0.0})
        g["roles"] += 1
        g["emp"] += num(r["emp"]) or 0.0
        g["payroll"] += num(r["wage_bill"]) or 0.0
    for t in rows(d / "tasks.csv"):
        part = "passes" if truth(t["passes"]) else "waits_on_check" if truth(t["blocked_by_missing_check"]) else "physical" if truth(t["physical"]) else "rest"
        groups[t["occ"][:2]][part] += num(t["task_payroll_usd"]) or 0.0
        if truth(t["agreed_all_three"]):  # the firmest part of "passes", shown beside it wherever it is printed
            groups[t["occ"][:2]]["agreed3"] += num(t["task_payroll_usd"]) or 0.0
    out = []
    for code, g in groups.items():
        row = {"code": code, "name": names.get(code, ""), "ref": ref(spec, "tasks.csv", f"occ={code}-*"), "mean_pay": g["payroll"] / g["emp"], **g}
        row |= {f"share_{k}": g[k] / g["payroll"] for k in ("passes", "agreed3", "waits_on_check", "physical", "rest")}
        bar, x = [], 0.0
        for part in ("passes", "waits_on_check", "physical", "rest"):  # the stacked bar, in percent of the group's payroll
            w = 100 * g[part] / g["payroll"]
            bar.append({"part": part, "x": x, "w": w if part != "rest" else 100 - x})
            x += w
        row |= {"bar": bar, "agreed3_x": 100 * g["agreed3"] / g["payroll"]}
        out.append(row)
    return {"version": spec["version"], "groups": sorted(out, key=lambda g: -g["mean_pay"])}
