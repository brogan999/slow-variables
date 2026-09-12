"""Seed YAML + data/*.jsonl -> in-memory DuckDB; export -> web/data/*.json. The web never computes a number."""

from __future__ import annotations

import csv
import json
import math
import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import duckdb
import yaml

from .schema import (
    UNVOTED,
    Bottleneck,
    Bucket,
    CompareRow,
    Crosswalk,
    Derived,
    Entity,
    Essay,
    FetchLog,
    Indicator,
    Layer,
    Membership,
    Observation,
    Prediction,
    Review,
    SkippedSource,
    Source,
    StatusEvent,
    Sublayer,
    Tier,
)

SEED, DATA, WEB = Path("seed"), Path("data"), Path("web/data")
Path = Path  # re-exported for cli
OBS = DATA / "observations"

# Every venture metric reads rounds from this one view: Form D equity and debt, and Epoch's equity rounds for an
# entity-quarter with no Form D filing (Form D is tier 4, Epoch tier 5; the better source wins the quarter).
VENTURE_ROUNDS = """CREATE OR REPLACE VIEW venture_rounds AS
WITH f AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'formd' AS source, 'equity' AS kind FROM observations
           WHERE series_key LIKE 'formd.%.amount_sold_usd.pt' AND entity_id IS NOT NULL),
d AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'formd' AS source, 'debt' AS kind FROM observations
      WHERE series_key LIKE 'formd.%.debt_sold_usd.pt' AND entity_id IS NOT NULL),
e AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'epoch' AS source, 'equity' AS kind FROM observations
      WHERE series_key LIKE 'epoch.%.round_equity_usd.pt' AND entity_id IS NOT NULL)
SELECT * FROM f UNION ALL SELECT * FROM d
UNION ALL SELECT * FROM e WHERE NOT EXISTS (
  SELECT 1 FROM f WHERE f.entity_id = e.entity_id AND date_trunc('quarter', f.as_of_date) = date_trunc('quarter', e.as_of_date))"""
OBS_COLUMNS = {
    "id": "VARCHAR",
    "series_key": "VARCHAR",
    "unit": "VARCHAR",
    "as_of_date": "DATE",
    "published_date": "DATE",
    "retrieved_at": "VARCHAR",
    "url": "VARCHAR",
    "content_hash": "VARCHAR",
    "http_status": "INTEGER",
    "source_id": "VARCHAR",
    "tier": "INTEGER",
    "audited_vs_reported": "VARCHAR",
    "extraction_method": "VARCHAR",
    "extractor_version": "VARCHAR",
    "raw_snippet": "VARCHAR",
    "value_numeric": "DOUBLE",
    "value_text": "VARCHAR",
    "value_low": "DOUBLE",
    "value_high": "DOUBLE",
    "period_start": "DATE",
    "entity_id": "VARCHAR",
    "run_rate_vs_booked": "VARCHAR",
    "gross_vs_net": "VARCHAR",
    "disputed": "BOOLEAN",
    "dispute_text": "VARCHAR",
    "note": "VARCHAR",
    "review_status": "VARCHAR",
    "reviewer_id": "VARCHAR",
    "supersedes_id": "VARCHAR",
}


def read_jsonl(p: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()] if p.exists() else []


