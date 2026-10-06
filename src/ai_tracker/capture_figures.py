"""The figures on /capture (Part 45f): every capture gauge as one mark, the profit split a year apart, each lab's
run-rate against what it has raised and promised, who is tied to whom on the financing ledger, and the concentration
indices on one strip. Everything is summed and laid out here from records the export already holds, so the page only
places it; the model of the page's rule is seed text."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from . import chart
from .market_map import display

SPEC = Path(__file__).resolve().parents[2] / "seed" / "capture.yaml"
# the words a gauge can read, in the order the figure's columns run; anything else is not yet a reading either way
WORDS = (("concentrating", "Toward fewer firms"), ("stable", "Holding steady"), ("open", "Too early or unclear"), ("dispersing", "Spreading out"))
# what an instrument on the financing ledger is: a promise to buy, or money or credit put behind the other party
KIND = {
    "contract": "buy", "commitment": "buy", "azure_commitment": "buy", "aws_commitment": "buy", "backstop": "buy",
    "equity": "stake", "equity_round": "stake", "guarantee": "stake",
}  # fmt: skip
CONCENTRATION = ("semis_hhi", "cloud_hhi", "lab_hhi", "model_token_concentration")
KEPT = 8  # the counterparties drawn by name; the rest are one node (a drawing rule, stated in the figure's foot)
GAP = 1.4  # percent of the drawing's height between two nodes


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text())


def strings(x: Any) -> list[str]:
    """The model's own words, for the test that keeps figures out of them."""
    if isinstance(x, str):
        return [x]
    if isinstance(x, dict):
        return [s for k, v in x.items() if k not in ("id", "after") for s in strings(v)]
    return [s for v in x for s in strings(v)] if isinstance(x, list) else []


def word(status: str | None) -> str:
    return status if status in ("concentrating", "stable", "dispersing") else "open"


def _gauges(store: Any, layers: list[dict[str, Any]]) -> dict[str, Any]:
    ruled = {i.id for i in store.seed.indicators if i.published and i.direction_rule}
    rows = []
    for layer in layers:
        mine = sorted((c for c in layer["indicators"] if c["id"] in ruled), key=lambda c: (-(c.get("confidence") or 0), c["id"]))
        groups = []
        for w, _ in WORDS:
            marks = [{"id": c["id"], "name": c["name"], "status": c["status"], "href": f"/indicators/{c['id']}"} for c in mine if word(c["status"]) == w]
            groups.append({"word": w, "n": len(marks), "marks": marks})
        rows.append({"id": layer["id"], "name": layer["name"], "order": layer["order"], "href": f"/layers/{layer['id']}", "status": layer["status"], "n": len(mine), "groups": groups})
    return {"words": [{"id": w, "label": label} for w, label in WORDS], "layers": rows, "n": sum(r["n"] for r in rows)}


def _year(stacks: dict[str, tuple[str, dict[str, Any]]]) -> dict[str, Any]:
    rows = []
    for name, (what, stack) in stacks.items():
        quarters = {q["as_of"]: q for q in stack["quarters"] if q["parts"]}
        if not quarters:
            continue
        newest = quarters[max(quarters)]
        before = quarters.get(f"{int(newest['as_of'][:4]) - 1}{newest['as_of'][4:]}")
        for p in newest["parts"]:
            old = next((o for o in before["parts"] if o["id"] == p["id"]), None) if before else None

            def end(part: dict[str, Any], q: dict[str, Any]) -> dict[str, Any]:
                return {"value": part["value"], "unit": "share", "as_of": q["as_of"], "quarter": q["name"], "x": round(100 * part["value"], 2), "href": part["href"], "obs_ids": part["obs_ids"]}

            rows.append({
                "stack": name, "what": what, "id": p["id"], "name": p["name"], "estimated": p["estimated"] or bool(old and old["estimated"]),
                "now": end(p, newest), "then": end(old, before) if old else None,
                "change": chart.change_label(p["value"] - old["value"], "share") if old else None,
                "rose": (p["value"] > old["value"]) if old else None,
            })  # fmt: skip
    return {"rows": rows, "ticks": [{"x": x, "label": f"{x}%"} for x in (0, 25, 50, 75, 100)]}


def _counted(store: Any, ledger: list[dict[str, Any]]) -> tuple[Any, list[dict[str, Any]]]:
    """The ledger rows the site's cumulative total counts (signed deals in dollars; no letters of intent, talks or
    self-reported aggregates), read off the metric's own inputs so this never restates its rule."""
    totals = store.derived_for("circular_commitments_total")
    if not totals:
        return None, []
    ids = set(totals[-1].input_observation_ids)
    rows = [r for r in ledger if r["id"] in ids]
    unknown = {r["instrument"] for r in rows} - set(KIND)
    if unknown:  # a new instrument must be read and named before it is drawn
        raise ValueError(f"capture_figures: ledger instruments with no kind: {sorted(unknown)}")
    return totals[-1], rows


