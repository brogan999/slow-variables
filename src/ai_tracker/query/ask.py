"""`ask(question)`: a claude-sonnet-5 tool loop over the semantic layer, with the citation post-check.

Every number in the answer must carry [obs:<id>], [derived:<id>] or [ind:<id>]. After the loop the answer goes
through citecheck; a failing answer gets one revise turn with the failures listed, and is `blocked` if it still fails.
The service never writes: the only tools are read-only SQL over the store and lookups of what the site exports.
"""

from __future__ import annotations

import copy
import difflib
import hashlib
import json
import logging
import math
import os
import re
import threading
from collections import Counter
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml

from .. import store as st
from ..analysis import fits
from ..ingest.scrub import scrub
from .citecheck import CITE, Record, check

log = logging.getLogger("ai-tracker.ask")
MODEL = os.environ.get("QUERY_MODEL", "claude-sonnet-5")
PROMPT_VERSION = "2"
# Sonnet 5 list price (platform pricing page, 11 Sep 2026); cache writes bill at 1.25x input, cache reads at 0.1x
USD_PER_MTOK_IN, USD_PER_MTOK_OUT = (
    float(x) for x in os.environ.get("QUERY_USD_PER_MTOK", "2,10").split(",")
)
AUDIT_KEYS = (
    "time",
    "status",
    "usd",
    "tools",
    "cites",
    "model",
    "prompt_version",
)  # never question or answer text
DOC_DIRS = ("docs/research", "docs/interpretation")  # public notes only; docs/private never ships or indexes
DOC_SKIP = {"BOTTLENECK_PROMPT.md"}  # a prompt addressed to a model: an injection hazard, not evidence
ROW_CAP = 200
READ_ONLY = re.compile(r"^\s*(select|with|describe|show)\b", re.I)
# v2 §6.1: pending and superseded rows (the raw table) never reach an answer; query()/query_table() would reach it by name
RAW = re.compile(r"observation_all|\bquery(_table)?\s*\(", re.I)