def write_jsonl(p: Path, rows: list[dict[str, Any]]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("".join(json.dumps(r, sort_keys=True, default=str) + "\n" for r in rows))


def dump(m: Any) -> dict[str, Any]:
    return json.loads(m.model_dump_json())


@dataclass
class Seed:
    buckets: list[Bucket]
    layers: list[Layer]
    sublayers: list[Sublayer]
    crosswalk: list[Crosswalk]
    sources: list[Source]
    indicators: list[Indicator]
    entities: list[Entity]
    predictions: list[Prediction]
    bottlenecks: list[Bottleneck] = field(default_factory=list)
    essays: list[Essay] = field(default_factory=list)
    sections: list[dict[str, str]] = field(default_factory=list)
    compare: list[CompareRow] = field(default_factory=list)
    skipped: list[SkippedSource] = field(default_factory=list)

    @classmethod
    def load(cls, root: Path = SEED) -> Seed:
        def rows(name: str) -> list[dict[str, Any]]:
            return yaml.safe_load((root / f"{name}.yaml").read_text())[name]

        inds = [
            Indicator(**r)
            for f in sorted((root / "indicators").glob("*.yaml"))
            for r in yaml.safe_load(f.read_text())["indicators"]
        ]
        bn = (
            yaml.safe_load((root / "bottlenecks.yaml").read_text())
            if (root / "bottlenecks.yaml").exists()
            else {}
        )
        cmp_ = yaml.safe_load((root / "compare.yaml").read_text()) if (root / "compare.yaml").exists() else {}
        crosswalk = [  # shared indicators follow from the indicators' own two addresses, never a hand list
            Crosswalk(
                **{
                    **r,
                    "shared_indicators": [
                        i.id
                        for i in inds
                        if i.bucket_id == r["bucket_id"]
                        and i.layer_id == r["layer_id"]
                        and (not r.get("sublayer_id") or i.sublayer_id == r["sublayer_id"])
                    ],
                }
            )
            for r in rows("crosswalk")
        ]
        return cls(
            [Bucket(**r) for r in rows("buckets")],
            [Layer(**r) for r in rows("layers")],
            [Sublayer(**r) for r in rows("sublayers")],
            crosswalk,
            [Source(**r) for r in rows("sources")],
            inds,
            [Entity(**r) for r in rows("entities")],
            [Prediction(**r) for r in rows("predictions")] if (root / "predictions.yaml").exists() else [],
            [Bottleneck(**r) for r in bn.get("bottlenecks", [])],
            [Essay(**r) for r in bn.get("essays", [])],
            bn.get("sections", []),
            [CompareRow(**r) for r in cmp_.get("rows", [])],
            [
                SkippedSource(**r)
                for r in yaml.safe_load((root / "sources.yaml").read_text()).get("skipped") or []
            ],
        )


FLAG_FIELDS = ("disputed", "dispute_text", "gross_vs_net", "run_rate_vs_booked", "note")


def append_observations(source_id: str, rows: list[Observation]) -> int:
    """Append-only, sorted by id. A changed value for the same key gets a new row that supersedes the old one."""
    p = OBS / f"{source_id}.jsonl"
    existing = read_jsonl(p)
    # other files count too: a connector that continues a hand-entered series (Ramp) supersedes the manual row for the
    # same key and date instead of standing beside it
    others = [r for f in sorted(OBS.glob("*.jsonl")) if f != p for r in read_jsonl(f)]
    ids = {r["id"] for r in existing + others}
    across: dict[
        tuple[Any, ...], tuple[str, str]
    ] = {}  # other files: the series key already names the subject
    for r in others:
        k = (r["series_key"], r["as_of_date"], r.get("period_start"))
        if not r["series_key"].startswith("watch.") and (k not in across or r["retrieved_at"] > across[k][1]):
            across[k] = (r["id"], r["retrieved_at"])
    latest: dict[tuple[Any, ...], tuple[str, str]] = {}
    for r in existing:
        k = (
            r["series_key"],
            r.get("entity_id"),
            r["as_of_date"],
            r.get("period_start"),
            r["url"] if r["series_key"].startswith("watch.") else None,
        )
        if k not in latest or r["retrieved_at"] > latest[k][1]:
            latest[k] = (r["id"], r["retrieved_at"])
    new: list[dict[str, Any]] = []
    own = {r["id"]: r for r in existing}
    touched = False
    for o in rows:
        if o.id in own:  # a corrected annotation rewrites only flag fields: never value, snippet, URL or id
            d, cur = dump(o), own[o.id]
            if cur.get("review_status") == Review.rejected.value:
                continue  # withdrawn in place: its dispute text is the public reason and stays
            if any(cur.get(k) != d.get(k) for k in FLAG_FIELDS):
                cur.update({k: d.get(k) for k in FLAG_FIELDS})
                touched = True
            continue
        if o.id in ids:
            continue
        k = (
            o.series_key,
            o.entity_id,
            o.as_of_date.isoformat(),
            o.period_start.isoformat() if o.period_start else None,
            o.url if o.series_key.startswith("watch.") else None,  # several posts per author per day
        )
        if k in latest:
            o.supersedes_id = latest[k][0]
        elif (k[0], k[2], k[3]) in across:
            o.supersedes_id = across[(k[0], k[2], k[3])][0]
        latest[k] = (o.id, o.retrieved_at.isoformat())
        ids.add(o.id)
        new.append(dump(o))
    if new or touched:
        write_jsonl(p, sorted(existing + new, key=lambda r: r["id"]))
    return len(new)


def append_fetchlog(log: FetchLog) -> None:
    p = DATA / "fetchlog.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(dump(log), sort_keys=True) + "\n")


def approve_pending(reviewer: str = "merge") -> int:
    n = 0
    for p in sorted(OBS.glob("*.jsonl")):
        rows = read_jsonl(p)
        for r in rows:
            if r["review_status"] == Review.pending.value:
                r["review_status"], r["reviewer_id"] = Review.approved.value, reviewer
                n += 1
        write_jsonl(p, rows)
    return n


class Store:
    def __init__(self, seed: Seed | None = None) -> None:
        self.seed = seed or Seed.load()
        self._db = duckdb.connect()
        self._local = threading.local()
        cols = ", ".join(f"'{k}': '{v}'" for k, v in OBS_COLUMNS.items())
        files = sorted(OBS.glob("*.jsonl"))
        if files:
            self.con.execute(
                f"CREATE TABLE observation_all AS SELECT * FROM read_json('{OBS}/*.jsonl', "
                f"format='newline_delimited', columns={{{cols}}})"
            )
        else:
            self.con.execute(
                "CREATE TABLE observation_all (" + ", ".join(f"{k} {v}" for k, v in OBS_COLUMNS.items()) + ")"
            )
        self.con.execute("""CREATE VIEW observations AS
            SELECT *, split_part(series_key, '.', 2) AS subject, date_trunc('quarter', as_of_date) AS q
            FROM observation_all o
            WHERE review_status = 'approved' AND NOT EXISTS (SELECT 1 FROM observation_all s WHERE s.supersedes_id = o.id)""")
        self.con.execute(
            "CREATE TABLE entity_membership (entity_id VARCHAR, layer_id VARCHAR, sublayer_id VARCHAR, "
            "is_primary BOOLEAN, from_date DATE, to_date DATE)"
        )
        self.con.executemany(
            "INSERT INTO entity_membership VALUES (?, ?, ?, ?, ?, ?)",
            [
                (e.id, m.layer_id, m.sublayer_id, m.is_primary, m.from_date, m.to_date)
                for e in self.seed.entities
                for m in e.memberships
            ]
            or [("", "", None, True, None, None)],
        )
        if not any(e.memberships for e in self.seed.entities):
            self.con.execute("DELETE FROM entity_membership")
        self.con.execute(VENTURE_ROUNDS)
        self.derived = [Derived(**r) for r in read_jsonl(DATA / "derived.jsonl")]
        self.events = [StatusEvent(**r) for r in read_jsonl(DATA / "status_events.jsonl")]
        self.fetchlog = [FetchLog(**r) for r in read_jsonl(DATA / "fetchlog.jsonl")]
        self.semantic_tables()


    @property
    def con(self) -> duckdb.DuckDBPyConnection:
        """This thread's cursor on the store's database. One DuckDB connection is not safe to share across
        threads, and the query service answers each request on its own thread; a cursor per thread is."""
        c = getattr(self._local, "con", None)
        if c is None:
            c = self._local.con = self._db.cursor()
        return c

    def semantic_tables(self) -> None:
        """DuckDB tables for the query layer: derived, status_events, indicators, metrics. Re-run after derived changes."""
        con = self.con
        con.execute(
            "CREATE OR REPLACE TABLE derived (id VARCHAR, metric VARCHAR, value DOUBLE, value_low DOUBLE, value_high DOUBLE, as_of_date DATE, dims VARCHAR, obs_ids VARCHAR[])"
        )
        con.executemany(
            "INSERT INTO derived VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    d.id,
                    d.metric,
                    d.value,
                    d.value_low,
                    d.value_high,
                    d.as_of_date,
                    json.dumps(d.dims, sort_keys=True),
                    d.input_observation_ids,
                )
                for d in self.derived
            ]
            or [(None,) * 8],
        )
        con.execute(
            "CREATE OR REPLACE TABLE status_events (id VARCHAR, target_type VARCHAR, target_id VARCHAR, old_status VARCHAR, new_status VARCHAR, old_conf INTEGER, new_conf INTEGER, reason VARCHAR, evidence_ids VARCHAR[], author VARCHAR, created_at TIMESTAMP)"
        )
        con.executemany(
            "INSERT INTO status_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    e.id,
                    e.target_type,
                    e.target_id,
                    e.old_status,
                    e.new_status,
                    e.old_conf,
                    e.new_conf,
                    e.reason,
                    e.evidence_ids,
                    e.author,
                    _utc_naive(e.created_at),  # stored as UTC; DuckDB fetches TIMESTAMPTZ only with pytz
                )
                for e in self.events
            ]
            or [(None,) * 11],
        )
        con.execute(
            "CREATE OR REPLACE TABLE indicators (id VARCHAR, name VARCHAR, lens VARCHAR, bucket_id VARCHAR, layer_id VARCHAR, sublayer_id VARCHAR, unit VARCHAR, metric VARCHAR, band_input VARCHAR, status VARCHAR, confidence INTEGER, published BOOLEAN)"
        )
        con.executemany(
            "INSERT INTO indicators VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    i.id,
                    i.name,
                    "both" if i.bucket_id and i.layer_id else "diffusion" if i.bucket_id else "capture",
                    i.bucket_id,
                    i.layer_id,
                    i.sublayer_id,
                    i.unit,
                    i.metric,
                    i.band_input,
                    ev.new_status if ev else None,
                    ev.new_conf if ev else None,
                    i.published,
                )
                for i in self.seed.indicators
                for ev in [self.current(i.id)]
            ],
        )
        spec = (
            (yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {}).get("metrics", {})
            if Path("semantic/metrics.yaml").exists()
            else {}
        )
        con.execute(
            "CREATE OR REPLACE TABLE metrics (name VARCHAR, description VARCHAR, unit VARCHAR, grain VARCHAR, lead_lag VARCHAR, caveats VARCHAR, formula VARCHAR)"
        )
        con.executemany(
            "INSERT INTO metrics VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    k,
                    m.get("description"),
                    m.get("unit"),
                    ",".join(m.get("grain", [])),
                    m.get("lead_lag"),
                    m.get("caveats"),
                    "\n".join(x for x in (m.get("python") and f"python: {m['python']}", m.get("sql")) if x),
                )
                for k, m in spec.items()
            ]
            or [(None,) * 7],
        )
        for t in ("derived", "status_events", "metrics"):
            con.execute(f"DELETE FROM {t} WHERE {'id' if t != 'metrics' else 'name'} IS NULL")

    # ---- queries -------------------------------------------------------------------------------------------
    def observations(self, *globs: str) -> list[dict[str, Any]]:
        cur = self.con.execute("SELECT * FROM observations ORDER BY as_of_date, series_key, id")
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        return [r for r in rows if any(fnmatch(r["series_key"], g) for g in globs)]

    def derived_for(self, metric: str, dims: dict[str, str] | None = None) -> list[Derived]:
        return sorted(
            (
                d
                for d in self.derived
                if d.metric == metric and all(d.dims.get(k) == v for k, v in (dims or {}).items())
            ),
            key=lambda d: (d.as_of_date, sorted(d.dims.items())),
        )

    def current(self, indicator_id: str) -> StatusEvent | None:
        evs = [e for e in self.events if e.target_id == indicator_id]
        return max(evs, key=lambda e: e.created_at) if evs else None

    def band_fit(self, ind: Indicator) -> Derived | None:
        """The derived row the bands were applied to, when the band input is a metric (carries the CI)."""
        if ind.band_input and ind.band_input.startswith("metric:"):
            rows = self.derived_for(ind.band_input[7:], ind.metric_dims)
            return rows[-1] if rows else None
        return None

    def band_input(self, ind: Indicator) -> tuple[float | None, date | None, list[str], Tier]:
        """Latest value the bands apply to, its obs ids, and the best (lowest) tier behind it."""
        if not ind.band_input:
            return None, None, [], Tier.ACTOR_STATEMENT
        if ind.band_input.startswith("metric:"):
            rows = self.derived_for(ind.band_input[7:], ind.metric_dims)
            if not rows:
                return None, None, [], Tier.ACTOR_STATEMENT
            d = rows[-1]
            return d.value, d.as_of_date, d.input_observation_ids, self._best_tier(d.input_observation_ids)
        obs = self.observations(ind.band_input)
        if not obs:
            return None, None, [], Tier.ACTOR_STATEMENT
        o = obs[-1]
        return o["value_numeric"], o["as_of_date"], [o["id"]], Tier(o["tier"])

    def band_interval(self, ind: Indicator) -> tuple[float | None, float | None]:
        """The interval around the band input, where the fit or the source published one."""
        if not ind.band_input:
            return None, None
        if ind.band_input.startswith("metric:"):
            rows = self.derived_for(ind.band_input[7:], ind.metric_dims)
            return (rows[-1].value_low, rows[-1].value_high) if rows else (None, None)
        obs = self.observations(ind.band_input)
        return (obs[-1]["value_low"], obs[-1]["value_high"]) if obs else (None, None)

    def evidence_obs(self, ind: Indicator) -> list[dict[str, Any]]:
        """Observations behind an indicator: its series globs plus the inputs of its derived metric."""
        rows = {o["id"]: o for g in ind.series_keys for o in self.observations(g)}
        if ind.metric:
            ids = sorted(
                {i for d in self.derived_for(ind.metric, ind.metric_dims) for i in d.input_observation_ids}
            )
            if ids:
                cur = self.con.execute(
                    "SELECT * FROM observations WHERE id IN (" + ",".join("?" * len(ids)) + ")", ids
                )
                cols = [c[0] for c in cur.description]
                rows.update({r[0]: dict(zip(cols, r)) for r in cur.fetchall()})
        return list(rows.values())

    def _best_tier(self, ids: list[str]) -> Tier:
        if not ids:
            return Tier.ACTOR_STATEMENT
        q = "SELECT min(tier) FROM observation_all WHERE id IN (" + ",".join("?" * len(ids)) + ")"
        t = self.con.execute(q, ids).fetchone()
        return Tier(t[0]) if t and t[0] else Tier.ACTOR_STATEMENT

    def headline(self, ind: Indicator) -> list[dict[str, Any]]:
        """Points for the indicator's chart: derived metric if set, else observations of the first series glob."""
        if ind.metric:
            return [
                {
                    "as_of": d.as_of_date.isoformat(),
                    "value": d.value,
                    "obs_ids": d.input_observation_ids,
                    "dims": d.dims,
                    "unit": ind.unit,
                }
                for d in self.derived_for(ind.metric, ind.metric_dims)
            ]
        if not ind.series_keys:
            return []
        return [_point(o) for o in self.observations(ind.series_keys[0])]

    # ---- export --------------------------------------------------------------------------------------------
    def export(self, out: Path = WEB) -> None:
        out.mkdir(parents=True, exist_ok=True)
        for sub in ("indicators", "series", "buckets", "layers", "lens"):
            (out / sub).mkdir(exist_ok=True)
        cards = {i.id: self._card(i) for i in self.seed.indicators}
        for ind in self.seed.indicators:
            series = {}
            for g in ind.series_keys:
                for o in self.observations(g):
                    series.setdefault(o["series_key"], []).append(_point(o))
            ev = sorted(
                (e for e in self.events if e.target_id == ind.id), key=lambda e: e.created_at, reverse=True
            )
            bv, b_as_of, b_ids, _ = self.band_input(ind)
            doc = {
                **_jsonable(ind.model_dump()),
                **cards[ind.id],
                "points": self.headline(ind),
                "band_value": {
                    "value": bv,
                    "as_of": b_as_of.isoformat() if b_as_of else None,
                    "obs_ids": b_ids,
                    "low": fit.value_low if (fit := self.band_fit(ind)) else None,
                    "high": fit.value_high if fit else None,
                }
                if bv is not None
                else None,
                "fits": [
                    {**dump(r[-1]), "obs_ids": r[-1].input_observation_ids}
                    for m in ind.related_metrics
                    if (r := self.derived_for(m, ind.metric_dims))
                ],
                "series": [{"series_key": k, "points": v} for k, v in sorted(series.items())],
                "chart_sources": self._chart_sources(
                    [i for p in self.headline(ind) for i in p["obs_ids"]], ind.metric
                ),
                "confidence_basis": {
                    **self._confidence_basis(ind),
                    "stale_as_of": cards[ind.id]["stale_as_of"],
                },
                "prediction_rows": [
                    {
                        "id": p.id,
                        "claimant": p.claimant,
                        "ledger": p.ledger,
                        "status": (pe.new_status if (pe := self.current(p.id)) else None),
                    }
                    for p in self.seed.predictions
                    if p.published and ind.id in p.related_indicators
                ],
                "derived": [
                    {**dump(d), "obs_ids": d.input_observation_ids}
                    for d in self.derived_for(ind.metric, ind.metric_dims)
                ]
                if ind.metric
                else [],
                "status_events": [dump(e) for e in ev],
                "crosswalk": [
                    dump(c)
                    for c in self.seed.crosswalk
                    if ind.id in c.shared_indicators
                    or c.bucket_id == ind.bucket_id
                    and c.layer_id == ind.layer_id
                ],
            }
            doc["evidence"] = self.evidence_for(ind.id)
            doc["related_bottlenecks"] = sorted(
                set(ind.related_bottlenecks)
                | {b.id for b in self.seed.bottlenecks if ind.id in b.related_indicators}
            )
            _write(out / "indicators" / f"{ind.id}.json", doc)
        live, withdrawn = self._all_series(), self._withdrawn()
        for key in sorted(live.keys() | withdrawn.keys()):
            rows = live.get(key, [])
            first = rows[0] if rows else withdrawn[key][0]
            src = next((s for s in self.seed.sources if s.id == first["source_id"]), None)
            _write(
                out / "series" / f"{key}.json",
                {
                    "series_key": key,
                    "unit": first["unit"],
                    "source": dump(src) if src else None,
                    "observations": [_full(o) for o in rows],
                    "withdrawn": withdrawn.get(key, []),
                },
            )
            (out.parent / "public" / "data").mkdir(parents=True, exist_ok=True)
            with (out.parent / "public" / "data" / f"{key}.csv").open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(OBS_COLUMNS))
                w.writeheader()
                for o in rows:
                    w.writerow({k: o.get(k) for k in OBS_COLUMNS})
        for b in self.seed.buckets:
            _write(
                out / "buckets" / f"{b.id}.json",
                {
                    **dump(b),
                    "indicators": [
                        cards[i.id] for i in self.seed.indicators if i.bucket_id == b.id and i.published
                    ],
                    "crosswalk": [dump(c) for c in self.seed.crosswalk if c.bucket_id == b.id],
                },
            )
        for layer in self.seed.layers:
            _write(
                out / "layers" / f"{layer.id}.json",
                {
                    **dump(layer),
                    "sublayers": [dump(s) for s in self.seed.sublayers if s.layer_id == layer.id],
                    "indicators": [
                        cards[i.id] for i in self.seed.indicators if i.layer_id == layer.id and i.published
                    ],
                    "crosswalk": [dump(c) for c in self.seed.crosswalk if c.layer_id == layer.id],
                    "venture": self._layer_venture(layer.id),
                    "commoditisation": self._commoditisation(cards) if layer.id == "model" else None,
                },
            )
        recent = [dump(e) for e in sorted(self.events, key=lambda e: e.created_at, reverse=True)[:3]]

        def as_of(cs: list[dict[str, Any]]) -> str:
            m = max([c["latest"]["as_of"] for c in cs if c["latest"] and c["published"]] or [""])
            return (
                min(m, date.today().isoformat()) if m else m
            )  # a quarter still in progress is labelled by its end

        as_of_d = as_of([cards[i.id] for i in self.seed.indicators if i.bucket_id])
        as_of_c = as_of([cards[i.id] for i in self.seed.indicators if i.layer_id])
        _write(out / "lens" / "diffusion.json", self._diffusion_lens(cards, recent, as_of_d))
        _write(
            out / "lens" / "capture.json",
            {
                "as_of": as_of_c,
                "verdict": "As of %s: " % as_of_c
                + ", ".join(_clause(self._capture_layer(layer, cards)) for layer in self.seed.layers)
                + ".",
                "what_would_change": [
                    f"{i.name}: {i.direction_rule.rationale}"
                    for i in self.seed.indicators
                    if i.published and i.layer_id and i.direction_rule
                ],
                "recent_status_events": recent,
                "stack_bars": self._stack_bars(),
                "gross_profit_stack_series": [
                    {
                        "as_of": d.as_of_date.isoformat(),
                        "layer_id": d.dims.get("layer_id"),
                        "basis": d.dims.get("basis"),
                        "value": d.value,
                        "obs_ids": d.input_observation_ids,
                    }
                    for d in self.derived_for("gross_profit_share_by_layer")
                ],
                "gross_profit_stack_sources": self._chart_sources(
                    [
                        i
                        for d in self.derived_for("gross_profit_share_by_layer")
                        for i in d.input_observation_ids
                    ],
                    "gross_profit_share_by_layer",
                ),
                "margin_stack_sources": self._chart_sources(
                    [
                        i
                        for d in self.derived_for("margin_stack_share_by_layer")
                        for i in d.input_observation_ids
                    ],
                    "margin_stack_share_by_layer",
                ),
                "margin_stack_series": [
                    {
                        "as_of": d.as_of_date.isoformat(),
                        "layer_id": d.dims.get("layer_id"),
                        "value": d.value,
                        "obs_ids": d.input_observation_ids,
                    }
                    for d in self.derived_for("margin_stack_share_by_layer")
                ],
                "layers": [self._capture_layer(layer, cards) for layer in self.seed.layers],
            },
        )
        _write(
            out / "index.json",
            {
                "indicators": list(cards.values()),
                "buckets": [dump(b) for b in self.seed.buckets],
                "layers": [dump(x) for x in self.seed.layers],
                "sublayers": [dump(s) for s in self.seed.sublayers],
                "crosswalk": [dump(c) for c in self.seed.crosswalk],
            },
        )
        _write(out / "obs_index.json", {o["id"]: o["series_key"] for o in self.observations("*")})
        _write(
            out / "predictions.json",
            [
                {
                    **_jsonable(pr.model_dump()),
                    "evidence": self.evidence_for(pr.id, *pr.related_indicators),
                    "status": (ev.new_status if (ev := self.current(pr.id)) else None),
                    "confidence_now": ev.new_conf if ev else None,
                    "status_events": [
                        dump(e)
                        for e in sorted(
                            (e for e in self.events if e.target_id == pr.id),
                            key=lambda e: e.created_at,
                            reverse=True,
                        )
                    ],
                }
                for pr in self.seed.predictions
            ],
        )
        _write(out / "ledger.json", self._ledger())
        _write(out / "stack.json", self._stack(cards))
        _write(out / "lens" / "ladder.json", self._ladder())
        _write(out / "analyses.json", self._analyses())
        from .memo import load_memos

        memos = load_memos()
        (out / "memos").mkdir(parents=True, exist_ok=True)
        for m in memos:
            _write(out / "memos" / f"{m['date']}.json", m)
        _write(
            out / "memos" / "index.json",
            [
                {k: v for k, v in m.items() if k != "body"} | {"summary": m["body"].split("\n\n")[0][:400]}
                for m in reversed(memos)
            ],
        )
        (out / "venture").mkdir(parents=True, exist_ok=True)
        for sub_id, doc in self._venture().items():
            _write(out / "venture" / f"{sub_id}.json", doc)
        _write(out / "bottlenecks.json", self._bottlenecks(cards))
        _write(out / "compare.json", self._compare(cards))
        _write(out / "thesis.json", read_jsonl(DATA / "thesis.jsonl"))
        _write(out / "sources.json", [self._source_health(s) for s in self.seed.sources])
        _write(out / "skipped_sources.json", [dump(s) for s in self.seed.skipped])
        _write(
            out / "changelog.json",
            [dump(e) for e in sorted(self.events, key=lambda e: e.created_at, reverse=True)],
        )
        self._write_docs(Path(".") if out == WEB else out / "_repo")
        (out / "meta.json").write_text(
            json.dumps(
                {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "observations": self.con.execute("SELECT count(*) FROM observations").fetchone()[0],
                    "indicators_published": sum(1 for i in self.seed.indicators if i.published),
                    "sources": len(self.seed.sources),
                }
            )
            + "\n"
        )

    def _card(self, ind: Indicator) -> dict[str, Any]:
        pts = self.headline(ind)
        ev = self.current(ind.id)
        latest = pts[-1] if pts else None
        ev_obs = self.evidence_obs(ind)
        stale = None
        if latest and ind.cadence_expected in CADENCE_DAYS:
            age = (date.today() - date.fromisoformat(latest["as_of"])).days
            if age > max(
                2 * CADENCE_DAYS[ind.cadence_expected], CADENCE_DAYS[ind.cadence_expected] + 30
            ):  # allow a publication lag
                stale = latest["as_of"]
        return {
            "id": ind.id,
            "name": ind.name,
            "bucket_id": ind.bucket_id,
            "layer_id": ind.layer_id,
            "valve_measured": ind.valve_measured,
            "unpublished_reason": ind.unpublished_reason,
            "unit": ind.unit,
            "published": ind.published,
            "status": ev.new_status if ev else None,
            "confidence": ev.new_conf if ev else None,
            "leading_lagging": ind.leading_lagging.value if ind.leading_lagging else None,
            "source_cluster": ind.source_cluster,
            "grade": _best_grade(ev_obs),
            "latest": latest,
            "sparkline": pts[-24:],
            "stale_as_of": None if ind.stale_ok else stale,
            "stale_reason": ind.stale_reason,
            "pending": self._awaiting().get(ind.id),
            "n_observations": len(self.evidence_obs(ind)),
            "answers": self._answers(ind),
        }

    def _confidence_basis(self, ind: Indicator) -> dict[str, Any]:
        """What the confidence number rests on, computed here so the page only lists it (v2 §4.2 L2)."""
        obs = self.evidence_obs(ind)
        names = {x.id: x.name for x in self.seed.sources}
        tiers = [Tier(o["tier"]) for o in obs]
        return {
            "grade": _best_grade(obs),
            "best_tier": int(min(tiers)) if tiers else None,
            "sources": sorted({names.get(o["source_id"], o["source_id"]) for o in obs}),
            "n_observations": len(obs),
        }

    def _answers(self, ind: Indicator) -> list[str]:
        """v2 §4.2 L1: the one line a card carries on which valve or which capture question it answers."""
        valves = {v["id"]: v["name"] for v in VALVES}
        buckets = {b.id: b.name for b in self.seed.buckets}
        layers = {x.id: x.name for x in self.seed.layers}
        subs = {x.id: x.name for x in self.seed.sublayers}
        out = []
        if ind.bucket_id:
            out.append(
                f"Valve: {valves[ind.valve_measured]}"
                if ind.valve_measured in valves
                else f"Bucket: {buckets.get(ind.bucket_id, ind.bucket_id)}"
            )
        if ind.layer_id:
            where = layers.get(ind.layer_id, ind.layer_id) + (
                f" / {subs[ind.sublayer_id]}" if ind.sublayer_id in subs else ""
            )
            out.append(f"Who keeps it: {where}")
        return out

    def _awaiting(self) -> dict[str, dict[str, str]]:
        """Crossings the evaluator proposed that wait for a human reason: shown on the card as the override note."""
        if not hasattr(self, "_awaiting_cache"):
            self._awaiting_cache = {
                p["target_id"]: {"new_status": p["new_status"], "since": p["created_at"][:10]}
                for p in read_jsonl(DATA / "proposed_status_events.jsonl")
                if p.get("target_type", "indicator") == "indicator" and not p.get("reason", "").strip()
            }
        return self._awaiting_cache

    def _diffusion_lens(
        self, cards: dict[str, Any], recent: list[dict[str, Any]], as_of: str
    ) -> dict[str, Any]:
        buckets = []
        for b in self.seed.buckets:
            mine = [i for i in self.seed.indicators if i.bucket_id == b.id and i.published]
            flow = [
                cards[i.id] for i in mine if not i.direction_rule
            ]  # a shared capture indicator keeps its own lens
            buckets.append(
                {
                    **dump(b),
                    "indicators": [cards[i.id] for i in mine],
                    "status": _summarise(flow),
                    "tally": _tally(flow),
                }
            )
        valves = []
        for v in VALVES:
            mine = [i for i in self.seed.indicators if i.valve_measured == v["id"] and i.published]
            flow = [cards[i.id] for i in mine if not i.direction_rule]
            valves.append(
                {**v, "status": _summarise(flow), "tally": _tally(flow), "indicator_ids": [i.id for i in mine]}
            )
        falsified = next(
            (t for t in read_jsonl(DATA / "thesis.jsonl") if t.get("id") == "normal_tech_falsified"), None
        )
        thesis = {True: "falsified", False: "holding"}.get(falsified.get("holds")) if falsified else None
        verdict = (
            "As of %s: " % as_of
            + ", ".join(_clause(b) for b in buckets)
            + "."
            + (f" Thesis: {thesis or 'untestable'}." if falsified else "")
        )
        return {
            "as_of": as_of,
            "verdict": verdict,
            "buckets": buckets,
            "valves": valves,
            "recent_status_events": recent,
            "what_would_change": [
                f"{i.name}: {i.band_rationale}"
                for i in self.seed.indicators
                if i.published and i.band_rationale
            ],
        }

    def _write_docs(self, root: Path) -> None:
        """v2 §9's generated documents: sources, bands, changelog and the JSON schemas, deterministic, no health."""
        from . import schema as sc

        def cell(v: Any) -> str:
            return str(v if v is not None else "").replace("|", "/").replace("\n", " ")

        docs, schemas = root / "docs", root / "schema"
        docs.mkdir(parents=True, exist_ok=True)
        schemas.mkdir(parents=True, exist_ok=True)
        head = "<!-- Generated by `ai-tracker export`; edit seed/*.yaml, never this file. -->\n\n"
        rows = [
            "| id | name | org | kind | tier | cadence | licence | attribution |",
            "|---|---|---|---|---|---|---|---|",
        ]
        rows += [
            f"| {x.id} | {cell(x.name)} | {cell(x.org)} | {x.kind.value} | {int(x.default_tier)} | {x.cadence} | {cell(x.license)} | {cell(x.attribution)} |"
            for x in sorted(self.seed.sources, key=lambda x: x.id)
        ]
        skip = ["| id | name | why not ingested |", "|---|---|---|"]
        skip += [
            f"| {x.id} | {cell(x.name)} | {cell(x.reason)} |"
            for x in sorted(self.seed.skipped, key=lambda x: x.id)
        ]
        people = [
            f"- {', '.join(x.people)}: {cell(x.name)}"
            for x in [
                *sorted(self.seed.sources, key=lambda x: x.id),
                *sorted(self.seed.skipped, key=lambda x: x.id),
            ]
            if x.people
        ]
        (docs / "sources.md").write_text(
            head
            + "# Sources\n\n"
            + "\n".join(rows)
            + "\n\n## Read, not ingested\n\n"
            + "\n".join(skip)
            + "\n\n## Who we read\n\n"
            + "\n".join(people)
            + "\n"
        )
        bands = []
        for i in sorted((i for i in self.seed.indicators if i.published), key=lambda i: i.id):
            if i.direction_rule:
                r = i.direction_rule
                rule = f"direction over {r.periods} periods, dead band {r.dead_band}, higher is {r.higher_is}. {r.rationale}"
            else:
                rule = f"normal {_band_text(i.normal_band)}; fast {_band_text(i.fast_band)}; falsifying {_band_text(i.falsifying_band)}. {i.band_rationale or ''}"
            bands.append(
                f"## {i.name} (`{i.id}`)\n\n- Band input: `{i.band_input or (i.series_keys[:1] or [''])[0]}` ({i.unit})\n- Rule: {rule.strip()}\n- Timing: {i.timing_rationale or ''}\n"
            )
        (docs / "bands.md").write_text(head + "# Bands and direction rules\n\n" + "\n".join(bands))
        log = ["| date | target | from | to | author | reason |", "|---|---|---|---|---|---|"]
        log += [
            f"| {e.created_at.date()} | {e.target_id} | {cell(e.old_status)} | {e.new_status} | {e.author} | {cell(e.reason)} |"
            for e in sorted(self.events, key=lambda e: (e.created_at, e.id), reverse=True)
        ]
        (docs / "changelog.md").write_text(head + "# Status changelog\n\n" + "\n".join(log) + "\n")
        for model in (
            sc.Observation,
            sc.Derived,
            sc.Indicator,
            sc.StatusEvent,
            sc.Source,
            sc.SkippedSource,
            sc.Entity,
            sc.Prediction,
            sc.Crosswalk,
            sc.Bottleneck,
            sc.FetchLog,
        ):
            (schemas / f"{model.__name__}.schema.json").write_text(
                json.dumps(model.model_json_schema(), indent=2, sort_keys=True) + "\n"
            )

    def _stack_bars(self) -> dict[str, Any]:
        """Latest complete quarter of the gross-profit stack as one bar per layer, summed here so the web never adds."""
        rows = self.derived_for("gross_profit_share_by_layer")
        if not rows:
            return {}
        latest = max(r.as_of_date for r in rows)
        keys = {o["id"]: o["series_key"] for o in self.observations("sec.*", "sec_seg.*", "epoch.*")}
        # part -> (layer, label, the series whose row the part links to)
        part = {
            "compute_semis": ("compute_physical", "chips", "sec.nvda.gross_profit."),
            "compute_cloud": ("compute_physical", "cloud", "sec_seg.msft.intelligent_cloud.revenue."),
            "model": ("model", "labs", "epoch."),
        }
        bars: dict[str, Any] = {}
        for r in sorted(
            (r for r in rows if r.as_of_date == latest), key=lambda r: r.dims["layer_id"], reverse=True
        ):
            layer, label, prefix = part[r.dims["layer_id"]]
            est = r.dims.get("basis") == "estimated"
            b = bars.setdefault(
                layer,
                {"value": 0.0, "as_of": latest.isoformat(), "estimated": False, "parts": [], "obs_ids": []},
            )
            b["value"] += r.value
            b["estimated"] = b["estimated"] or est
            link = next((i for i in r.input_observation_ids if keys.get(i, "").startswith(prefix)), None)
            b["parts"].append(
                {
                    "label": label,
                    "value": r.value,
                    "estimated": est,
                    "grade": "C"
                    if est
                    else None,  # filed parts mix 10-K (A) and 10-Q (B) rows; the page shows neither
                    "href": f"/series/{keys[link]}#{link}" if link else "/query#gross_profit_share_by_layer",
                    "obs_ids": r.input_observation_ids,
                }
            )
            b["obs_ids"] = sorted(set(b["obs_ids"]) | set(r.input_observation_ids))
        return bars

    def evidence_for(self, *targets: str) -> list[dict[str, Any]]:
        """Dated evidence records: observations whose series is evidence.<target>.<for|against|context>.pt."""
        if not targets:
            return []
        rows = self.con.execute(
            "SELECT id, series_key, as_of_date, value_text, url, tier, source_id, raw_snippet, entity_id, "
            "audited_vs_reported FROM observations "
            "WHERE " + " OR ".join("series_key LIKE ?" for _ in targets) + " ORDER BY as_of_date DESC",
            [f"evidence.{t}.%" for t in targets],
        ).fetchall()
        return [
            {
                "id": r[0],
                "target": r[1].split(".")[1],
                "stance": r[1].split(".")[2],
                "as_of": r[2].isoformat(),
                "summary": r[3],
                "url": r[4],
                "tier": r[5],
                "source_id": r[6],
                "snippet": r[7],
                "entity_id": r[8],
                "grade": _grade({"tier": r[5], "audited_vs_reported": r[9]}),
            }
            for r in rows
        ]

    def _stack(self, cards: dict[str, Any]) -> dict[str, Any]:
        """The sub-layer taxonomy with its entities, their dated memberships and each entity's latest observation."""
        latest = {
            r[0]: {
                "series_key": r[1],
                "value": r[2],
                "value_text": r[3],
                "unit": r[4],
                "as_of": r[5].isoformat(),
                "obs_ids": [r[6]],
            }
            for r in self.con.execute(
                "SELECT entity_id, series_key, value_numeric, value_text, unit, as_of_date, id FROM ("
                "SELECT *, row_number() OVER (PARTITION BY entity_id ORDER BY as_of_date DESC, retrieved_at DESC) rn "
                "FROM observations WHERE entity_id IS NOT NULL AND source_id <> 'openrouter') WHERE rn = 1"  # model prices are not entity facts
            ).fetchall()
        }
        ents = {e.id: e for e in self.seed.entities}

        def entity(e: Entity, m: Membership) -> dict[str, Any]:
            return {
                **dump(e),
                "is_primary": m.is_primary,
                "from_date": m.from_date.isoformat() if m.from_date else None,
                "to_date": m.to_date.isoformat() if m.to_date else None,
                "latest": latest.get(e.id),
            }

        return {
            "layers": [
                {
                    **dump(layer),
                    "sublayers": [
                        {
                            **dump(sub),
                            "entities": sorted(
                                (
                                    entity(ents[e.id], m)
                                    for e in self.seed.entities
                                    for m in e.memberships
                                    if m.sublayer_id == sub.id
                                ),
                                key=lambda x: (not x["is_primary"], x["name"].lower()),
                            ),
                            "indicators": [
                                cards[i.id] for i in self.seed.indicators if i.sublayer_id == sub.id
                            ],
                        }
                        for sub in self.seed.sublayers
                        if sub.layer_id == layer.id
                    ],
                }
                for layer in self.seed.layers
            ]
        }

    def _analyses(self) -> list[dict[str, Any]]:
        """Saved analyses: each metric's latest derived rows with provenance and the formula text, for /query."""
        spec = (yaml.safe_load((SEED / "analyses.yaml").read_text()) or {}).get("analyses", [])
        metrics = (yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {}).get("metrics", {})

        def latest(m: str, dims: dict[str, str] | None) -> dict[str, Any] | None:
            rows = self.derived_for(m, dims)
            return {**dump(rows[-1]), "obs_ids": rows[-1].input_observation_ids} if rows else None

        return [
            {
                **a,
                "latest": latest(a["metric"], a.get("dims")),
                "related_latest": {m: latest(m, None) for m in a.get("related", [])},
                "description": metrics.get(a["metric"], {}).get("description"),
                "caveats": metrics.get(a["metric"], {}).get("caveats"),
                "sql": metrics.get(a["metric"], {}).get("sql")
                or f"python: {metrics.get(a['metric'], {}).get('python')}",
            }
            for a in spec
        ]

    def _ladder(self) -> dict[str, Any]:
        """Appendix E rungs with the production and research rows that sit on each, plus the current level."""
        rungs = (yaml.safe_load((SEED / "ladder.yaml").read_text()) or {}).get("rungs", [])
        rows = self.con.execute(
            "SELECT id, series_key, entity_id, as_of_date, value_numeric, tier, url, raw_snippet FROM observations "
            "WHERE series_key LIKE 'cl_ladder.%' ORDER BY as_of_date"
        ).fetchall()

        def at(level: int, research: bool) -> list[dict[str, Any]]:
            return [
                {
                    "obs_id": r[0],
                    "subject": r[1].split(".")[1],
                    "entity_id": r[2],
                    "as_of": r[3].isoformat(),
                    "tier": r[5],
                    "url": r[6],
                    "snippet": r[7],
                }
                for r in rows
                if r[4] == level and r[1].endswith(".rung_research.pt") == research
            ]

        cur = self.derived_for("continual_learning_level")
        return {
            "current": {
                "value": cur[-1].value,
                "as_of": cur[-1].as_of_date.isoformat(),
                "obs_ids": cur[-1].input_observation_ids,
            }
            if cur
            else None,
            "rungs": [
                {**r, "production": at(r["level"], False), "research": at(r["level"], True)} for r in rungs
            ],
            "chart_sources": self._chart_sources([r[0] for r in rows]),
        }

    def _venture(self) -> dict[str, dict[str, Any]]:
        """Per sub-layer: quarterly venture dollars and round counts from the derived rows, for the flow strip."""
        out: dict[str, dict[str, Any]] = {}
        for metric in ("venture_dollars", "round_count", "venture_dollars_incl_debt"):
            for d in self.derived_for(metric):
                sub = d.dims.get("sublayer_id")
                if not sub:
                    continue
                q = out.setdefault(sub, {"sublayer_id": sub, "quarters": {}})["quarters"].setdefault(
                    d.as_of_date.isoformat(), {"as_of": d.as_of_date.isoformat()}
                )
                q[metric] = {"value": d.value, "obs_ids": d.input_observation_ids}
        self._by_source(out)
        return {
            k: {
                **v,
                "quarters": [v["quarters"][d] for d in sorted(v["quarters"])],
                "chart_sources": self._chart_sources(
                    [
                        i
                        for q in v["quarters"].values()
                        for seg in q.get("by_source", [])
                        for i in seg["obs_ids"]
                    ],
                    "venture_dollars_by_source",
                ),
            }
            for k, v in out.items()
        }

    def _chart_sources(self, ids: list[str], metric: str | None = None) -> dict[str, Any]:
        """P1 §9: every chart names where its points come from (and the metric, when they are derived)."""
        ids = sorted(set(ids))
        found = (
            {
                r[0]
                for r in self.con.execute(
                    "SELECT DISTINCT source_id FROM observation_all WHERE id IN ("
                    + ",".join("?" * len(ids))
                    + ")",
                    ids,
                ).fetchall()
            }
            if ids
            else set()
        )
        return {
            "metric": metric,
            "sources": [
                {"id": x.id, "name": x.name, "org": x.org, "license": x.license, "attribution": x.attribution}
                for x in self.seed.sources
                if x.id in found
            ],
        }

    def _by_source(self, out: dict[str, dict[str, Any]]) -> None:
        """Stacked segments per quarter: source x kind, each linking to its first round's row."""
        keys = {o["id"]: o["series_key"] for o in self.observations("formd.*", "epoch.*")}
        for d in self.derived_for("venture_dollars_by_source"):
            sub = d.dims["sublayer_id"]
            q = out.setdefault(sub, {"sublayer_id": sub, "quarters": {}})["quarters"].setdefault(
                d.as_of_date.isoformat(), {"as_of": d.as_of_date.isoformat()}
            )
            first = d.input_observation_ids[0]
            q.setdefault("by_source", []).append(
                {
                    "source": d.dims["source"],
                    "kind": d.dims["kind"],
                    "value": d.value,
                    "obs_ids": d.input_observation_ids,
                    "href": f"/series/{keys[first]}#{first}" if first in keys else None,
                }
            )

    def _layer_venture(self, layer_id: str) -> dict[str, Any] | None:
        """Trailing-four-quarter equity dollars at the latest quarter the venture data covers, the same a year
        earlier, the arrow (±10% [judgement]) and each sub-layer's figure for the ticks. A layer with no rounds in
        that window reads "none on file" (value None), never its last non-empty figure."""
        every = [d for d in self.derived_for("venture_dollars_4q") if d.as_of_date <= date.today()]
        rows = [d for d in every if d.dims["layer_id"] == layer_id]
        if not rows:
            return None
        latest, first = max(d.as_of_date for d in every), min(d.as_of_date for d in every)

        def at(day: date, sub: str) -> Derived | None:
            return next((d for d in rows if d.as_of_date == day and d.dims["sublayer_id"] == sub), None)

        def pt(d: Derived) -> dict[str, Any]:
            return {"value": d.value, "as_of": d.as_of_date.isoformat(), "obs_ids": d.input_observation_ids}

        prior_day = date(latest.year - 1, latest.month, latest.day)
        now, prior = at(latest, "all"), at(prior_day, "all")
        nv = now.value if now else 0.0
        pv = prior.value if prior else (0.0 if prior_day >= first else None)  # covered, but no rounds in it
        change = None if pv is None or (pv == 0 and nv == 0) else math.inf if pv == 0 else nv / pv - 1
        names = {x.id: x.name for x in self.seed.sublayers}
        return {
            **(pt(now) if now else {"value": None, "as_of": latest.isoformat(), "obs_ids": []}),
            "prior": pt(prior) if prior else None,
            "arrow": None
            if change is None
            else "up"
            if change > 0.10
            else "down"
            if change < -0.10
            else "flat",
            "sublayers": [
                {
                    "sublayer_id": d.dims["sublayer_id"],
                    "name": names.get(d.dims["sublayer_id"], d.dims["sublayer_id"]),
                    **pt(d),
                }
                for d in sorted(rows, key=lambda d: -d.value)
                if d.as_of_date == latest and d.dims["sublayer_id"] != "all"
            ],
        }

    def _capture_layer(self, layer: Any, cards: dict[str, Any]) -> dict[str, Any]:
        """One layer of the capture lens. Only direction-scored indicators vote: a flow status on the same
        layer belongs to the other lens."""
        mine = [i for i in self.seed.indicators if i.layer_id == layer.id and i.published]
        directions = [cards[i.id] for i in mine if i.direction_rule]
        return {
            **dump(layer),
            "indicators": [cards[i.id] for i in mine],
            "status": _summarise(directions),
            "tally": _tally(directions),
            "venture": self._layer_venture(layer.id),
            "reading": self._reading(layer, cards),
        }

    def _reading(self, layer: Any, cards: dict[str, Any]) -> str:
        """One sentence per layer from its direction statuses and capital flow. Deterministic; no numbers."""
        scored = [
            cards[i.id]
            for i in self.seed.indicators
            if i.layer_id == layer.id and i.published and i.direction_rule
        ]
        status = _summarise(scored).replace("_", " ")

        def names(xs: list[str]) -> str:
            return (
                xs[0]
                if len(xs) == 1
                else f"{xs[0]} and {xs[1]}"
                if len(xs) == 2
                else f"{xs[0]}, {xs[1]} and others"
            )

        conc = [c["name"] for c in scored if c["status"] == "concentrating"]
        disp = [c["name"] for c in scored if c["status"] == "dispersing"]
        # the status chip and the venture arrow sit beside this sentence, so it says what they cannot
        parts = (
            []
            if conc or disp
            else [f"{layer.name} {'is' if status in ('unmeasured', 'not yet measurable') else 'reads'} {status}"]
        )
        if conc:
            parts.append(f"toward concentration: {names(conc)}")
        if disp:
            parts.append(f"toward dispersion: {names(disp)}")
        if not parts:
            parts = [f"{layer.name} reads {status}"]
        out = "; ".join(parts) + "."
        return out[0].upper() + out[1:]

    def _commoditisation(self, cards: dict[str, Any]) -> dict[str, Any]:
        """The model layer's four commoditisation proxies (Part 1's list), named with their own statuses; no composite."""
        ids = [
            "open_vs_closed_gap",
            "model_price_per_intelligence_point",
            "epoch_inference_price_fixed_capability",
            "enterprise_multi_homing_share",
        ]
        proxies = [
            {"id": i, "name": cards[i]["name"], "status": cards[i]["status"]} for i in ids if i in cards
        ]
        return {
            "proxies": proxies,
            "line": "Commoditisation proxies: "
            + "; ".join(f"{p['name']} {(p['status'] or 'unmeasured').replace('_', ' ')}" for p in proxies)
            + ".",
        }

    def _bottlenecks(self, cards: dict[str, Any]) -> dict[str, Any]:
        def rel(b: Bottleneck) -> list[dict[str, Any]]:
            return [
                {
                    "id": i,
                    "name": cards[i]["name"],
                    "status": cards[i]["status"],
                    "published": cards[i]["published"],
                }
                for i in b.related_indicators
                if i in cards
            ]

        items = [{**dump(b), "related": rel(b)} for b in self.seed.bottlenecks]
        fast, normal = {"faster_than_normal"}, {"consistent_with_normal", "slower_than_normal"}
        summary = []
        for sec in self.seed.sections:
            its = [i for i in items if i["section"] == sec["name"]]
            linked = list({r["id"]: r for i in its for r in i["related"] if r["published"]}.values())
            summary.append(
                {
                    "name": sec["name"],
                    "items": len(its),
                    "watched": sum(1 for i in its if i["related"]),
                    "fast": sum(1 for r in linked if r["status"] in fast),
                    "normal": sum(1 for r in linked if r["status"] in normal),
                    "other": sum(1 for r in linked if r["status"] and r["status"] not in fast | normal),
                }
            )
        domains = [d for d, _ in Counter(b.domain or "general" for b in self.seed.bottlenecks).most_common()]
        grid = [
            {
                "name": sec["name"],
                "cells": {
                    d: [
                        b.id
                        for b in self.seed.bottlenecks
                        if b.section == sec["name"] and (b.domain or "general") == d
                    ]
                    for d in domains
                },
            }
            for sec in self.seed.sections
        ]
        return {
            "sections": self.seed.sections,
            "essays": [dump(e) for e in self.seed.essays],
            "items": items,
            "summary": summary,
            "domains": domains,
            "grid": grid,
        }

    def _compare(self, cards: dict[str, Any]) -> dict[str, Any]:
        """Leans is derived from status, never written by hand."""
        LEAN = {"faster_than_normal": "ai2027", "consistent_with_normal": "nk", "slower_than_normal": "nk"}
        preds = {p.id: p for p in self.seed.predictions}

        def pred(pid: str) -> dict[str, Any]:
            ev = self.current(pid)
            return {"id": pid, "claimant": preds[pid].claimant, "status": ev.new_status if ev else None}

        rows = []
        for r in self.seed.compare:
            c = cards[r.indicator]
            ids = list(dict.fromkeys(r.predictions + r.nk_predictions + r.ai2027_predictions))
            flow = not next(i for i in self.seed.indicators if i.id == r.indicator).direction_rule
            rows.append(
                {
                    "indicator": r.indicator,
                    "card": c,
                    # a capture row reads concentrating or dispersing, which neither worldview's lean describes
                    "leans": (LEAN.get(c["status"] or "", "open") if c["published"] else "open")
                    if flow
                    else None,
                    "columns": {
                        ledger: {
                            "text": getattr(r, ledger),
                            "predictions": [pred(p) for p in ids if preds[p].ledger == ledger],
                        }
                        for ledger in ("nk", "ai2027", "lab", "capture")
                    },
                }
            )
        tally = {k: sum(1 for x in rows if x["leans"] == k) for k in ("nk", "ai2027", "open")}
        return {"rows": rows, "tally": tally}

    def _ledger(self) -> list[dict[str, Any]]:
        """The circular / vendor-financing ledger: every `circular.*` and `markets.*` observation with parties and instrument."""
        names = {n.lower(): e for e in self.seed.entities for n in (e.id, e.name, *e.aliases)}

        def party(
            slug: str,
        ) -> dict[str, Any]:  # series keys name parties in lower case; resolve them to entities
            e = names.get(slug)
            primary = next((m for m in e.memberships if m.is_primary), None) if e else None
            return {
                "slug": slug,
                "entity_id": e.id if e else None,
                "name": e.name if e else slug,
                "href": f"/stack/{primary.sublayer_id}#{e.id}"
                if e and primary and primary.sublayer_id
                else None,
            }

        rows = []
        for o in self.observations("circular.*", "markets.*"):
            parts = o["series_key"].split(".")
            parties = parts[1].split("_") if parts[0] == "circular" else [parts[1]]
            instrument = parts[2].rsplit("_", 1)[0] if parts[0] == "circular" else parts[2]
            rows.append(
                {
                    **_full(o),
                    "parties": [party(x) for x in parties],
                    "instrument": instrument,
                    "obs_id": o["id"],
                }
            )
        return sorted(rows, key=lambda r: r["as_of_date"], reverse=True)

    def _withdrawn(self) -> dict[str, list[dict[str, Any]]]:
        """Rows withdrawn in place (rejected, with the reason in dispute_text): shown struck through, never deleted."""
        cur = self.con.execute(
            "SELECT * FROM observation_all WHERE review_status = 'rejected' AND dispute_text IS NOT NULL "
            "ORDER BY as_of_date, id"
        )
        cols = [d[0] for d in cur.description]
        out: dict[str, list[dict[str, Any]]] = {}
        for r in cur.fetchall():
            o = dict(zip(cols, r))
            out.setdefault(o["series_key"], []).append(_full(o))
        return out

    def _all_series(self) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for o in self.observations("*"):
            out.setdefault(o["series_key"], []).append(o)
        return out

    def _source_health(self, s: Source) -> dict[str, Any]:
        own = [fl for fl in self.fetchlog if fl.source_id == s.id]
        if not own and s.connector == "feeds":  # one connector fetches every watched feed under its own id;
            mine = lambda fl: f"{s.id}:" in (fl.error or "")  # noqa: E731 - a run failed this feed only if its error names it
            own = [
                fl.model_copy(update={"ok": fl.ok or not mine(fl), "error": fl.error if mine(fl) else None})
                for fl in self.fetchlog
                if fl.source_id == "feeds"
            ]
        logs = sorted(own, key=lambda fl: fl.finished_at)
        last_ok = next((fl for fl in reversed(logs) if fl.ok), None)
        if not last_ok:
            row = self.con.execute(
                "SELECT max(retrieved_at), count(*) FROM observation_all WHERE source_id = ?", [s.id]
            ).fetchone()
            if row and row[0]:
                return {
                    **dump(s),
                    "last_success_at": row[0],
                    "last_error": None,
                    "items_found": row[1],
                    "runs": 0,
                    "health": _health(row[0], s.cadence),
                }
        return {
            **dump(s),
            "last_success_at": last_ok.finished_at.isoformat() if last_ok else None,
            "last_error": logs[-1].error if logs and not logs[-1].ok else None,
            "items_found": last_ok.items_found if last_ok else 0,
            "runs": len(logs),
            "health": _health(last_ok.finished_at.isoformat() if last_ok else None, s.cadence),
        }