def _labs(store: Any, counted: list[dict[str, Any]]) -> dict[str, Any]:
    ents = {e.id: e for e in store.seed.entities}
    obs = {o["id"]: o for o in store.observations("epoch.*.revenue_run_rate_usd.pt", "epoch.*.round_equity_usd.pt")}
    latest: dict[str, Any] = {}
    for d in store.derived_for("lab_recoupment_ratio"):
        latest[d.dims["entity"]] = d
    rows = []
    for subject, d in latest.items():
        mine = [obs[i] for i in d.input_observation_ids]  # the ratio's own inputs: one run-rate, and every round by its date
        rr, rounds = next(o for o in mine if o["measure"] == "revenue_run_rate_usd"), [o for o in mine if o["measure"] == "round_equity_usd"]
        eid = rr["entity_id"] or subject
        buys = [r for r in counted if KIND[r["instrument"]] == "buy" and any(p["entity_id"] == eid for p in r["parties"])]
        rows.append({
            "id": eid, "subject": subject, "name": display(ents[eid]) if eid in ents else subject,
            "run_rate": {"value": rr["value_numeric"], "unit": "USD", "as_of": rr["as_of_date"].isoformat(), "obs_ids": [rr["id"]], "href": store.href_of([rr["id"]]), "stamp": store.stamp_of([rr["id"]])},
            "equity": {"value": sum(o["value_numeric"] for o in rounds), "unit": "USD", "n": len(rounds), "obs_ids": [o["id"] for o in rounds], "as_of": max(o["as_of_date"] for o in rounds).isoformat()},
            "promised": {"value": sum(r["value_numeric"] for r in buys), "unit": "USD", "n": len(buys), "obs_ids": [r["id"] for r in buys]} if buys else None,
            "ratio": {"value": d.value, "unit": "ratio", "as_of": d.as_of_date.isoformat(), "obs_ids": d.input_observation_ids, "href": store._derived_href(d)},
        })  # fmt: skip
    rows.sort(key=lambda r: -r["equity"]["value"])
    top = max((b["value"] for r in rows for b in (r["run_rate"], r["equity"], r["promised"]) if b), default=1.0)
    for r in rows:
        for b in (r["run_rate"], r["equity"], r["promised"]):
            if b:
                b["w"] = round(100 * b["value"] / top, 2)
    drawn = {r["id"] for r in rows}
    frontier = [e for e in store.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)]
    return {"rows": rows, "absent": [display(e) for e in frontier if e.id not in drawn]}