TOOLS = [
    {
        "name": "sql",
        "description": "Read-only DuckDB SQL over the semantic layer. Tables: observations (approved, non-superseded rows: id, series_key, subject, entity_id, value_numeric, value_text, value_low, value_high, unit, as_of_date, published_date, source_id, tier, audited_vs_reported, disputed, dispute_text, raw_snippet, url), derived (id, metric, value, value_low, value_high, as_of_date, dims JSON text, obs_ids), status_events (target_type, target_id, old_status, new_status, new_conf, reason, evidence_ids, author, created_at), indicators (id, name, lens, bucket_id, layer_id, unit, metric, band_input, status, confidence, published), metrics (name, description, unit, grain, caveats). Rows are capped at 200; one statement, no writes.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "metric",
        "description": "Latest derived rows for a metric (all dims slices), with the description, unit and caveats from the semantic layer.",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
    {
        "name": "indicator",
        "description": "An indicator's definition, bands or direction rule, current status and reason, latest value and the ids behind it. When band_input.derived_id is set, cite that derived row for the value; it is the slice the bands apply to.",
        "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "changes_since",
        "description": "Status events on or after a date (ISO), newest first.",
        "input_schema": {"type": "object", "properties": {"date": {"type": "string"}}, "required": ["date"]},
    },
    {
        "name": "search_evidence",
        "description": "Keyword search (BM25) over approved observations' snippets, text values and dispute text, and over the tracker's public research notes. Start here when a question names a topic, study, phrase or organisation rather than a metric or indicator. An observation hit carries `cite` to use as [obs:<id>]; a note hit is context only and has no citation, so never state a number that appears only in a note.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "fit_trend",
        "description": "Fit an exponential trend to one observation series (a series_key; a glob must match a single unit) from an optional ISO start date. Returns the doubling time in days (or the halving time for a falling series) with its 95% interval, the point count and R^2, and a one-off derived id to cite as [derived:<id>].",
        "input_schema": {
            "type": "object",
            "properties": {"series": {"type": "string"}, "since": {"type": "string"}},
            "required": ["series"],
        },
    },
    {
        "name": "concordance",
        "description": "The monthly labour trackers behind cross_tracker_concordance: each tracker's indicator, latest reading with its observation id, the fast-band threshold that counts as an AI-attributable break, and whether it is past it; plus the latest concordance row to cite.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "crosswalk",
        "description": "Crosswalk rows linking diffusion buckets to capture layers: relation, note and shared indicators. Optional bucket_id or layer_id filter.",
        "input_schema": {
            "type": "object",
            "properties": {"bucket_id": {"type": "string"}, "layer_id": {"type": "string"}},
        },
    },
    {
        "name": "entity",
        "description": "Look up a company or organisation by id, name or alias: id, CIK, dated layer and sub-layer memberships, and the series recorded for it; close matches when there is no exact hit.",
        "input_schema": {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    },
]
TOOL_NAMES = {t["name"] for t in TOOLS}


def _system(store: st.Store) -> str:
    metrics = (yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {})["metrics"]
    mlines = "\n".join(f"- {k} ({m.get('unit')}): {m.get('description')}" for k, m in metrics.items())
    ilines = "\n".join(
        f"- {i.id} [{'diffusion' if i.bucket_id else 'capture'}{'/capture' if i.bucket_id and i.layer_id else ''}]: {i.name}"
        for i in store.seed.indicators
        if i.published
    )
    return f"""You answer questions about an AI diffusion and value-capture tracker from its own data store. Today is {date.today().isoformat()}.

Method you must respect (from the tracker's methodology page):
- Three layers: observation (raw, sourced, dated) -> derived (a formula over observations) -> indicator (status, confidence, bands). Every number has an observation behind it.
- Evidence tiers 1-7: 1 benchmark, 2 model release, 3 product behaviour, 4 official filing or government statistic, 5 credible reporting, 6 published analysis, 7 an actor's statement about itself. Tier 7 never moves a status above `emerging`. A run-rate reported by the press is never audited.
- Diffusion statuses: consistent_with_normal, faster_than_normal, slower_than_normal, emerging, not_yet_measurable. Capture: concentrating, dispersing, stable, unclear. Fast is not good; concentrating is not good.
- Status lives only in status events, each with a reason, evidence ids and an author.

How to frame an answer (theory organises what the data shows; it is never a source of numbers):
- The value stick: a transaction creates value between what the buyer would pay and what the supplier would accept; each firm captures the slice it can hold against rivals, buyers and suppliers.
- Nordhaus on Schumpeterian profits: innovators keep only a small share of the surplus their innovations create; most of it reaches users as lower prices and better products.
- Teece on profiting from innovation: when imitation is easy, owners of complementary assets (distribution, manufacturing, data, customer relationships) capture the profits rather than the inventor.
- Perez on technological revolutions: an installation period financed by speculative capital ends in a turning point, and a deployment period follows in which the technology spreads through the wider economy.
- Rents come in kinds that migrate as bottlenecks move: scarcity rents on a constrained input, scale and network rents, switching-cost rents, and regulatory rents.
- Evidence grades: A is a tier-1 benchmark or an audited filing or government statistic; B is a company-stated filing, a model release, product behaviour, or published analysis that is not an estimate; C is credible reporting or an estimate; D is a single source or an actor's statement about itself.

Rules for answers:
1. Use the tools to look things up. Never answer a number from memory. If the store has no record, say that it has no record and give no number.
2. Every number you state must be followed by a citation token for the record it comes from: [obs:<id>] for an observation, [derived:<id>] for a derived row, [ind:<id>] for an indicator's band edge or status, [event:<id>] for a number quoted from a status event's reason. Put the token in the same sentence as the number. Years and small counts ("3 of 4 trackers") do not need one, but cite the record anyway when there is one.
3. Render values the way the site does: shares as percentages (0.063 -> 6.3%), USD with k/M/B/T, ratios with x, minutes as hours when over an hour, and name the as-of date and the source tier.
4. Quote a status only with its reason and date. Mention the dispute text when a row is disputed and the tier when it is 7.
5. Be brief: two to five sentences, plain prose, no headings or bullet lists. Do not describe the tools or your process.

Metrics in the semantic layer:
{mlines}

Published indicators:
{ilines}
"""


class Tools:
    """Read-only tool implementations bound to one Store."""

    def __init__(self, store: st.Store) -> None:
        self.store = store
        self.metrics = (yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {})["metrics"]
        self.adhoc: dict[
            str, Record
        ] = {}  # fit_trend rows for one answer; ask() works on a copy, never the shared store
        self.adhoc_href: dict[str, str] = {}
        self._index: dict[str, Any] = {}  # shared by copies: the BM25 index is built once, on first search
        # Model SQL and the public console run on this connection: no file, network or extension access
        # (/proc/self/environ holds the service's secrets), locked so no statement can switch it back.
        # The store's only DuckDB file read (read_json at load) has already run; later reads use pathlib.
        if not store.con.execute("SELECT current_setting('lock_configuration')").fetchone()[0]:
            store.con.execute("SET enable_external_access = false")
            store.con.execute("SET lock_configuration = true")

    def sql(self, query: str) -> Any:
        if not READ_ONLY.match(query) or ";" in query.strip().rstrip(";"):
            return {"error": "read-only: one SELECT/WITH/DESCRIBE/SHOW statement"}
        if RAW.search(query):
            return {
                "error": "observation_all is the raw table (pending and superseded rows); query the observations view"
            }
        q = query.strip().rstrip(";")
        if READ_ONLY.match(q).group(1).lower() in ("select", "with"):
            q = f"SELECT * FROM ({q}) LIMIT {ROW_CAP}"
        cur = self.store.con.cursor()
        timer = threading.Timer(5.0, cur.interrupt)
        timer.start()
        try:
            res = cur.execute(q)
            cols = [d[0] for d in res.description]
            rows = res.fetchall()
        except Exception as e:  # noqa: BLE001 - the model sees the SQL error and retries
            return {"error": str(e)[:500]}
        finally:
            timer.cancel()
            cur.close()
        return {
            "columns": cols,
            "rows": [[_json(v) for v in r] for r in rows],
            "truncated": len(rows) >= ROW_CAP,
        }

    def metric(self, name: str) -> Any:
        rows = self.store.derived_for(name)
        latest: dict[str, Any] = {}
        for d in rows:
            latest[json.dumps(d.dims, sort_keys=True)] = d
        m = self.metrics.get(name) or {}
        return {
            "name": name,
            "description": m.get("description"),
            "unit": m.get("unit"),
            "caveats": m.get("caveats"),
            "latest": [
                {
                    "id": d.id,
                    "dims": d.dims,
                    "as_of": d.as_of_date.isoformat(),
                    "value": d.value,
                    "low": d.value_low,
                    "high": d.value_high,
                    "obs_ids": d.input_observation_ids,
                }
                for d in latest.values()
            ],
            "n_rows": len(rows),
        }

    def indicator(self, id: str) -> Any:
        ind = next((i for i in self.store.seed.indicators if i.id == id), None)
        if not ind:
            return {"error": f"no indicator {id}"}
        ev = self.store.current(id)
        value, as_of, ids, tier = self.store.band_input(ind)
        fit = self.store.band_fit(ind)
        return {
            "id": ind.id,
            "name": ind.name,
            "definition": ind.definition,
            "unit": ind.unit,
            "published": ind.published,
            "bands": {
                "normal": st.dump(ind.normal_band) if ind.normal_band else None,
                "fast": st.dump(ind.fast_band) if ind.fast_band else None,
                "falsifying": st.dump(ind.falsifying_band) if ind.falsifying_band else None,
                "rationale": ind.band_rationale,
            },
            "direction_rule": st.dump(ind.direction_rule) if ind.direction_rule else None,
            "status": {
                "status": ev.new_status,
                "confidence": ev.new_conf,
                "reason": ev.reason,
                "since": ev.created_at.isoformat(),
                "evidence_ids": ev.evidence_ids,
            }
            if ev
            else None,
            "band_input": {
                "value": value,
                "as_of": as_of.isoformat() if as_of else None,
                "obs_ids": ids,
                "best_tier": int(tier),
                "derived_id": fit.id if fit else None,  # the row to cite for this value
                "dims": fit.dims if fit else {},
            },
            "series_keys": ind.series_keys,
            "metric": ind.metric,
            "counterevidence": ind.counterevidence,
        }

    def changes_since(self, date: str) -> Any:
        since = (
            datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
            if "T" not in date
            else datetime.fromisoformat(date)
        )
        evs = sorted(
            (e for e in self.store.events if e.created_at >= since), key=lambda e: e.created_at, reverse=True
        )
        return [st.dump(e) for e in evs[:50]]

    def search_evidence(self, query: str, k: int = 8) -> Any:
        if "bm25" not in self._index:
            self._index["bm25"] = _bm25_index(self._evidence_docs())
        return _bm25_search(self._index["bm25"], query, max(1, min(int(k), 20)))

    def _evidence_docs(self) -> list[dict[str, Any]]:
        docs = []
        for o in self.store.observations("*"):
            text = " ".join(x for x in (o["raw_snippet"], o["value_text"], o["dispute_text"]) if x)
            docs.append(
                {
                    "cite": f"obs:{o['id']}",
                    "series_key": o["series_key"],
                    "as_of": o["as_of_date"].isoformat(),
                    "value": o["value_numeric"],
                    "unit": o["unit"],
                    "text": text,
                }
            )
        for d in DOC_DIRS:
            for f in sorted(Path(d).glob("*.md")) if Path(d).is_dir() else []:
                if f.name in DOC_SKIP:
                    continue
                for n, para in enumerate(re.split(r"\n\s*\n", f.read_text(errors="ignore"))):
                    text, _flagged = scrub(para.strip())
                    if len(text) >= 40:
                        docs.append({"cite": None, "doc": f"{f}#p{n}", "text": text})
        return docs

    def fit_trend(self, series: str, since: str | None = None) -> Any:
        rows = self.store.observations(series)
        rows = [r for r in rows if r["value_numeric"] is not None]
        keys, units = {r["series_key"] for r in rows}, {r["unit"] for r in rows}
        if not rows:
            return {"error": f"no approved numeric rows match {series}"}
        if len(units) > 1:
            return {"error": f"{series} matches several units {sorted(units)}; name one series"}
        start = date.fromisoformat(since) if since else None
        pts = [(r["as_of_date"], r["value_numeric"]) for r in rows]
        fit, kind = fits.loglinear(pts, start), "doubling_days"
        if fit is None:  # a falling series: the doubling time of 1/y is the halving time of y
            fit, kind = fits.loglinear([(d, 1 / v) for d, v in pts if v > 0], start), "halving_days"
        if fit is None:
            return {
                "error": "no exponential trend: fewer than three positive points or no consistent direction"
            }
        used = [
            r["id"] for r in rows if r["value_numeric"] > 0 and (start is None or r["as_of_date"] >= start)
        ]
        rid = "fit-" + hashlib.sha1(f"{series}|{since}|{sorted(used)}".encode()).hexdigest()[:12]
        self.adhoc[rid] = Record(
            rid,
            "derived",
            [x for x in (fit.value, fit.low, fit.high, float(fit.n), fit.r2) if x is not None],
            "days",
        )
        self.adhoc_href[rid] = f"/series/{sorted(keys)[0]}"
        return {
            "id": rid,
            "kind": kind,
            "value_days": round(fit.value, 1),
            "low_days": round(fit.low, 1) if fit.low is not None else None,
            "high_days": round(fit.high, 1) if fit.high is not None else None,
            "n_points": fit.n,
            "r2": round(fit.r2, 3),
            "series_keys": sorted(keys),
            "obs_ids": used,
            "note": "a one-off fit for this answer, not a saved metric; cite it as [derived:<id>]",
        }

    def concordance(self) -> Any:
        m = self.metrics.get("cross_tracker_concordance") or {}
        latest = self.store.derived_for("cross_tracker_concordance")
        trackers = []
        for key in m.get("inputs", []):
            ind = next(
                (i for i in self.store.seed.indicators if any(fnmatch(key, g) for g in i.series_keys)), None
            )
            rows = self.store.observations(key)
            last = rows[-1] if rows else None
            band = ind.fast_band if ind else None
            past = (
                bool(last and band)
                and (band.lo is None or last["value_numeric"] >= band.lo)
                and (band.hi is None or last["value_numeric"] <= band.hi)
            )
            trackers.append(
                {
                    "series_key": key,
                    "indicator": ind.id if ind else None,
                    "latest": {
                        "id": last["id"],
                        "value": last["value_numeric"],
                        "as_of": last["as_of_date"].isoformat(),
                    }
                    if last
                    else None,
                    "fast_band": st.dump(band) if band else None,
                    "past_threshold": past,
                }
            )
        d = latest[-1] if latest else None
        return {
            "description": m.get("description"),
            "concordance": {"id": d.id, "value": d.value, "as_of": d.as_of_date.isoformat()} if d else None,
            "trackers": trackers,
        }

    def crosswalk(self, bucket_id: str | None = None, layer_id: str | None = None) -> Any:
        return [
            st.dump(c)
            for c in self.store.seed.crosswalk
            if (not bucket_id or c.bucket_id == bucket_id) and (not layer_id or c.layer_id == layer_id)
        ]

    def entity(self, name: str) -> Any:
        q = name.strip().lower()
        names = {n.lower(): e for e in self.store.seed.entities for n in (e.id, e.name, *e.aliases)}
        e = names.get(q)
        if not e:
            close = difflib.get_close_matches(q, list(names), n=5, cutoff=0.6)
            close += [n for n in names if q and q in n][:5]
            return {"error": f"no entity {name}", "close_matches": sorted({names[c].id for c in close})}
        series = self.store.con.execute(
            "SELECT DISTINCT series_key FROM observations WHERE entity_id = ? ORDER BY 1 LIMIT 60", [e.id]
        ).fetchall()
        return {
            "id": e.id,
            "name": e.name,
            "aliases": e.aliases,
            "cik": e.cik,
            "memberships": [st.dump(m) for m in e.memberships],
            "series": [r[0] for r in series],
        }

    def records(self, ids: list[tuple[str, str]]) -> dict[str, Record]:
        """Cited records as citecheck needs them: values, CI bounds, band edges, unit and verbatim snippet."""
        out: dict[str, Record] = {i: self.adhoc[i] for k, i in ids if k == "derived" and i in self.adhoc}
        obs = [i for k, i in ids if k == "obs"]
        if obs:
            cur = self.store.con.execute(
                "SELECT id, value_numeric, value_low, value_high, unit, concat_ws(' ', raw_snippet, value_text, dispute_text) FROM observation_all WHERE id IN ("
                + ",".join("?" * len(obs))
                + ")",
                obs,
            )
            for id_, v, lo, hi, unit, snip in cur.fetchall():
                out[id_] = Record(
                    id_, "obs", [x for x in (v, lo, hi) if x is not None], unit or "", snip or ""
                )
        for k, i in ids:
            if k == "derived":
                d = next((d for d in self.store.derived if d.id == i), None)
                if d:
                    m = self.metrics.get(d.metric) or {}
                    out[i] = (
                        Record(  # ponytail: the description's stated thresholds verify too; so would a typical value it quotes
                            i,
                            "derived",
                            [x for x in (d.value, d.value_low, d.value_high) if x is not None],
                            m.get("unit", ""),
                            m.get("description", ""),
                        )
                    )
            elif k == "event":
                e = next((e for e in self.store.events if e.id == i), None)
                if e:
                    out[i] = Record(
                        i,
                        "event",
                        [float(e.new_conf)] + ([float(e.old_conf)] if e.old_conf is not None else []),
                        "",
                        e.reason,
                    )
            elif k == "ind":
                ind = next((x for x in self.store.seed.indicators if x.id == i), None)
                if ind:
                    edges = [
                        b
                        for band in (ind.normal_band, ind.fast_band, ind.falsifying_band)
                        if band
                        for b in (band.lo, band.hi)
                        if b is not None
                    ]
                    ev = self.store.current(i)
                    if ev:
                        edges.append(float(ev.new_conf))
                    if ind.direction_rule:
                        edges += [ind.direction_rule.dead_band, float(ind.direction_rule.periods)]
                    out[i] = Record(i, "ind", edges, ind.unit)
        return out

    def href(self, kind: str, id_: str) -> str | None:
        if kind == "obs":
            r = self.store.con.execute(
                "SELECT series_key FROM observation_all WHERE id = ?", [id_]
            ).fetchone()
            return f"/series/{r[0]}#{id_}" if r else None
        if kind == "derived":
            if id_ in self.adhoc:
                return self.adhoc_href.get(id_)
            d = next((d for d in self.store.derived if d.id == id_), None)
            return f"/query#{d.metric}" if d else None
        if kind == "event":
            e = next((e for e in self.store.events if e.id == id_), None)
            return (
                (
                    f"/predictions#{e.target_id}"
                    if e.target_type == "prediction"
                    else f"/indicators/{e.target_id}"
                )
                if e
                else "/changelog"
            )
        return f"/indicators/{id_}"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _bm25_index(docs: list[dict[str, Any]]) -> dict[str, Any]:
    postings: dict[str, list[tuple[int, int]]] = {}
    lengths = []
    for n, d in enumerate(docs):
        tf = Counter(_tokens(f"{d.get('series_key', '')} {d['text']}"))  # the series key is searchable too
        lengths.append(sum(tf.values()))
        for t, c in tf.items():
            postings.setdefault(t, []).append((n, c))
    return {"docs": docs, "postings": postings, "len": lengths, "avg": sum(lengths) / max(len(lengths), 1)}


def _bm25_search(
    ix: dict[str, Any], query: str, k: int, k1: float = 1.2, b: float = 0.75
) -> list[dict[str, Any]]:
    n = len(ix["docs"])
    scores: Counter[int] = Counter()
    for t in set(_tokens(query)):
        post = ix["postings"].get(t, [])
        idf = math.log(1 + (n - len(post) + 0.5) / (len(post) + 0.5))
        for i, tf in post:
            scores[i] += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * ix["len"][i] / ix["avg"]))
    out = []
    for i, sc in scores.most_common(k):
        d = dict(ix["docs"][i])
        d["text"] = d["text"][:400]
        d["score"] = round(sc, 2)
        out.append(d)
    return out


