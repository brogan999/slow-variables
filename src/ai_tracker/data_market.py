"""The data market (plan Part 57): what the firms that sell training data show their buyers asking for.

seed/data_market.yaml lists the vendors and the signals, in a model's words, read from the vendors' own pages. Each
vendor is listed under a signal only with a page of its own that was fetched (seed/data_market_fetches.yaml), so a
signal's count is a count of cited pages' owners; vendors whose growth evidence is weak are counted apart. Nothing here
is a reading or a status, and no evaluator, metric or query tool reads it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .board import FIGURE, YEAR

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "data_market.yaml"
FETCHES = ROOT / "seed" / "data_market_fetches.yaml"
SOCIAL = re.compile(r"https?://([\w-]+\.)*(x|twitter|linkedin|facebook|instagram|tiktok|reddit)\.com/", re.I)
ROLES = ("seller", "builder")
EVIDENCE = ("evidenced", "weak")
UNITS = {
    "per hour": "Paid by the hour",
    "salary": "Salaries",
    "per task": "Paid by the task",
    "per company": "Offered for one company's records",
    "per dataset": "For a dataset",
    "other": "Other sums",
}
WHOSE = {
    "job post": "job listing",
    "company claim": "the company's own page",
    "press": "press report",
    "terms": "published terms",
}


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def fetches() -> list[dict[str, Any]]:
    return (yaml.safe_load(FETCHES.read_text()) or {}).get("fetches") or [] if FETCHES.exists() else []


def _figure(text: str) -> bool:
    return bool(FIGURE.search(YEAR.sub("", text)))


def figures(text: str) -> list[str]:
    """The numbers a text states, commas dropped: what a price's amount must share with its snippet."""
    return re.findall(r"\d+(?:\.\d+)?", re.sub(r"(?<=\d),(?=\d)", "", text or ""))


def _dups(ids: list[Any]) -> list[Any]:
    return sorted({i for i in ids if ids.count(i) > 1})


def problems(doc: dict[str, Any], fetched: list[dict[str, Any]]) -> list[str]:
    errors = []
    for k in ("model", "date", "method", "reviewed_by"):
        if not (doc.get("made_by") or {}).get(k):
            errors.append(f"data market: made_by has no {k}")
    if "Anthropic" not in str(doc.get("disclosure") or ""):
        errors.append("data market: the disclosure does not name Anthropic")
    record = {f["url"]: f for f in fetched}

    def page(where: str, url: str) -> None:
        if SOCIAL.search(url):
            errors.append(f"{where}: {url} is a social-media link")
        elif url not in record:
            errors.append(f"{where}: {url} has no fetch record")
        elif record[url].get("http_status") != 200:
            errors.append(f"{where}: {url} did not answer")
        elif not record[url].get("content_hash") or not record[url].get("retrieved_at"):
            errors.append(f"{where}: {url} has no content hash or no day it was read")

    vendors = doc.get("vendors") or []
    for dup in _dups([v.get("id") for v in vendors]):
        errors.append(f"data market: vendor {dup} is given twice")
    for v in vendors:
        w = f"data market: vendor {v.get('id')}"
        if v.get("role") not in ROLES:
            errors.append(f"{w} has role {v.get('role')}")
        if v.get("evidence") not in EVIDENCE:
            errors.append(f"{w} has evidence {v.get('evidence')}")
        sells = str(v.get("sells") or "").strip()
        if not v.get("name") or not sells:
            errors.append(f"{w} has no name or does not say what it sells")
        elif _figure(sells):
            errors.append(f"{w} types a figure, a size word or an address")
        if not v.get("pages"):
            errors.append(f"{w} cites no fetched page")
        for url in v.get("pages") or []:
            page(w, url)
    ids, themes = {v.get("id") for v in vendors}, doc.get("themes") or {}
    for c in doc.get("board") or []:
        if c.get("theme") not in themes:
            errors.append(f"data market: board column {c.get('theme')} is not a theme")
        if not c.get("label"):
            errors.append(f"data market: board column {c.get('theme')} has no label")
    signals = doc.get("signals") or []
    for dup in _dups([s.get("id") for s in signals]):
        errors.append(f"data market: signal {dup} is given twice")
    for s in signals:
        w = f"data market: signal {s.get('id')}"
        if s.get("theme") not in themes:
            errors.append(f"{w}: {s.get('theme')} is not a theme")
        for k in ("headline", "implies"):
            if not str(s.get(k) or "").strip():
                errors.append(f"{w} has no {k}")
            elif _figure(str(s[k])):
                errors.append(f"{w} types a figure, a size word or an address")
        cited = {e.get("vendor") for e in s.get("evidence") or []}
        if not cited:
            errors.append(f"{w} cites no fetched page")
        for vid in s.get("shown_by") or []:
            if vid not in ids:
                errors.append(f"{w} is shown by {vid}, which is not a vendor")
            elif vid not in cited:
                errors.append(f"{w} is shown by {vid} with no page of its own")
        for e in s.get("evidence") or []:
            page(w, str(e.get("url") or ""))
    prices = doc.get("prices") or []
    for dup in _dups([p.get("id") for p in prices]):
        errors.append(f"data market: price {dup} is given twice")
    for p in prices:
        w = f"data market: price {p.get('id')}"
        if p.get("vendor") not in ids:
            errors.append(f"{w} names {p.get('vendor')}, which is not a vendor")
        if p.get("unit") not in UNITS:
            errors.append(f"{w} has unit {p.get('unit')}")
        if p.get("whose") not in WHOSE:
            errors.append(f"{w} has source kind {p.get('whose')}")
        what = str(p.get("what") or "").strip()
        if not what:
            errors.append(f"{w} does not say what is priced")
        elif _figure(what):
            errors.append(f"{w} types a figure in its description")
        stated = figures(str(p.get("amount") or ""))
        if not stated or not set(stated) <= set(figures(str(p.get("snippet") or ""))):
            errors.append(f"{w} gives a figure its snippet does not state")
        page(w, str(p.get("url") or ""))
    return errors