def _health(last_success: str | None, cadence: str) -> str:
    """ok within twice the cadence (plus a lag), stale beyond it, never when there is no success at all."""
    if not last_success:
        return "never"
    days = CADENCE_DAYS.get(cadence)
    if days is None:
        return "ok"
    age = (date.today() - date.fromisoformat(last_success[:10])).days
    return "ok" if age <= max(2 * days, days + 30) else "stale"


CADENCE_DAYS = {
    "daily": 1,
    "weekly": 7,
    "biweekly": 14,
    "monthly": 31,
    "quarterly": 92,
    "per_release": 120,
    "annual": 366,
}
VALVES = [
    {"id": "invention_to_product", "from": "methods", "to": "products", "name": "Invention → product"},
    {"id": "product_to_adoption", "from": "products", "to": "early_adoption", "name": "Product → adoption"},
    {
        "id": "adoption_to_adaptation",
        "from": "early_adoption",
        "to": "adaptation",
        "name": "Adoption → adaptation",
    },
    {
        "id": "return_arrow",
        "from": "adaptation",
        "to": "methods",
        "name": "Return arrow (deployment → invention)",
    },
    {"id": "leak", "from": "adaptation", "to": "capture", "name": "Leak (surplus exits the chain)"},
]


def _grade(o: dict[str, Any]) -> str:
    """One row's grade. The basis matters: a 10-K is audited and grades A, a 10-Q is company-stated and grades B."""
    from .schema import Basis, grade_from_tier

    return grade_from_tier(Tier(o["tier"]), Basis(o["audited_vs_reported"]))