def _json(v: Any) -> Any:
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, (list, dict, str, int, float, bool)) or v is None:
        return v
    return str(v)


def _run(
    client: Any,
    system: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    tools: Tools,
    usage: dict[str, int],
    calls: list[dict[str, Any]],
) -> str:
    """One pass of the tool loop: keep answering tool calls until the model stops with text."""
    for _ in range(12):
        r = client.messages.create(
            model=MODEL, max_tokens=1200, system=system, tools=TOOLS, messages=messages
        )
        usage["in"] += r.usage.input_tokens
        usage["out"] += r.usage.output_tokens
        usage["cache_write"] += getattr(r.usage, "cache_creation_input_tokens", 0) or 0
        usage["cache_read"] += getattr(r.usage, "cache_read_input_tokens", 0) or 0
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            return "".join(b.text for b in r.content if b.type == "text")
        results = []
        for b in r.content:
            if b.type == "tool_use":
                try:  # an unknown tool or a bad argument is an answer for the model, not a 502 for the reader
                    out = (
                        getattr(tools, b.name)(**b.input)
                        if b.name in TOOL_NAMES
                        else {"error": f"unknown tool {b.name}"}
                    )
                except Exception as e:  # noqa: BLE001
                    out = {"error": f"{type(e).__name__}: {e}"[:300]}
                calls.append({"tool": b.name, "input": b.input})
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": json.dumps(out, default=_json)[:20000],
                    }
                )
        messages.append({"role": "user", "content": results})
    return ""