def _ties(store: Any, total: Any, counted: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Who is tied to whom: each counted row joins a frontier lab (right) to its counterparty (left); a deal with no
    frontier lab in it runs between suppliers. Bands are sized by face value, the same scale on both sides."""
    if total is None:
        return None
    ents = {e.id: e for e in store.seed.entities}
    labs = {e.id for e in store.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)}

    def name(p: dict[str, Any]) -> str:
        return display(ents[p["entity_id"]]) if p["entity_id"] in ents else p["name"]

    pairs: dict[tuple[str, str, str], dict[str, Any]] = {}
    for r in counted:
        a, b = r["parties"]
        lab = next((p for p in (b, a) if p["entity_id"] in labs), None)
        other = a if lab is b else b
        if lab is None:
            lab, other = b, a
        key = (other["entity_id"], lab["entity_id"], KIND[r["instrument"]])
        row = pairs.setdefault(key, {"a": other["entity_id"], "a_name": name(other), "b": lab["entity_id"], "b_name": name(lab), "lab": lab["entity_id"] in labs, "kind": key[2], "value": 0.0, "unit": "USD", "n": 0, "obs_ids": [], "press": 0, "href": "/ledger"})
        row["value"] += r["value_numeric"]
        row["n"] += 1
        row["obs_ids"].append(r["id"])
        row["press"] += r["audited_vs_reported"] == "reported"
    rows = sorted(pairs.values(), key=lambda p: -p["value"])
    left_total: Counter[str] = Counter()
    for p in rows:
        if p["lab"]:
            left_total[p["a"]] += p["value"]
    kept = [k for k, _ in left_total.most_common(KEPT)]
    names = {p["a"]: p["a_name"] for p in rows} | {p["b"]: p["b_name"] for p in rows}

    def ends(p: dict[str, Any]) -> tuple[str, str]:
        return ("none", "none") if not p["lab"] else (p["a"] if p["a"] in kept else "other", p["b"])

    bands: dict[tuple[str, str, str], dict[str, Any]] = {}
    for p in rows:
        le, ri = ends(p)
        b = bands.setdefault((le, ri, p["kind"]), {"left": le, "right": ri, "kind": p["kind"], "value": 0.0, "unit": "USD", "n": 0, "obs_ids": []})
        b["value"] += p["value"]
        b["n"] += p["n"]
        b["obs_ids"] += p["obs_ids"]
    label = {"other": "Other suppliers", "none": "No frontier lab in the deal"}

    def side(key: str) -> list[dict[str, Any]]:
        size: Counter[str] = Counter()
        for b in bands.values():
            size[b[key]] += b["value"]
        order = sorted(size, key=lambda k: (k in ("other", "none"), k == "none", -size[k]))
        scale = (100 - GAP * (max(len(kept), 1) + 1)) / total.value  # one scale for both sides: the left has the most gaps
        gap = GAP if key == "left" else (100 - scale * total.value) / max(len(order) - 1, 1)
        out, at = [], 0.0
        for k in order:
            out.append({"id": k, "name": label.get(k) or names[k], "value": size[k], "unit": "USD", "y": round(at, 3), "h": round(scale * size[k], 3), "obs_ids": [i for b in bands.values() if b[key] == k for i in b["obs_ids"]]})
            at += scale * size[k] + gap
        mids = chart.spread([n["y"] + n["h"] / 2 for n in out], 5.8)
        for n, m in zip(out, mids):
            n["label_y"] = m
        return out

    left, right = side("left"), side("right")
    lo, ro = [n["id"] for n in left], [n["id"] for n in right]
    drawn = sorted(bands.values(), key=lambda b: (lo.index(b["left"]), ro.index(b["right"]), b["kind"]))
    for key, nodes, other, order in (("left", left, "right", ro), ("right", right, "left", lo)):
        for n in nodes:
            at = n["y"]
            for b in sorted((b for b in drawn if b[key] == n["id"]), key=lambda b: (order.index(b[other]), b["kind"])):
                b[f"{key}_y"], b[f"{key}_h"] = round(at, 3), round(n["h"] * b["value"] / n["value"], 3)
                at += n["h"] * b["value"] / n["value"]
    for b in drawn:
        y0, y1, z0, z1 = b["left_y"], b["left_y"] + b["left_h"], b["right_y"], b["right_y"] + b["right_h"]
        b["d"] = f"M0,{y0:.2f} C50,{y0:.2f} 50,{z0:.2f} 100,{z0:.2f} L100,{z1:.2f} C50,{z1:.2f} 50,{y1:.2f} 0,{y1:.2f} Z"
        b["left_name"], b["right_name"] = next(n["name"] for n in left if n["id"] == b["left"]), next(n["name"] for n in right if n["id"] == b["right"])
    return {
        "total": {"value": total.value, "unit": "USD", "as_of": total.as_of_date.isoformat(), "obs_ids": total.input_observation_ids, "href": "/indicators/circular_financing_scale", "n": len(counted)},
        "left": left, "right": right, "bands": drawn, "pairs": rows,
    }  # fmt: skip


def _concentration(store: Any, layers: list[dict[str, Any]]) -> dict[str, Any]:
    said = {i.id: i.definition for i in store.seed.indicators}
    cards = {c["id"]: (c, layer) for layer in layers for c in layer["indicators"]}
    rows = []
    for i in CONCENTRATION:
        if i in cards and cards[i][0]["latest"] and cards[i][0]["unit"] == "index":
            c, layer = cards[i]
            rows.append({"id": i, "name": c["name"], "layer": layer["name"], "href": f"/indicators/{i}", "value": c["latest"]["value"], "unit": "index", "x": round(100 * c["latest"]["value"], 2), "as_of": c["latest"]["as_of"], "obs_ids": c["latest"]["obs_ids"], "status": c["status"], "counts": said[i]})
    return {"rows": rows}


def build(store: Any, layers: list[dict[str, Any]], gross: dict[str, Any], margin: dict[str, Any], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    total, counted = _counted(store, ledger)
    return {
        "gauges": _gauges(store, layers),
        "year": _year({"gross_profit": ("gross profit", gross), "operating_income": ("operating income", margin)}),
        "labs": _labs(store, counted),
        "ties": _ties(store, total, counted),
        "concentration": _concentration(store, layers),
        "rule": load()["rule"],
    }
