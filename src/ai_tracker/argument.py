"""The opening argument as data: facts for the essays' [fact:id] tokens, the five slow variables, the clocks plate,
the Perez phase and the exits. The essays never type a number; `problems` re-tests every sentence's premise nightly."""

from __future__ import annotations

import re
from datetime import date, timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from .store import Store

SPEC = Path("seed/argument.yaml")
ESSAYS = {"home": Path("docs/argument/home.md"), "full": Path("docs/argument/full.md")}
PLATES = {"clocks", "perez", "stack"}
TOKEN = re.compile(r"\[(fact|plate):([a-z0-9_]+)\]")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text())


def _metric_href(s: Store, metric: str) -> str:
    ind = next(
        (i for i in s.seed.indicators if i.published and metric in (i.metric, (i.band_input or "")[7:])), None
    )
    return f"/indicators/{ind.id}" if ind else "/query"


def fact(s: Store, spec: dict[str, Any]) -> dict[str, Any] | None:
    if "indicator" in spec:
        ind = next(i for i in s.seed.indicators if i.id == spec["indicator"])
        pts = s.headline(ind)
        if not pts:
            return None
        p = pts[-1]
        return {
            "value": p["value"],
            "unit": p["unit"],
            "as_of": p["as_of"],
            "obs_ids": p["obs_ids"],
            "href": f"/indicators/{ind.id}",
        }
    rows = s.derived_for(spec["metric"], spec.get("dims"))
    if not rows:
        return None
    d = rows[-1]
    if spec.get("pick") == "quarter_end":  # the latest reading dated on a calendar quarter's last day
        d = next(
            (
                r
                for r in reversed(rows)
                if (r.as_of_date + timedelta(days=1)).day == 1 and r.as_of_date.month in (3, 6, 9, 12)
            ),
            None,
        )
        if d is None:
            return None
    if spec.get("pick") == "year_ago":  # exactly a year back, give or take a quarter-end's calendar drift
        d = next((r for r in reversed(rows) if 355 <= (rows[-1].as_of_date - r.as_of_date).days <= 375), None)
        if d is None:
            return None
    return {
        "value": d.value,
        "unit": s.metric_spec(spec["metric"]).get("unit"),
        "as_of": d.as_of_date.isoformat(),
        "obs_ids": d.input_observation_ids,
        "href": _metric_href(s, spec["metric"]),
    }


def _holds(expect: dict[str, Any] | None, value: float, other: dict[str, float | None]) -> bool | None:
    if not expect:
        return None
    ((op, rhs),) = expect.items()
    rhs = other.get(rhs) if isinstance(rhs, str) else rhs
    if rhs is None:
        return None
    return {"gt": value > rhs, "gte": value >= rhs, "lt": value < rhs, "lte": value <= rhs}[op]


def facts(s: Store, spec: dict[str, Any]) -> dict[str, dict[str, Any] | None]:
    out = {k: fact(s, v) for k, v in spec["facts"].items()}
    values = {k: (f["value"] if f else None) for k, f in out.items()}
    for k, f in out.items():
        if f:
            f["holds"] = _holds(spec["facts"][k].get("expect"), f["value"], values)
    return out