def ask(store: st.Store, question: str, tools: Tools | None = None, client: Any = None) -> dict[str, Any]:
    import anthropic

    tools = copy.copy(tools or Tools(store))  # shares the store and index; its own one-off fit rows
    tools.adhoc, tools.adhoc_href = {}, {}
    client = client or anthropic.Anthropic()
    system = [{"type": "text", "text": _system(store), "cache_control": {"type": "ephemeral"}}]
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    usage = {"in": 0, "out": 0, "cache_write": 0, "cache_read": 0}
    calls: list[dict[str, Any]] = []
    text = _run(client, system, messages, tools, usage, calls)
    status = "ok"
    res = check(text, tools.records(CITE.findall(text)))
    if not res.ok:
        messages.append(
            {
                "role": "user",
                "content": "Citation check failed:\n"
                + "\n".join(f"- {f}" for f in res.failures)
                + "\nRevise the answer so every number is followed by the citation token of a record that contains it, or drop the number. Reply with the revised answer only.",
            }
        )
        text = _run(client, system, messages, tools, usage, calls)
        res = check(text, tools.records(CITE.findall(text)))
        status = "revised" if res.ok else "blocked"
    if (
        status == "blocked"
    ):  # one fresh attempt: a new conversation often avoids the number that tripped the check
        retry = _run(client, system, [{"role": "user", "content": question}], tools, usage, calls)
        res2 = check(retry, tools.records(CITE.findall(retry)))
        if res2.ok:
            text, res, status = retry, res2, "retried"
    cites = [{"kind": k, "id": i, "href": tools.href(k, i)} for k, i in dict.fromkeys(CITE.findall(text))]
    usd = (
        (usage["in"] + 1.25 * usage["cache_write"] + 0.1 * usage["cache_read"]) * USD_PER_MTOK_IN
        + usage["out"] * USD_PER_MTOK_OUT
    ) / 1e6
    audit = {  # P1 §8 / v2 §6.1: auditable by the records it cited, the model and the prompt; never the text
        "time": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
        "status": status,
        "usd": round(usd, 5),
        "tools": len(calls),
        "cites": [f"{c['kind']}:{c['id']}" for c in cites],
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
    }
    log.info("ask %s", json.dumps(audit, sort_keys=True))
    return {
        "audit": audit,
        "answer": res.annotated if status == "blocked" else text,
        "status": status,
        "citations": cites,
        "checks": {"numbers": res.numbers, "failures": res.failures},
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "usage": {**usage, "usd": round(usd, 5)},
        "tool_calls": calls,
    }


