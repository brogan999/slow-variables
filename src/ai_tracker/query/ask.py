"""`ask(question)`: a claude-sonnet-5 tool loop over the semantic layer, with the citation post-check.

Every number in the answer must carry [obs:<id>], [derived:<id>] or [ind:<id>]. After the loop the answer goes
through citecheck; a failing answer gets one revise turn with the failures listed, and is `blocked` if it still fails.
The service never writes: the only tools are read-only SQL over the store and lookups of what the site exports.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .. import store as st
from .citecheck import CITE, Record, check

log = logging.getLogger("ai-tracker.ask")
MODEL = os.environ.get("QUERY_MODEL", "claude-sonnet-5")
PROMPT_VERSION = "1"
USD_PER_MTOK_IN, USD_PER_MTOK_OUT = (
    float(x) for x in os.environ.get("QUERY_USD_PER_MTOK", "3,15").split(",")
)
ROW_CAP = 200
READ_ONLY = re.compile(r"^\s*(select|with|describe|show)\b", re.I)

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
        "description": "An indicator's definition, bands or direction rule, current status and reason, latest value and the ids behind it.",
        "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "changes_since",
        "description": "Status events on or after a date (ISO), newest first.",
        "input_schema": {"type": "object", "properties": {"date": {"type": "string"}}, "required": ["date"]},
    },
]


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

Rules for answers:
1. Use the tools to look things up. Never answer a number from memory. If the store has no record, say that it has no record and give no number.
2. Every number you state must be followed by a citation token for the record it comes from: [obs:<id>] for an observation, [derived:<id>] for a derived row, [ind:<id>] for an indicator's band edge or status. Put the token in the same sentence as the number. Years and small counts ("3 of 4 trackers") do not need one, but cite the record anyway when there is one.
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

    def sql(self, query: str) -> Any:
        if not READ_ONLY.match(query) or ";" in query.strip().rstrip(";"):
            return {"error": "read-only: one SELECT/WITH/DESCRIBE/SHOW statement"}
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

    def records(self, ids: list[tuple[str, str]]) -> dict[str, Record]:
        """Cited records as citecheck needs them: values, CI bounds, band edges, unit and verbatim snippet."""
        out: dict[str, Record] = {}
        obs = [i for k, i in ids if k == "obs"]
        if obs:
            cur = self.store.con.execute(
                "SELECT id, value_numeric, value_low, value_high, unit, raw_snippet FROM observation_all WHERE id IN ("
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
                    out[i] = Record(
                        i,
                        "derived",
                        [x for x in (d.value, d.value_low, d.value_high) if x is not None],
                        (self.metrics.get(d.metric) or {}).get("unit", ""),
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
            d = next((d for d in self.store.derived if d.id == id_), None)
            return f"/query#{d.metric}" if d else None
        return f"/indicators/{id_}"


def _json(v: Any) -> Any:
    if isinstance(v, (date, datetime)):
        return v.isoformat()
    if isinstance(v, (list, dict, str, int, float, bool)) or v is None:
        return v
    return str(v)


def ask(store: st.Store, question: str, tools: Tools | None = None, client: Any = None) -> dict[str, Any]:
    import anthropic

    tools = tools or Tools(store)
    client = client or anthropic.Anthropic()
    system = [{"type": "text", "text": _system(store), "cache_control": {"type": "ephemeral"}}]
    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    usage = {"in": 0, "out": 0}
    calls: list[dict[str, Any]] = []
    text = ""
    for _ in range(12):
        r = client.messages.create(
            model=MODEL, max_tokens=1200, system=system, tools=TOOLS, messages=messages
        )
        usage["in"] += r.usage.input_tokens
        usage["out"] += r.usage.output_tokens
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            text = "".join(b.text for b in r.content if b.type == "text")
            break
        results = []
        for b in r.content:
            if b.type == "tool_use":
                out = getattr(tools, b.name)(**b.input)
                calls.append({"tool": b.name, "input": b.input})
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": b.id,
                        "content": json.dumps(out, default=_json)[:20000],
                    }
                )
        messages.append({"role": "user", "content": results})
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
        r = client.messages.create(
            model=MODEL, max_tokens=1200, system=system, tools=TOOLS, messages=messages
        )
        usage["in"] += r.usage.input_tokens
        usage["out"] += r.usage.output_tokens
        text = "".join(b.text for b in r.content if b.type == "text")
        res = check(text, tools.records(CITE.findall(text)))
        status = "revised" if res.ok else "blocked"
    cites = [{"kind": k, "id": i, "href": tools.href(k, i)} for k, i in dict.fromkeys(CITE.findall(text))]
    usd = usage["in"] * USD_PER_MTOK_IN / 1e6 + usage["out"] * USD_PER_MTOK_OUT / 1e6
    log.info(
        "ask %s status=%s usd=%.4f tools=%d",
        hashlib.sha1(question.encode()).hexdigest()[:8],
        status,
        usd,
        len(calls),
    )
    return {
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
                tools.store.con.execute(
                    "SELECT series_key FROM observation_all WHERE id = ?", [c["id"]]
                ).fetchone()[0]
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
            ok = a["status"] in ("ok", "revised") and hit
        out.append(
            {
                "id": q["id"],
                "ok": ok,
                "status": a["status"],
                "answer": a["answer"],
                "citations": a["citations"],
                "usd": a["usage"]["usd"],
            }
        )
    return out