def clocks(s: Store, spec: dict[str, Any]) -> dict[str, Any]:
    c = spec["clocks"]
    start = str(c["start"])
    drawn, listed = [], []
    for link in c["links"]:
        ind = next(i for i in s.seed.indicators if i.id == link["id"])
        # a disputed reading (METR's above its suite's ceiling, say) never sets a line's shape
        mine = [
            p for p in s.headline(ind) if fnmatch(p["series_key"], link["series"]) and not p.get("disputed")
        ]
        pts = [p for p in mine if p["as_of"] >= start]
        if link.get("frontier"):  # the running best, starting from the best reading before the start date
            before = [p for p in mine if p["as_of"] < start]
            best: list[dict[str, Any]] = [max(before, key=lambda p: p["value"])] if before else []
            for p in pts:
                if not best or p["value"] > best[-1]["value"]:
                    best.append(p)
            pts = best
        if len(pts) < 3 or pts[0]["value"] is None or pts[0]["value"] <= 0:
            listed.append(link["id"])
            continue
        first, last = pts[0], pts[-1]
        drawn.append(
            {
                **link,
                "name": ind.name,
                "unit": ind.unit,
                "from": first["as_of"],
                "series": [{"as_of": p["as_of"], "value": p["value"], "obs_ids": p["obs_ids"]} for p in pts],
                "multiple": {
                    "value": last["value"] / first["value"],
                    "unit": "ratio",
                    "as_of": last["as_of"],
                    "obs_ids": first["obs_ids"] + last["obs_ids"],
                    "href": f"/indicators/{ind.id}",
                },
            }
        )
    mult = {d["id"]: d["multiple"]["value"] for d in drawn}
    a, b = c.get("expect", {}).get("gt", [None, None])
    holds = mult[a] > mult[b] if a in mult and b in mult else None
    return {"start": start, "drawn": drawn, "listed": listed, "holds": holds}


def _raw_phase(capex: float, fin: float | None, fin_year_ago: float | None) -> str:
    if fin is None:
        return "untestable"
    if capex >= 1 and fin > 0:
        return "installation"
    if capex < 0.5 and fin_year_ago is not None and fin < fin_year_ago:
        return "deployment"
    return "turning_point"


def phase(s: Store, spec: dict[str, Any]) -> dict[str, Any]:
    p = spec["phase"]
    capex = s.derived_for(p["capex"])
    fin = {d.as_of_date: d for d in s.derived_for(p["financing"])}

    def fin_at(day: date) -> Any:
        """The flow read at that quarter end, else the latest reading inside the quarter."""
        return fin.get(day) or max(
            (d for k, d in fin.items() if day - timedelta(days=92) < k <= day),
            key=lambda d: d.as_of_date,
            default=None,
        )

    history: list[dict[str, Any]] = []
    state = None
    for c in capex:
        f, f0 = fin_at(c.as_of_date), fin_at(c.as_of_date.replace(year=c.as_of_date.year - 1))
        raw = _raw_phase(c.value, f.value if f else None, f0.value if f0 else None)
        if state is None or (raw != state and history and history[-1]["raw"] == raw):
            state = raw
        history.append({"as_of": c.as_of_date.isoformat(), "raw": raw, "state": state})
    if not capex or not fin:
        return {"state": "untestable", "rule": p["rule"], "as_of": None, "history": history}
    return {"state": state, "rule": p["rule"], "as_of": history[-1]["as_of"], "history": history}


def exits(spec: dict[str, Any]) -> list[dict[str, Any]]:
    from .store import DATA, read_jsonl

    states = {v["id"]: v.get("state") for v in read_jsonl(DATA / "thesis.jsonl")}
    return [
        {
            "monitor": e["monitor"],
            "label": e.get("label"),
            "text": e["text"],
            "state": states.get(e["monitor"]),
        }
        for e in spec["exits"]
    ]