def golden(store: st.Store, tools: Tools | None = None, client: Any = None) -> list[dict[str, Any]]:
    """Run seed/golden.yaml: an answer passes when its citations land on the expected records (or it refuses)."""
    from fnmatch import fnmatch

    tools = tools or Tools(store)
    out = []
    for q in (yaml.safe_load(Path("seed/golden.yaml").read_text()) or {})["questions"]:
        a = ask(store, q["question"], tools, client)
        exp = q["expect"]
        if exp.get("refuse"):
            ok = not a["checks"]["numbers"] and a["status"] != "blocked"
        else:
            cited_series = {
                (
                    tools.store.con.execute(
                        "SELECT series_key FROM observation_all WHERE id = ?", [c["id"]]
                    ).fetchone()
                    or [None]
                )[0]
                for c in a["citations"]
                if c["kind"] == "obs"
            }
            cited_series = {s for s in cited_series if s}
            cited_metrics = {
                d.metric
                for c in a["citations"]
                if c["kind"] == "derived"
                for d in store.derived
                if d.id == c["id"]
            }
            cited_inds = {c["id"] for c in a["citations"] if c["kind"] == "ind"}
            hit = (
                any(fnmatch(s, g) for g in exp.get("series", []) for s in cited_series)
                or bool(cited_metrics & set(exp.get("metrics", [])))
                or bool(cited_inds & set(exp.get("indicators", [])))
            )
            used = {c["tool"] for c in a["tool_calls"]}
            said = a["answer"].lower()
            ok = (
                a["status"] in ("ok", "revised", "retried")
                and hit
                and (not exp.get("tool") or exp["tool"] in used)
                and all(w in said for w in exp.get("mentions", []))  # the answer must say what the number is
            )
        out.append(
            {
                "id": q["id"],
                "ok": ok,
                "informational": bool(q.get("informational")),
                "status": a["status"],
                "answer": a["answer"],
                "citations": a["citations"],
                "usd": a["usage"]["usd"],
            }
        )
    return out
