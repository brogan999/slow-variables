"""The Automatability Census (plan Part 21): a snapshot bundle built in a separate project and imported as published.

The site never recomputes a verdict or share. It checks the bundle against its own manifest, loads its tables for SQL,
and writes web/data/census/ by selecting, sorting and joining. A task "passes the structural hand-over screen" under the
census's rule; every "passes" figure travels with the part all three scorers pass (`agreed3`). Where none of a role's
or function's payroll was scored by all three, agreed3 is None and the page says so rather than printing a zero.
Modelled figures (the modelled saving, the substitution sigma) are exported only under keys that say so."""

from __future__ import annotations

import csv
import hashlib
import itertools
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
    index: dict[str, Any] = {
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
        "kinds": shape(spec),
        "figures": figures(spec, h, val, tasks, scorers),
        "dial": [
            {"rule": x["rule"], "ref": ref(spec, "validation.json", f"dial/{i}"), "passes": x["freed"], "agreed3": x["agreed3"], "alone": x["alone"], "alone_rest": x["alone_rest"], "headline": x["headline"],
             "vh": x["vh"], "g": x["g"], "l": x["l"], "label": (spec.get("dial_labels") or {}).get(f"{x['vh']}-{x['g']}-{x['l']}")}
            for i, x in enumerate(val["dial"])
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
                "agreed3": x.get("agreed3"),
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
        groups[t["occ"][:2]][_part(t)] += num(t["task_payroll_usd"]) or 0.0
        if truth(t["agreed_all_three"]):  # the firmest part of "passes", shown beside it wherever it is printed
            groups[t["occ"][:2]]["agreed3"] += num(t["task_payroll_usd"]) or 0.0
    out = []
    for code, g in groups.items():
        row = {"code": code, "name": names.get(code, ""), "ref": ref(spec, "tasks.csv", f"occ={code}-*"), "mean_pay": g["payroll"] / g["emp"], **g}
        row |= {f"share_{k}": g[k] / g["payroll"] for k in ("passes", "agreed3", "waits_on_check", "physical", "rest")}
        row |= {"bar": _bar(g, g["payroll"]), "agreed3_x": 100 * g["agreed3"] / g["payroll"]}
        out.append(row)
    return {"version": spec["version"], "groups": sorted(out, key=lambda g: -g["mean_pay"])}


PARTS = ("passes", "waits_on_check", "physical", "rest")
TIGHT = 15.0  # a row of the scorers figure whose marks span less than this much of the axis stacks on a phone
# The fixed phrases of the bundle's `why`, read as the question(s) most often failed among the scorers voting no.
QUESTIONS = {"hours": "nobody can tell quickly whether it worked", "check": "no existing check settles it", "stakes": "a failure is too expensive"}
GATES = {"physical": "physical work", "accountable": "an accountable sign-off"}
PASSED = "checkable fast, an existing check settles it, survivable if wrong"


def _part(t: dict[str, str]) -> str:
    """One of four things the screen says of a task's payroll, from the bundle's own flags."""
    return "passes" if truth(t["passes"]) else "waits_on_check" if truth(t["blocked_by_missing_check"]) else "physical" if truth(t["physical"]) else "rest"


def _bar(g: dict[str, Any], total: float) -> list[dict[str, Any]]:
    """The four parts as one stacked bar, in percent of `total`; the last part closes it."""
    bar, x = [], 0.0
    for part in PARTS:
        w = 100 * g[part] / total
        bar.append({"part": part, "x": x, "w": w if part != "rest" else 100 - x})
        x += w
    return bar


def reason(why: str) -> set[str]:
    """What a task's `why` says held it: a gate, or the question(s) most often failed among the scorers voting no (not
    every question it fails); empty when it passes. A phrase this does not know is an error, so a later bundle's new
    reason cannot fall silently into a remainder."""
    if why == PASSED:
        return set()
    for gate, start in GATES.items():
        if why.startswith(start):
            return {gate}
    by_phrase = {v: k for k, v in QUESTIONS.items()}
    parts = why.split(", and ")
    if not all(p in by_phrase for p in parts):
        raise ValueError(f"census: a reason the site has not read: {why!r}")
    return {by_phrase[p] for p in parts}


def _usd_bars(rows: list[dict[str, Any]], keep: tuple[str, ...]) -> dict[str, Any]:
    """Rows that carry `passes` and `agreed3`, laid on one dollar axis from zero."""
    from .chart import axis, y

    ax = axis([r["passes"] for r in rows], "USD", zero=True)
    w = lambda v: round(100 - y(v or 0.0, ax), 2)  # noqa: E731
    return {
        "ticks": [{"left": round(100 - t["y"], 2), "label": t["label"]} for t in ax["ticks"]],
        "rows": [{**{k: r[k] for k in keep}, "w": w(r["passes"]), "agreed3_x": w(r["agreed3"])} for r in rows],
    }


def figures(spec: dict[str, Any], h: dict[str, Any], val: dict[str, Any], tasks: list[dict[str, str]], scorers: list[str]) -> dict[str, Any]:
    """The census page's figures, laid out here so the page computes nothing. Each sums the bundle's task table by a
    flag or a fixed phrase the bundle itself gives; none re-votes a task."""
    from .chart import axis, y

    d = bundle(spec)
    total = h["knowledge_payroll_usd"]
    zero = lambda: {**dict.fromkeys(PARTS, 0.0), "agreed3": 0.0, **{f"by_{s}": 0.0 for s in scorers}}  # noqa: E731
    whole, by_fn = zero(), {r["function"]: zero() for r in rows(d / "functions.csv")}
    why = {k: 0.0 for k in (*GATES, *QUESTIONS)}
    for t in tasks:
        usd = num(t["task_payroll_usd"]) or 0.0
        for g in (whole, by_fn[t["function"]]):
            g[_part(t)] += usd
            g["agreed3"] += usd if truth(t["agreed_all_three"]) else 0.0
            for s in scorers:
                g[f"by_{s}"] += usd if truth(t[f"passes_by_{s}"]) else 0.0
        for k in reason(t["why"]):
            why[k] += usd
    mark = lambda k, usd: {"id": k, "usd": usd, "share": usd / total, "w": 100 * usd / total}  # noqa: E731
    voted = total - sum(why[k] for k in GATES)

    functions = []
    for r in rows(d / "functions.csv"):
        g, pay = by_fn[r["function"]], num(r["payroll"]) or 0.0
        functions.append({
            "function": r["function"], "ref": ref(spec, "functions.csv", r["function"]), "payroll": pay, **{k: g[k] for k in (*PARTS, "agreed3")},
            **{f"share_{k}": g[k] / pay for k in (*PARTS, "agreed3")}, "bar": _bar(g, pay), "agreed3_x": 100 * g["agreed3"] / pay,
        })  # fmt: skip
    functions.sort(key=lambda f: (-f["share_passes"], f["function"]))

    # each model's own share of a function's payroll, beside the vote and the part all three pass, on one share axis
    lines = [(None, ref(spec, "manifest.json", "headline"), whole, total), *((f["function"], f["ref"], by_fn[f["function"]], f["payroll"]) for f in functions)]
    ax = axis([g[f"by_{s}"] / pay for _, _, g, pay in lines for s in scorers], "share", zero=True)
    x = lambda v: round(100 - y(v, ax), 2)  # noqa: E731
    scorer_rows = []
    for fn, rf, g, pay in lines:
        by = {s: {"usd": g[f"by_{s}"], "share": g[f"by_{s}"] / pay, "x": x(g[f"by_{s}"] / pay)} for s in scorers}
        xs = [b["x"] for b in by.values()]
        tight = max(xs) - x(g["agreed3"] / pay) < TIGHT  # the page then prints the rule and all three in type, not as marks
        scorer_rows.append({
            "function": fn, "ref": rf, "passes": g["passes"], "agreed3": g["agreed3"], "share_passes": g["passes"] / pay, "share_agreed3": g["agreed3"] / pay,
            "by_scorer": by, "vote_x": x(g["passes"] / pay), "agreed3_x": x(g["agreed3"] / pay), "lo_x": min(xs), "hi_x": max(xs), "spread_w": round(max(xs) - min(xs), 2),
            "tight": tight, "note_x": round(max(xs) + 4, 2) if tight else None,
        })  # fmt: skip

    dial = _usd_bars(
        [{"rule": r["rule"], "passes": r["freed"], "agreed3": r["agreed3"], "headline": r["headline"], "ref": ref(spec, "validation.json", f"dial/{i}"),
          "label": (spec.get("dial_labels") or {}).get(f"{r['vh']}-{r['g']}-{r['l']}")} for i, r in enumerate(val["dial"])],
        ("rule", "passes", "agreed3", "headline", "label", "ref"),
    )  # fmt: skip
    return {
        "whole": {
            "payroll": total, "passes": whole["passes"], "agreed3": whole["agreed3"], "share_agreed3": whole["agreed3"] / total,
            "agreed3_x": 100 * whole["agreed3"] / total, "ref": ref(spec, "tasks.csv", "*"),
            "parts": [{**b, "usd": whole[b["part"]], "share": whole[b["part"]] / total} for b in _bar(whole, total)],
        },
        "screen": {
            "payroll": total, "ref": ref(spec, "tasks.csv", "why"), "gates": [mark(k, why[k]) for k in GATES], "voted": mark("voted", voted),
            "questions": [mark(k, why[k]) for k in QUESTIONS], "passes": whole["passes"], "agreed3": whole["agreed3"],
            "share_passes": whole["passes"] / total, "share_agreed3": whole["agreed3"] / total,
            "passes_w": 100 * whole["passes"] / total, "agreed3_x": 100 * whole["agreed3"] / total,
        },
        "dial": dial,
        "functions": functions,
        "scorers": {"ticks": [{"left": round(100 - t["y"], 2), "label": t["label"]} for t in ax["ticks"]], "rows": scorer_rows},
    }  # fmt: skip


# Where a rank label may sit: the offset of its box from the dot, in pixels, as the page's SIDE map draws the same
# names. A pixel is a different share of the plot on a phone and on a desk, so each gets its own choice of place.
PLOT_PX = {"label": (282.0, 288.0), "label_wide": (790.0, 384.0)}  # the plot's width and height at each
LABEL_PX, DOT_PX = (17.0, 13.0), 11.0
LABEL_SIDES = {
    "r": (6.0, -7.0), "l": (-23.0, -7.0), "t": (-8.5, -19.0), "b": (-8.5, 4.0),
    "tr": (5.0, -16.0), "tl": (-22.0, -16.0), "br": (5.0, 2.0), "bl": (-22.0, 2.0),
    "r2": (16.0, -7.0), "l2": (-33.0, -7.0), "t2": (-8.5, -30.0), "b2": (-8.5, 15.0),
    "tr2": (12.0, -23.0), "tl2": (-29.0, -23.0), "br2": (12.0, 9.0), "bl2": (-29.0, 9.0),
}  # fmt: skip


def label_box(q: dict[str, Any], key: str = "label") -> tuple[float, float, float, float]:
    """A point's rank label as a box in percent of the plot, at the plot size `key` names."""
    (w, h), (dx, dy) = PLOT_PX[key], LABEL_SIDES[q[key]]
    return (q["x"] + 100 * dx / w, q["y"] + 100 * dy / h, 100 * LABEL_PX[0] / w, 100 * LABEL_PX[1] / h)


def dot_box(q: dict[str, Any], key: str = "label") -> tuple[float, float, float, float]:
    w, h = PLOT_PX[key]
    return (q["x"] - 50 * DOT_PX / w, q["y"] - 50 * DOT_PX / h, 100 * DOT_PX / w, 100 * DOT_PX / h)


def _hit(a: tuple[float, ...], b: tuple[float, ...]) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def _place(points: list[dict[str, Any]], key: str) -> None:
    """A rank label takes the first place around its dot where it covers no dot and no other label: the four sides,
    then the corners, then a ring further out. Covering a listed dot or a label costs more than covering a hollow
    dot. Labels are placed in rank order, then tried again against where the others ended up, alone and in pairs
    (two labels in a knot often have to move together)."""
    listed = [q for q in points if q["listed"]]
    dots = [(dot_box(q, key), 3 if q["listed"] else 1, q) for q in points]

    def cost(q: dict[str, Any]) -> float:
        b = label_box(q, key)
        return (
            100 * (b[0] < 0 or b[0] + b[2] > 100 or b[1] < 0)
            + sum(w for d, w, o in dots if o is not q and _hit(b, d))
            + sum(3 for o in listed if o is not q and key in o and _hit(b, label_box(o, key)))
        )

    def settle(qs: tuple[dict[str, Any], ...]) -> None:
        def total(ks: tuple[str, ...]) -> float:
            for q, k in zip(qs, ks):
                q[key] = k
            return sum(cost(q) for q in qs)

        total(min(itertools.product(LABEL_SIDES, repeat=len(qs)), key=total))

    for q in listed:
        settle((q,))
    for _ in range(3):
        for q in listed:
            settle((q,))
        for a, b in itertools.combinations(listed, 2):
            if cost(a) + cost(b) and abs(a["x"] - b["x"]) < 20 and abs(a["y"] - b["y"]) < 20:
                settle((a, b))


def rollup_plot(ranked: list[dict[str, Any]], shown: int = 20) -> dict[str, Any]:
    """Every industry `rollup` ranks, placed by its two ingredients: across, the share of its employment in small
    firms; up, the share of its payroll that passes. The first `shown` are the page's list; the curve is the score of
    the last of them, so the list is everything on or above it."""
    from .chart import axis, y

    if not ranked:
        return {}
    xa = axis([r["small_share"]["value"] for r in ranked], "share", zero=True)
    ya = axis([r["share_total"] for r in ranked], "share", zero=True)
    px = lambda v: round(100 - y(v, xa), 2)  # noqa: E731
    cut = ranked[min(shown, len(ranked)) - 1]["score"]
    lo = max(cut / ya["hi"], xa["lo"] + (xa["hi"] - xa["lo"]) / 200)  # where the curve enters at the top of the plot
    steps = [lo + (xa["hi"] - lo) * i / 40 for i in range(41)]
    curve = [{"x": px(v), "y": max(0.0, y(cut / v, ya))} for v in steps]
    points = [
        {"naics": r["naics"], "title": r["title"], "ref": r["ref"], "rank": r["rank"], "listed": r["rank"] <= shown, "passes": r["passes"], "agreed3": r.get("agreed3"),
         "share_total": r["share_total"], "small_share": r["small_share"]["value"], "x": px(r["small_share"]["value"]), "y": y(r["share_total"], ya)}
        for r in ranked
    ]  # fmt: skip
    for key in PLOT_PX:
        _place(points, key)
    return {
        "x": {"ticks": [{"x": round(100 - t["y"], 2), "label": t["label"]} for t in xa["ticks"]]},
        "y": {"ticks": ya["ticks"], "unit": None, "log": False, "chars": max(len(t["label"]) for t in ya["ticks"])},
        "points": points,
        "cut": curve,
        "cut_points": " ".join(f"{c['x']},{c['y']}" for c in curve),
    }  # fmt: skip