def build(doc: dict[str, Any], fetched: list[dict[str, Any]]) -> dict[str, Any]:
    """web/data/data_market.json: the vendors with the signals each shows, and the signals most-shown first, each with
    how many vendors show it (weak evidence apart) and the pages, with the day each was read."""
    read = {f["url"]: str(f["retrieved_at"]) for f in fetched}
    vendors = doc.get("vendors") or []
    weak = {v["id"] for v in vendors if v["evidence"] == "weak"}
    name = {v["id"]: v["name"] for v in vendors}
    signals = [
        {
            **{k: s[k] for k in ("id", "theme", "headline", "implies")},
            "shown_by": s["shown_by"],
            "evidenced": len(set(s["shown_by"]) - weak),
            "weak": len(set(s["shown_by"]) & weak),
            "evidence": [
                {
                    "vendor": e["vendor"],
                    "name": name[e["vendor"]],
                    "url": e["url"],
                    "retrieved_at": read[e["url"]],
                }
                for e in s["evidence"]
            ],
        }
        for s in doc.get("signals") or []
    ]
    signals.sort(key=lambda s: (-s["evidenced"], s["id"]))
    top = max((s["evidenced"] for s in signals), default=0) or 1
    themes = doc.get("themes") or {}
    for s in signals:
        s["bar"] = round(100 * s["evidenced"] / top)  # the row's bar, as a share of the most-shown signal
        s["theme_name"] = themes.get(s["theme"], s["theme"])
    listed = [{**v, "signals": [s["id"] for s in signals if v["id"] in s["shown_by"]]} for v in vendors]
    columns = doc.get("board") or []
    theme_of = {s["id"]: s["theme"] for s in signals}
    headline = {s["id"]: s["headline"] for s in signals}

    def row(v: dict[str, Any]) -> dict[str, Any]:
        """A vendor on the board: a mark in each column where a signal of its own sits, and its signals by headline."""
        shows = {theme_of[i] for i in v["signals"]}
        return {
            **{k: v[k] for k in ("id", "name", "sells", "signals", "pages")},
            "n_signals": len(v["signals"]),
            "cells": [c["theme"] in shows for c in columns],
            "shown": [{"id": i, "headline": headline[i]} for i in v["signals"]],
        }

    def group(gid: str, name: str, says: str, keep: Any) -> dict[str, Any]:
        rows = sorted((row(v) for v in listed if keep(v)), key=lambda r: (-r["n_signals"], r["name"].lower()))
        return {"id": gid, "name": name, "says": says, "n": len(rows), "vendors": rows}

    groups = [
        group(
            "evidenced",
            "Sellers with evidence of fast growth",
            "A page read here shows, within the past year, a revenue claim, a funding round, a named model-builder customer or an acquisition.",
            lambda v: v["role"] == "seller" and v["evidence"] == "evidenced",
        ),
        group(
            "weak",
            "Sellers with weak evidence of growth",
            "Their pages show what they sell, but no page read here gives good evidence that they are growing fast.",
            lambda v: v["role"] == "seller" and v["evidence"] == "weak",
        ),
        group(
            "builders",
            "Companies that build models for robots",
            "Buyers and makers of data, not sellers: their pages say what they train on and how they collect it.",
            lambda v: v["role"] == "builder",
        ),
    ]
    prices = [
        {
            **{k: p[k] for k in ("id", "vendor", "what", "amount", "snippet", "url")},
            "name": name[p["vendor"]],
            "whose_name": WHOSE[p["whose"]],
            "retrieved_at": read[p["url"]],
            "unit": p["unit"],
        }
        for p in sorted(doc.get("prices") or [], key=lambda p: (name[p["vendor"]].lower(), p["id"]))
    ]
    price_groups = [
        {"unit": u, "name": n, "rows": [p for p in prices if p["unit"] == u]} for u, n in UNITS.items()
    ]
    price_groups = [{**g, "n": len(g["rows"])} for g in price_groups if g["rows"]]
    made = doc.get("made_by") or {}
    return {
        "made_by": {**made, "date": str(made.get("date"))},
        "disclosure": doc.get("disclosure"),
        "counts": {
            "sellers": sum(v["role"] == "seller" and v["evidence"] == "evidenced" for v in vendors),
            "weak": len(weak),
            "builders": sum(v["role"] == "builder" for v in vendors),
            "signals": len(signals),
            "pages": len({e["url"] for s in signals for e in s["evidence"]}),
            "prices": len(prices),
        },
        "themes": themes,
        "vendors": listed,
        "board": {"columns": columns, "groups": groups},
        "prices": {"groups": price_groups},
        "signals": signals,
    }