def headlines(spec: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Each lens page's headline: the claim its monitor's current state supports, in the words the seed gives."""
    from .store import DATA, read_jsonl

    states = {v["id"]: v.get("state") for v in read_jsonl(DATA / "thesis.jsonl")}
    out = {}
    for page, h in spec["headlines"].items():
        state = states.get(h["monitor"]) or "untestable"
        out[page] = {
            "monitor": h["monitor"],
            "state": state,
            "claim": h["claims"].get(state) or h["claims"]["untestable"],
        }
    return out


def essay_shape(text: str) -> list[str]:
    """What the page renderer needs: a title, a lede, then folios each opened by one label and one claim."""
    blocks = [b.strip() for b in text.split("\n\n") if b.strip()]
    bad = []
    if not blocks or not blocks[0].startswith("# "):
        bad.append("does not open with a '# ' title")
    folio = None
    for b in blocks[2:]:
        if b.startswith("### "):
            if folio is not None and not folio["claim"]:
                bad.append(f"folio '{folio['label']}' has no '## ' claim")
            folio = {"label": b[4:], "claim": False}
        elif b.startswith("## "):
            if folio is None:
                bad.append("a '## ' claim comes before any '### ' folio label")
            elif folio["claim"]:
                bad.append(f"folio '{folio['label']}' has two '## ' claims")
            else:
                folio["claim"] = True
        elif folio is None:
            bad.append("text between the lede and the first folio would be dropped")
    if folio is not None and not folio["claim"]:
        bad.append(f"folio '{folio['label']}' has no '## ' claim")
    return bad


def build(s: Store) -> dict[str, Any]:
    spec = load()
    f = facts(s, spec)
    return {
        "as_of": max((x["as_of"] for x in f.values() if x), default=None),
        "essay": {k: p.read_text() for k, p in ESSAYS.items()},
        "facts": f,
        "slow_variables": spec["slow_variables"],
        "clocks": clocks(s, spec),
        "phase": phase(s, spec),
        "exits": exits(spec),
        "headlines": headlines(spec),
        "sources": spec["sources"],
    }


def problems(s: Store) -> tuple[list[str], list[str]]:
    """Errors for anything that cannot resolve (CI catches them); attention for sentences the data stopped backing."""
    spec = load()
    errors: list[str] = []
    ids = {i.id for i in s.seed.indicators}
    published = {i.id for i in s.seed.indicators if i.published}
    for k, v in spec["facts"].items():
        if "indicator" in v and v["indicator"] not in ids or "metric" in v and not s.metric_spec(v["metric"]):
            errors.append(f"argument: fact {k} names an unknown indicator or metric")
    for x in spec["slow_variables"] + spec["clocks"]["links"]:
        if x["id"] not in published:
            errors.append(f"argument: {x['id']} is not a published indicator")
    from .thesis import RULES

    monitors = {r.__name__ for r in RULES}
    for e in spec["exits"]:
        if e["monitor"] not in monitors or not e.get("label"):
            errors.append(f"argument: exit {e['monitor']} names an unknown monitor or has no label")
    for page, h in spec["headlines"].items():
        if h["monitor"] not in monitors or "untestable" not in h["claims"]:
            errors.append(f"argument: {page} headline names an unknown monitor or has no untestable claim")
    for path in ESSAYS.values():
        text = path.read_text() if path.exists() else ""
        if not text:
            errors.append(f"argument: {path} is missing")
        errors += [f"argument: {path} {b}" for b in essay_shape(text)] if text else []
        for kind, key in TOKEN.findall(text):
            if kind == "fact" and key not in spec["facts"] or kind == "plate" and key not in PLATES:
                errors.append(f"argument: {path} has an unknown [{kind}:{key}]")
    if errors:
        return errors, []
    notes: list[str] = []
    for k, f in facts(s, spec).items():
        if f is None:
            notes.append(f"argument: fact {k} has no reading; the essay shows a gap there")
        elif f["holds"] is False:
            notes.append(
                f"argument: fact {k} no longer meets {spec['facts'][k]['expect']}; rewrite the sentence that leans on it"
            )
    if clocks(s, spec)["holds"] is False:
        notes.append(
            "argument: the clocks plate's caption (capability outpacing the work) no longer holds; rewrite it"
        )
    # the essays also assert states in words ("installation", "contradicted"): re-test those too
    got = {e["monitor"]: e["state"] for e in exits(spec)}
    want = {e["monitor"]: e["expect"] for e in spec["exits"] if e.get("expect")}
    if spec["phase"].get("expect"):
        got["phase"], want["phase"] = phase(s, spec)["state"], spec["phase"]["expect"]
    for k, w in want.items():
        if got.get(k) != w:
            notes.append(
                f"argument: the essays say {k} reads {w}, but it now reads {got.get(k)}; rewrite them"
            )
    return errors, notes