def _best_grade(obs: list[dict[str, Any]]) -> str | None:
    """The best grade among the rows behind an indicator; A sorts before B before C before D."""
    return min((_grade(o) for o in obs), default=None)


def _clause(doc: dict[str, Any]) -> str:
    """A layer's clause in the lens verdict. One instrument is a reading, not a direction, so it is named."""
    t = doc.get("tally") or {}
    tail = " (one reading)" if t.get("scored") == 1 else ""
    return f"{doc['name'].lower()} {doc['status'].replace('_', ' ')}{tail}"


def _votes(cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One vote per source cluster: four readings of one survey are one instrument, not four facts. Within a
    cluster the most confident scored card speaks. An unscored or unclear card never votes."""
    clusters: dict[str, list[dict[str, Any]]] = {}
    for c in cards:
        if c.get("status") and c["status"] not in UNVOTED:
            clusters.setdefault(c.get("source_cluster") or c["id"], []).append(c)
    return [max(v, key=lambda c: (c.get("confidence") or 0, c["id"])) for v in clusters.values()]


def _summarise(cards: list[dict[str, Any]]) -> str:
    """Mode of the votes; an unscored or unclear card never outvotes a reading, and one instrument votes once."""
    if not [c for c in cards if c.get("status")]:
        return "unmeasured"
    votes = _votes(cards)
    if not votes:
        return "emerging" if any(c.get("status") == "emerging" for c in cards) else "unclear"
    statuses = [c["status"] for c in votes]
    counts = sorted(((statuses.count(x), x) for x in set(statuses)), reverse=True)
    if len(counts) > 1 and counts[0][0] == counts[1][0]:
        return "mixed"  # no majority: say so rather than pick one
    return counts[0][1]


def _tally(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """What the verdict rests on: how many instruments voted, out of how many published indicators, by how
    much, and the name of the single reading when only one voted (v2 §4.2: say how thin a reading is)."""
    votes = _votes(cards)
    statuses = [c["status"] for c in votes]
    counts = sorted(((statuses.count(x), x) for x in set(statuses)), reverse=True)
    return {
        "scored": len(votes),
        "published": len([c for c in cards if c.get("published", True)]),
        "margin": counts[0][0] - (counts[1][0] if len(counts) > 1 else 0) if counts else 0,
        "only": votes[0]["name"] if len(votes) == 1 else None,
    }


def _band_text(b: Any) -> str:
    return (
        "none"
        if not b
        else f"{b.lo if b.lo is not None else '-inf'} to {b.hi if b.hi is not None else 'inf'}"
    )


def _utc_naive(t: datetime) -> datetime:
    return t.astimezone(timezone.utc).replace(tzinfo=None) if t.tzinfo else t


def _point(o: dict[str, Any]) -> dict[str, Any]:
    return {
        "as_of": o["as_of_date"].isoformat(),
        "value": o["value_numeric"],
        "low": o["value_low"],
        "high": o["value_high"],
        "obs_ids": [o["id"]],
        "series_key": o["series_key"],
        "subject": o["subject"],
        "unit": o["unit"],
        "disputed": o["disputed"],
        "grade": _grade(o),
        **_flags(o),
    }


def _flags(o: dict[str, Any]) -> dict[str, Any]:
    """v2 §1.3: the flags travel with every point, so a card or chart never shows a run-rate as revenue unmarked."""
    flags = [
        label
        for label, on in (
            ("disputed", o.get("disputed")),
            ("run-rate", o.get("run_rate_vs_booked") == "run_rate"),
            ("gross", o.get("gross_vs_net") == "gross"),
            ("net", o.get("gross_vs_net") == "net"),
        )
        if on
    ]
    return {"flags": flags, "dispute_text": o.get("dispute_text")} if flags else {}


def _full(o: dict[str, Any]) -> dict[str, Any]:
    return {**_jsonable(o), "grade": _grade(o)}


def _jsonable(d: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(d, default=lambda v: v.value if hasattr(v, "value") else str(v)))


def _write(p: Path, doc: Any) -> None:
    p.write_text(json.dumps(doc, sort_keys=True, indent=1, default=str) + "\n")
