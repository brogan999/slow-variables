"""Seed YAML + data/*.jsonl -> in-memory DuckDB; export -> web/data/*.json. The web never computes a number."""

from __future__ import annotations

import csv
import json
import math
import threading
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from fnmatch import fnmatch
from functools import cached_property
from pathlib import Path
from typing import Any

import duckdb
import yaml

from . import chart
from .analysis.direction import window
from .schema import (
    CONFIDENCE_RUBRIC,
    STAMPS,
    UNVOTED,
    Basis,
    Bottleneck,
    Bucket,
    CompareRow,
    Crosswalk,
    Derived,
    Entity,
    Essay,
    Extraction,
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
    stamp,
)

SEED, DATA, WEB = Path("seed"), Path("data"), Path("web/data")
# the two profit stacks, bottom first: (layer id in the metric's dims, label)
GROSS_PROFIT_PARTS = [("compute_semis", "Chips"), ("compute_cloud", "Cloud"), ("model", "Labs")]
MARGIN_PARTS = [("compute_semis", "Chip segments"), ("compute_cloud", "Cloud segments")]
Path = Path  # re-exported for cli
OBS = DATA / "observations"

# Every venture metric reads rounds from this one view: Form D equity and debt, and Epoch's equity rounds with no Form D
# row for the same entity in the same calendar quarter or within 45 days (Form D is tier 4, Epoch tier 5; the better
# source wins). The quarter match alone counted xAI's Series E twice: its Form D dates the first sale in December and
# Epoch dates the round in January.
# ponytail: the match reads dates, not amounts, so a small filing beside a separate large reported round would hide it.
VENTURE_ROUNDS = """CREATE OR REPLACE VIEW venture_rounds AS
WITH f AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'formd' AS source, 'equity' AS kind FROM observations
           WHERE series_key LIKE 'formd.%.amount_sold_usd.pt' AND entity_id IS NOT NULL),
d AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'formd' AS source, 'debt' AS kind FROM observations
      WHERE series_key LIKE 'formd.%.debt_sold_usd.pt' AND entity_id IS NOT NULL),
e AS (SELECT entity_id, as_of_date, value_numeric AS v, id, 'epoch' AS source, 'equity' AS kind FROM observations
      WHERE series_key LIKE 'epoch.%.round_equity_usd.pt' AND entity_id IS NOT NULL)
SELECT * FROM f UNION ALL SELECT * FROM d
UNION ALL SELECT * FROM e WHERE NOT EXISTS (  -- one round reported twice: a filing and Epoch's row
  SELECT 1 FROM f WHERE f.entity_id = e.entity_id AND (date_trunc('quarter', f.as_of_date) = date_trunc('quarter', e.as_of_date)
                                                      OR abs(date_diff('day', f.as_of_date, e.as_of_date)) <= 45))"""
# Trailing four quarters of capital spending by the five hyperscalers, one row per quarter in which all five have four
# quarters. The same differencing of year-to-date filings as capex_to_revenue_stack (a test holds the two equal).
# ponytail: two copies of these CTEs; repoint capex_to_revenue_stack here in its own PR.
CAPEX_TTM = """CREATE OR REPLACE VIEW hyperscaler_capex_ttm AS
WITH cum AS (
  SELECT subject, as_of_date, period_start, value_numeric AS v, id FROM observations
  WHERE source_ns = 'sec' AND measure = 'capex' AND grain IN ('q', 'h1', '9m', 'fy')
    AND subject IN ('msft', 'googl', 'amzn', 'meta', 'orcl')),
diffed AS (
  SELECT subject, as_of_date, v - coalesce(lag(v) OVER w, 0) AS v,
         list_filter([id, lag(id) OVER w], x -> x IS NOT NULL) AS ids,
         date_diff('day', coalesce(lag(as_of_date) OVER w, period_start), as_of_date) AS days
  FROM cum WINDOW w AS (PARTITION BY subject, period_start ORDER BY as_of_date)),
capex AS (
  SELECT date_trunc('quarter', as_of_date) AS cq, subject, v, ids FROM diffed WHERE days BETWEEN 80 AND 100
  QUALIFY row_number() OVER (PARTITION BY subject, as_of_date ORDER BY len(ids), ids) = 1),
qs AS (SELECT DISTINCT cq FROM capex),
per AS (
  SELECT q.cq, c.subject, sum(c.v) AS v, flatten(list(c.ids)) AS ids
  FROM qs q JOIN capex c ON c.cq > q.cq - INTERVAL 12 MONTH AND c.cq <= q.cq
  GROUP BY q.cq, c.subject HAVING count(*) = 4)
SELECT cq, sum(v) AS v, list_sort(flatten(list(ids))) AS ids FROM per GROUP BY cq HAVING count(*) = 5"""
# Each data-centre site Epoch tracks that has both a built figure and a planned one: the newest reading dated on or
# before today, and the largest figure dated after it. Rows Epoch has withdrawn are flagged disputed and left out.
DC_SITES = """CREATE OR REPLACE VIEW dc_sites AS
WITH x AS (
  SELECT subject, as_of_date, value_numeric AS mw, id, retrieved_at FROM observations
  WHERE source_ns = 'epoch_dc' AND measure = 'power_mw' AND NOT coalesce(disputed, false)),
built AS (
  SELECT subject, arg_max(mw, as_of_date) AS built_mw, arg_max(id, as_of_date) AS built_id
  FROM x WHERE as_of_date <= current_date GROUP BY subject),
planned AS (
  SELECT subject, mw AS planned_mw, id AS planned_id FROM x WHERE as_of_date > current_date
  QUALIFY row_number() OVER (PARTITION BY subject ORDER BY mw DESC, as_of_date, id) = 1)
SELECT b.subject, b.built_mw, b.built_id, p.planned_mw, p.planned_id,
       (SELECT least(CAST(substr(max(retrieved_at), 1, 10) AS DATE), current_date) FROM x) AS read_on
FROM built b JOIN planned p USING (subject)"""
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
        # the series key is <namespace>.<subject>.<measure>.<grain>; split once here so no formula has to
        self.con.execute("""CREATE VIEW observations AS
            SELECT *, split_part(series_key, '.', 1) AS source_ns, split_part(series_key, '.', 2) AS subject,
                   array_to_string(str_split(series_key, '.')[3:-2], '.') AS measure,
                   str_split(series_key, '.')[-1] AS grain,
                   date_trunc('quarter', as_of_date) AS q
            FROM observation_all o
            WHERE review_status = 'approved' AND NOT EXISTS (SELECT 1 FROM observation_all s WHERE s.supersedes_id = o.id)""")
        self.con.execute(
            "CREATE TABLE entity_membership (entity_id VARCHAR, layer_id VARCHAR, sublayer_id VARCHAR, "
            "is_primary BOOLEAN, from_date DATE, to_date DATE)"
        )
        # the bands, so a formula that needs a threshold joins the seed rather than restating the number
        self.con.execute(
            "CREATE TABLE bands (indicator_id VARCHAR, band_input VARCHAR, normal_lo DOUBLE, normal_hi DOUBLE, "
            "fast_lo DOUBLE, fast_hi DOUBLE, falsifying_lo DOUBLE, falsifying_hi DOUBLE)"
        )
        self.con.executemany(
            "INSERT INTO bands VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    i.id,
                    i.band_input,
                    *(
                        x
                        for b in (i.normal_band, i.fast_band, i.falsifying_band)
                        for x in (b.lo if b else None, b.hi if b else None)
                    ),
                )
                for i in self.seed.indicators
            ],
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
        self.con.execute(CAPEX_TTM)
        self.con.execute(DC_SITES)
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
                    _formula(m),
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

    def metric_spec(self, name: str | None) -> dict[str, Any]:
        """One metric's entry in the semantic layer, or an empty dict."""
        if not name:
            return {}
        if not hasattr(self, "_metric_spec"):
            path = Path("semantic/metrics.yaml")
            self._metric_spec = (
                (yaml.safe_load(path.read_text()) or {}).get("metrics", {}) if path.exists() else {}
            )
        return self._metric_spec.get(name) or {}

    def band_unit(self, ind: Indicator) -> str:
        """The unit of the number the bands apply to: a metric's own unit when the band reads a metric."""
        if ind.band_input and ind.band_input.startswith("metric:"):
            return self.metric_spec(ind.band_input[7:]).get("unit") or ind.unit
        return ind.unit

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

    @cached_property
    def _obs_meta(self) -> dict[str, tuple[str, str]]:
        """Every row's series key and stamp, for a point's link and the firmness word a figure prints."""
        rows = self.con.execute(
            "SELECT id, series_key, tier, audited_vs_reported, extraction_method FROM observation_all"
        ).fetchall()
        return {i: (k, stamp(Tier(t), Basis(b), Extraction(x))) for i, k, t, b, x in rows}

    def stamp_of(self, ids: list[str]) -> str | None:
        """The weakest stamp among the rows behind a number: a ratio of a filing and an estimate is an estimate."""
        got = [self._obs_meta[i][1] for i in ids if i in self._obs_meta]
        return min(got, key=STAMPS.index) if got else None

    def href_of(self, ids: list[str]) -> str | None:
        """A row's record on its series page (the first of `ids` the store holds)."""
        first = next((i for i in ids if i in self._obs_meta), None)
        return f"/series/{self._obs_meta[first][0]}#{first}" if first else None

    def _chart(self, ind: Indicator, pts: list[dict[str, Any]]) -> dict[str, Any] | None:
        """The indicator chart, laid out here so the page only draws: axes, the bands or the direction rule's window,
        and each point's position, link and stamp, written onto the point itself."""
        today, log = date.today(), ind.unit == "minutes"
        for p in pts:
            day = date.fromisoformat(p["as_of"])
            # a reading's record is its row; a number derived from several rows links to its derived row, which
            # lists them all (picking one input would be arbitrary)
            many = p.get("derived_id") and len(p["obs_ids"]) > 1
            p["href"] = f"#d-{p['derived_id']}" if many else self.href_of(p["obs_ids"])
            p["stamp"] = self.stamp_of(p["obs_ids"])
            if day > today:  # a quarter still running, dated at its end
                p["partial"] = True
        drawn = [
            p
            for p in pts
            if p["value"] is not None and math.isfinite(p["value"]) and (p["value"] > 0 or not log)
        ]
        if not drawn:
            return None
        rule, when = ind.direction_rule, [date.fromisoformat(p["as_of"]) for p in drawn]
        win = window(list(zip(when, (p["value"] for p in drawn))), rule) if rule else []
        on_chart = [("normal", ind.normal_band), ("fast", ind.fast_band)] if not rule and ind.band_input and (
            ind.band_input == f"metric:{ind.metric}" or ind.band_input == (ind.series_keys or [None])[0]
        ) else []  # fmt: skip
        extra = (
            [win[0][1] - rule.dead_band, win[0][1] + rule.dead_band]
            if win
            else [e for _, b in on_chart if b for e in (b.lo, b.hi) if e is not None]
        )
        # a range open at one end shows a sliver past its edge, or a fast range at the axis's top would draw nothing
        vals = [
            v
            for p in drawn
            for v in (p["value"], p.get("low"), p.get("high"))
            if v is not None and math.isfinite(v)
        ]
        vals += extra
        reach = (max(vals) - min(vals)) * 0.08
        extra += [b.lo + reach for _, b in on_chart if b and b.hi is None and b.lo is not None]
        extra += [b.hi - reach for _, b in on_chart if b and b.lo is None and b.hi is not None]
        xa = chart.time_axis(when)
        ya = chart.axis(
            [v for p in drawn for v in (p["value"], p.get("low"), p.get("high"))] + extra,
            ind.unit,
            log=log,
            zero=not rule and not log,
        )
        left = Counter(win)  # a point is in the window when its (date, value) is; ties are identical readings
        for d, p in zip(when, drawn):
            p["x"], p["y"] = chart.x(d, xa["lo"], xa["hi"]), chart.y(p["value"], ya)
            if all(
                p.get(k) is not None and math.isfinite(p[k]) and (p[k] > 0 or not log)
                for k in ("low", "high")
            ):
                p["y_low"], p["y_high"] = chart.y(p["low"], ya), chart.y(p["high"], ya)
            if rule:
                p["faint"] = not left[(d, p["value"])]
                left[(d, p["value"])] -= 1
        bands = [
            {"name": name, "y": (top := chart.y(ya["hi"] if b.hi is None else b.hi, ya)),
             "height": round(chart.y(ya["lo"] if b.lo is None else b.lo, ya) - top, 2)}
            for name, b in on_chart if b
        ]  # fmt: skip
        dead = change = None
        if rule and len(win) == rule.periods + 1:
            (d0, base), (d1, last) = win[0], win[-1]
            top, x0 = chart.y(base + rule.dead_band, ya), chart.x(d0, xa["lo"], xa["hi"])
            dead = {
                "x": x0,
                "width": round(chart.x(d1, xa["lo"], xa["hi"]) - x0, 2),
                "y": top,
                "height": round(chart.y(base - rule.dead_band, ya) - top, 2),
            }
            steps = [b[1] - a[1] for a, b in zip(win, win[1:])]
            change = {
                "label": chart.change_label(last - base, ind.unit),
                "dead_band": "±" + chart.change_label(rule.dead_band, ind.unit)[1:],
                # the rule's second test: more than half the steps must move the way the window moved
                "steps": f"{sum(1 for x in steps if x * (last - base) > 0)} of {len(steps)} steps "
                + ("rose" if last > base else "fell"),
            }
        series = None if ind.metric else (ind.series_keys or [None])[0]
        return {
            "x": {"ticks": xa["ticks"]},
            "y": {
                **{k: ya[k] for k in ("ticks", "unit", "log")},
                "chars": max(len(t["label"]) for t in ya["ticks"]),
            },
            "bands": bands,
            "dead": dead,
            "change": change,
            "line": bool(rule)
            and len(set(when)) == len(when),  # a single series in time order: join the dots
            "drawn": {
                "metric": ind.metric,
                "series": series,
                "others": len(ind.series_keys) - (1 if series else 0),
                "total": len(ind.series_keys),
            },
            "needs": rule.periods + 1 if rule else None,  # readings the direction rule compares
            "partial": any(p.get("partial") for p in drawn),
            "n_drawn": len(drawn),
            "stamps": sorted({p["stamp"] for p in drawn if p["stamp"]}, key=STAMPS.index),
        }

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
                    "derived_id": d.id,
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
            pts = self.headline(ind)
            doc = {
                **_jsonable(ind.model_dump()),
                **cards[ind.id],
                "points": pts,
                "chart": self._chart(ind, pts),
                "direction_readings": ind.direction_rule.periods + 1 if ind.direction_rule else None,
                # the ids of the sources actually behind the rows: a series namespace is not always a source id
                "source_ids": sorted({o["source_id"] for o in self.evidence_obs(ind)}),
                "band_value": {
                    "value": bv,
                    "unit": self.band_unit(ind),
                    "as_of": b_as_of.isoformat() if b_as_of else None,
                    "obs_ids": b_ids,
                    "low": fit.value_low if (fit := self.band_fit(ind)) else None,
                    "high": fit.value_high if fit else None,
                }
                if bv is not None
                else None,
                "fits": [
                    {
                        **dump(r[-1]),
                        "obs_ids": r[-1].input_observation_ids,
                        "unit": self.metric_spec(m).get("unit"),
                    }
                    for m in ind.related_metrics
                    if (r := self.derived_for(m, ind.metric_dims))
                ],
                "series": [{"series_key": k, "points": v} for k, v in sorted(series.items())],
                "chart_sources": self._chart_sources([i for p in pts for i in p["obs_ids"]], ind.metric),
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
                "gross_profit_stack": self._profit_stack("gross_profit_share_by_layer", GROSS_PROFIT_PARTS),
                "margin_stack": self._profit_stack("margin_stack_share_by_layer", MARGIN_PARTS),
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
        _write(out / "signposts.json", self._signposts())
        _write(out / "context.json", self._context())
        _write(out / "analyses.json", self._analyses())
        from .memo import load_memos

        memos = load_memos()
        (out / "memos").mkdir(parents=True, exist_ok=True)
        for m in memos:
            _write(out / "memos" / f"{m['date']}.json", m)
        _write(
            out / "memos" / "index.json",
            [
                {k: v for k, v in m.items() if k != "body"} | {"summary": _excerpt(m["body"])}
                for m in reversed(memos)
            ],
        )
        (out / "venture").mkdir(parents=True, exist_ok=True)
        for sub_id, doc in self._venture().items():
            _write(out / "venture" / f"{sub_id}.json", doc)
        bottlenecks = self._bottlenecks(cards)
        _write(out / "bottlenecks.json", bottlenecks)
        _write(out / "compare.json", self._compare(cards))
        _write(out / "thesis.json", read_jsonl(DATA / "thesis.jsonl"))
        from .argument import build

        argument = build(self)
        _write(out / "argument.json", argument)
        from .outlook import build as build_outlook

        outlook = build_outlook(self)
        _write(out / "outlook.json", outlook)
        _write(out / "board.json", self.board(cards, argument, outlook))
        from .singularity import build as build_singularity

        _write(out / "singularity.json", build_singularity(self, outlook=outlook))
        from .bottleneck_map import from_store

        _write(out / "map.json", from_store(self, cards, bottlenecks, argument, outlook))
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
                    "confidence_rubric": [{**b, "span": b["hi"] - b["lo"] + 1} for b in CONFIDENCE_RUBRIC],
                    "sources": len(self.seed.sources),
                }
            )
            + "\n"
        )

    def _ledger_rows(self) -> list[dict[str, Any]]:
        return [
            {**_jsonable(pr.model_dump()), "status": ev.new_status if (ev := self.current(pr.id)) else None}
            for pr in self.seed.predictions
        ]

    def board(
        self,
        cards: dict[str, dict[str, Any]] | None = None,
        argument: dict[str, Any] | None = None,
        outlook: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Every prediction on the site with one status word (src/ai_tracker/board.py)."""
        from . import board
        from .argument import build as build_argument
        from .argument import load as load_argument
        from .outlook import build as build_outlook

        argument = argument if argument is not None else build_argument(self)
        return board.build(
            board.load(),
            self._ledger_rows(),
            outlook if outlook is not None else build_outlook(self),
            argument,
            read_jsonl(DATA / "thesis.jsonl"),
            load_argument()["exits"],
            cards if cards is not None else {},
        )

    def prediction_table(self) -> None:
        """The board's rows as a table the query service copies, so SQL can join a prediction to its reading."""
        import re

        from .format import fmt_line
        from .outlook import build as build_outlook

        ol = build_outlook(self)
        tests = ol.get("tests") or {}

        def plain(text: str) -> str:  # the threshold a [test:] token prints on the page; other tokens drop out
            text = re.sub(
                r"\[test:([a-z0-9_]+)\]",
                lambda m: fmt_line(tests[m[1]]["line"], tests[m[1]]["unit"]) if m[1] in tests else "",
                text,
            )
            return re.sub(r"\s*\[(?:cite|fact|plate):[a-z0-9_]+\]", "", text)

        rows = [r for f in self.board(outlook=ol)["folios"] for r in f["rows"]]
        self.con.execute(
            "CREATE OR REPLACE TABLE predictions (id VARCHAR, kind VARCHAR, folio VARCHAR, stage VARCHAR, row VARCHAR,"
            " who VARCHAR, attribution VARCHAR, line VARCHAR, state VARCHAR, word VARCHAR, settles VARCHAR,"
            " test_fact VARCHAR, test_op VARCHAR, test_against VARCHAR, reading_value DOUBLE, reading_unit VARCHAR,"
            " reading_as_of VARCHAR, reading_derived_id VARCHAR, obs_ids VARCHAR[], indicators VARCHAR[], sources VARCHAR[],"
            " href VARCHAR)"
        )
        for r in rows:
            t, rd = r.get("test") or {}, r.get("reading") or {}
            self.con.execute(
                "INSERT INTO predictions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    r["id"], r["kind"], r["folio"], r.get("stage"), r.get("row"), r["who"], r["attribution"],
                    plain(r["line"]), r["state"], r["word"], None if r["settles"] is None else plain(str(r["settles"])),
                    t.get("fact"), t.get("op"), None if t.get("against") is None else str(t["against"]),
                    rd.get("value") if isinstance(rd.get("value"), (int, float)) else None, rd.get("unit"),
                    rd.get("as_of"), rd.get("derived_id"), rd.get("obs_ids") or [], r["indicators"], r["sources"], r["href"],
                ],
            )

    def _card(self, ind: Indicator) -> dict[str, Any]:
        pts = self.headline(ind)
        ev = self.current(ind.id)
        latest = pts[-1] if pts else None
        ev_obs = self.evidence_obs(ind)
        # the status is read off the band input, which is often a fit rather than the latest point; say so on
        # the card unless they are the same number
        bi = self.band_input(ind)
        band_value = (
            {
                "value": bi[0],
                "unit": self.band_unit(ind),
                "as_of": bi[1].isoformat() if bi[1] else None,
                "obs_ids": bi[2],
            }
            if bi[0] is not None
            and ind.band_input
            and ind.band_input.startswith("metric:")
            and not (latest and latest.get("value") == bi[0])
            else None
        )
        stale = latest["as_of"] if latest and is_stale(latest["as_of"], ind.cadence_expected) else None
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
            "band_value": band_value,
            "grade": _best_grade(ev_obs),
            "latest": latest,
            "spark": _spark(pts),
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
                    "n_indicators": len(mine),
                    "status": _summarise(flow),
                    "tally": _tally(flow),
                }
            )
        valves = []
        for v in VALVES:
            mine = [i for i in self.seed.indicators if i.valve_measured == v["id"] and i.published]
            flow = [cards[i.id] for i in mine if not i.direction_rule]
            valves.append(
                {
                    **v,
                    "status": _summarise(flow),
                    "tally": _tally(flow),
                    "indicator_ids": [i.id for i in mine],
                }
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
            # how many sources the stage statuses rest on (flow indicators only: a capture card on a stage page does not
            # vote); each stage's page names them, indicator by indicator
            "n_sources": len(
                self._chart_sources(
                    [
                        i
                        for ind in self.seed.indicators
                        if ind.published
                        and ind.bucket_id
                        and not ind.direction_rule
                        and cards[ind.id].get("latest")
                        for i in cards[ind.id]["latest"]["obs_ids"]
                    ]
                )["sources"]
            ),
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

    def _derived_href(self, d: Derived) -> str:
        """A derived number's record: its row in the derived table of the published indicator that reads it (every
        input listed there), else the metric's saved analysis on /query."""
        ind = next(
            (
                i
                for i in self.seed.indicators
                if i.published
                and i.metric == d.metric
                and all(d.dims.get(k) == v for k, v in (i.metric_dims or {}).items())
            ),
            None,
        )
        return f"/indicators/{ind.id}#d-{d.id}" if ind else f"/query#{d.metric}"

    def _profit_stack(self, metric: str, parts: list[tuple[str, str]]) -> dict[str, Any]:
        """One stacked column per calendar quarter, shares from the bottom in `parts` order, laid out here so the
        page only draws: each part's height, place, stamp and record. A quarter with no row stays on the axis as a
        gap, never closed up. A share is as firm as the weakest figure in its total, so every part of a quarter
        whose total includes an estimate is an estimate; the part that is itself estimated is the hatched one."""
        rows = [r for r in self.derived_for(metric) if r.dims.get("layer_id") in {pid for pid, _ in parts}]
        empty = {
            "quarters": [],
            "axis": None,
            "keys": [],
            "ends": [],
            "stamps": [],
            "sources": self._chart_sources([], metric),
        }
        if not rows:
            return empty
        spine = [min(r.as_of_date for r in rows)]
        while spine[-1] < max(r.as_of_date for r in rows):
            spine.append(_next_quarter_end(spine[-1]))
        off = sorted({r.as_of_date for r in rows} - set(spine))
        if (
            off
        ):  # a formula that dates a row off a quarter end would drop it silently; fail the export instead
            raise ValueError(f"{metric}: rows dated off a quarter end: {off[:3]}")
        slot, quarters, alt = 100 / len(spine), [], False
        for i, q in enumerate(spine):
            cum, col = 0.0, []
            for pid, name in parts:
                r = next((r for r in rows if r.as_of_date == q and r.dims.get("layer_id") == pid), None)
                if r is None:
                    continue
                bottom = 100 - 100 * cum
                cum += r.value
                top = round(100 - 100 * cum, 2)
                col.append(
                    {
                        "id": pid,
                        "name": name,
                        "value": r.value,
                        "unit": "share",
                        "as_of": q.isoformat(),
                        "obs_ids": r.input_observation_ids,
                        "estimated": r.dims.get("basis") == "estimated",
                        "stamp": self.stamp_of(r.input_observation_ids),
                        "href": self._derived_href(r),
                        "y": top,
                        "height": round(bottom - top, 2),
                    }
                )
            yearly = i == 0 or q.month == 3  # a phone keeps the first label and each first quarter's
            alt = False if yearly else not alt
            quarters.append(
                {
                    "as_of": q.isoformat(),
                    "name": f"Q{(q.month - 1) // 3 + 1} {q.year}",
                    "label": f"Q{(q.month - 1) // 3 + 1}" + (f" {q.year}" if yearly else ""),
                    "minor": len(spine) > 5 and not yearly and alt,
                    "x": round(i * slot + slot * 0.14, 2),
                    "cx": round(i * slot + slot / 2, 2),
                    "width": round(slot * 0.72, 2),
                    "parts": col,
                }
            )
        newest = next((q for q in reversed(quarters) if q["parts"]), None)
        if newest is None:
            return empty
        mids = [p["y"] + p["height"] / 2 for p in newest["parts"]]
        order = sorted(range(len(mids)), key=lambda k: mids[k])
        placed = dict(zip(order, chart.spread([mids[k] for k in order], 7.0)))
        return {
            "quarters": quarters,
            "axis": {
                "ticks": [
                    {"y": y, "label": label} for y, label in ((0.0, "100%"), (50.0, "50%"), (100.0, "0%"))
                ],
                "unit": None,
                "log": False,
                "chars": 4,
            },
            # which parts appear, and which is itself an estimate (hatched), for the key strip
            "keys": [
                {
                    "id": pid,
                    "name": name,
                    "estimate": any(p["estimated"] for qq in quarters for p in qq["parts"] if p["id"] == pid),
                }
                for pid, name in parts
                if any(p["id"] == pid for qq in quarters for p in qq["parts"])
            ],
            # the newest column's shares, labelled beside it and spread so thin parts never collide
            "ends": [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "value": p["value"],
                    "unit": "share",
                    "as_of": p["as_of"],
                    "obs_ids": p["obs_ids"],
                    "y": placed[k],
                }
                for k, p in enumerate(newest["parts"])
            ],
            "stamps": sorted(
                {p["stamp"] for qq in quarters for p in qq["parts"] if p["stamp"]}, key=STAMPS.index
            ),
            "sources": self._chart_sources([i for r in rows for i in r.input_observation_ids], metric),
        }

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

        doc = {
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
        for layer in doc["layers"]:  # the counts a page prints, so the page counts nothing
            for sl in layer["sublayers"]:
                sl["n_entities"] = len(sl["entities"])
                sl["n_verified"] = sum(1 for e in sl["entities"] if e["verified"])
                sl["n_indicators"] = len(sl["indicators"])
        return doc

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
                "sql": _formula(metrics.get(a["metric"], {})),
            }
            for a in spec
        ]

    def _signposts(self) -> dict[str, Any]:
        """Capability signposts (Part 11, section B): each test's record on one percent scale with the date of its
        newest row, so a record nobody has challenged in a year shows as stale; and HAL's accuracy and reliability
        for each agent by release date. No status: a signpost is dated and tested only through claims."""
        spec = yaml.safe_load((SEED / "signposts.yaml").read_text())
        rows = self.derived_for("benchmark_frontier")
        newest = {
            f"{ns}.{m}": d
            for ns, m, d in self.con.execute(
                "SELECT source_ns, measure, max(as_of_date) FROM observations WHERE source_ns IN "
                "('epoch_bench', 'hal_reliability') AND grain = 'pt' AND NOT coalesce(disputed, false) GROUP BY 1, 2"
            ).fetchall()
        }
        today, tests = date.today(), []
        for t in spec["tests"]:
            recs = [r for r in rows if r.dims.get("test") == t["test"]]
            if not recs:
                continue
            rec, new = recs[-1], newest[t["test"]]
            tests.append(
                {
                    **t,
                    "value": rec.value,
                    "unit": "share",
                    "as_of": rec.as_of_date.isoformat(),
                    "obs_ids": rec.input_observation_ids,
                    "href": self.href_of(rec.input_observation_ids),
                    "stamp": self.stamp_of(rec.input_observation_ids),
                    "newest": new.isoformat(),
                    "stale": (today - new).days > spec["stale_after_days"],
                    "x": round(100 * rec.value, 2),
                }
            )
        tests.sort(key=lambda t: (-t["value"], t["test"]))  # the jagged edge, from furthest along to least
        return {
            "stale_after_days": spec["stale_after_days"],
            "tests": tests,
            "axis": {"ticks": [{"x": v, "label": f"{v}%"} for v in (0, 25, 50, 75, 100)]},
            "reliability": self._hal_gap(),
            "chart_sources": self._chart_sources(
                [i for t in tests for i in t["obs_ids"]], "benchmark_frontier"
            ),
        }

    def _hal_gap(self) -> dict[str, Any] | None:
        """HAL's accuracy and overall reliability for each agent, by its model's release, with a straight-line trend
        through each. Both run from 0 to 1 but measure different things, so the figure is read by its slopes, not its
        heights. Each line runs through the mean of exactly the rows `hal_trend_per_year` fitted, at that slope, and
        its record is a row of the figure's own table (`#d-<derived id>`)."""
        pts = [
            {
                "measure": m,
                "unit": unit,
                "as_of": d.isoformat(),
                "value": v,
                "obs_ids": [i],
                "label": json.loads(snip).get("label") or sub,  # HAL's own name for the agent, not our slug
            }
            for i, sub, m, unit, d, v, snip in self.con.execute(
                "SELECT id, subject, measure, unit, as_of_date, value_numeric, raw_snippet FROM observations "
                "WHERE source_ns = 'hal_reliability' AND measure IN ('accuracy', 'reliability') "
                "AND value_numeric IS NOT NULL AND NOT coalesce(disputed, false) ORDER BY as_of_date, subject, measure"
            ).fetchall()
        ]
        if not pts:
            return None
        trends = []
        for d in {d.dims["measure"]: d for d in self.derived_for("hal_trend_per_year")}.values():
            fitted = set(d.input_observation_ids)
            mine = [p for p in pts if p["obs_ids"][0] in fitted]
            if not mine:
                continue
            days = [date.fromisoformat(p["as_of"]).toordinal() for p in mine]
            # a least-squares line runs through the mean of the points it was fitted to
            mid, ybar = sum(days) / len(days), sum(p["value"] for p in mine) / len(mine)
            trends.append(
                {
                    "id": d.id,
                    "measure": d.dims["measure"],
                    "value": d.value,
                    "label": chart.change_label(d.value, "share") + " a year",
                    "as_of": d.as_of_date.isoformat(),
                    "n": len(mine),
                    "obs_ids": d.input_observation_ids,
                    "href": f"#d-{d.id}",
                    "ends": [(t, ybar + d.value * (t - mid) / 365.25) for t in (min(days), max(days))],
                }
            )
        xa = chart.time_axis([date.fromisoformat(p["as_of"]) for p in pts])
        ya = chart.axis(
            [p["value"] for p in pts] + [v for t in trends for _, v in t["ends"]], "index", zero=True
        )
        for p in pts:
            p["x"] = chart.x(date.fromisoformat(p["as_of"]), xa["lo"], xa["hi"])
            p["y"] = chart.y(p["value"], ya)
            p["href"] = self.href_of(p["obs_ids"])
        for t in trends:
            (t1, v1), (t2, v2) = t.pop("ends")
            t["x1"], t["y1"] = chart.x(date.fromordinal(t1), xa["lo"], xa["hi"]), chart.y(v1, ya)
            t["x2"], t["y2"] = chart.x(date.fromordinal(t2), xa["lo"], xa["hi"]), chart.y(v2, ya)
        trends.sort(key=lambda t: t["y2"])
        for t, y in zip(trends, chart.spread([t["y2"] for t in trends], 16.0)):  # two-line labels
            t["label_y"] = y
        return {
            "points": pts,
            "trends": trends,
            "x": {"ticks": xa["ticks"]},
            "y": {
                "ticks": ya["ticks"],
                "log": ya["log"],
                "unit": "score, 0 to 1",
                "chars": max(len(t["label"]) for t in ya["ticks"]),
            },
            "stamps": sorted({self.stamp_of(p["obs_ids"]) for p in pts} - {None}, key=STAMPS.index),
            "chart_sources": self._chart_sources(
                [i for p in pts for i in p["obs_ids"]], "hal_trend_per_year"
            ),
        }

    def _context(self) -> dict[str, Any]:
        """Context figures (seed/context.yaml): official series drawn beside the outlook's claims, with no status.
        Every line on a figure shares one axis. A point read from a metric is a derived row, so its record is its
        row in the figure's own table (`#d-<derived id>`), which links the observations it was computed from: each
        row by series and month, or the series page where a window holds more than a few. A line does not bridge a
        missing period (`joined` false). A name in the seed that matches no metric or series is an error."""
        spec = yaml.safe_load((SEED / "context.yaml").read_text())
        known = set((yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {}).get("metrics", {}))
        pages = {f"buckets/{b.id}" for b in self.seed.buckets} | {f"layers/{x.id}" for x in self.seed.layers}
        start, figures = date.fromisoformat(spec["start"]), []
        for f in spec["figures"]:
            if f.get("page", spec["page"]) not in pages:
                raise ValueError(f"context.yaml {f['id']}: no page {f.get('page', spec['page'])}")
            lines = []
            for ln in f["lines"]:
                if "metric" in ln:
                    if ln["metric"] not in known:
                        raise ValueError(f"context.yaml {f['id']}: no metric {ln['metric']}")
                    rows = [
                        d for d in self.derived_for(ln["metric"], ln.get("dims")) if d.as_of_date >= start
                    ]
                    pts = [
                        {
                            "as_of": d.as_of_date.isoformat(),
                            "value": d.value,
                            "obs_ids": d.input_observation_ids,
                            "id": d.id,
                            "href": f"#d-{d.id}",
                            "inputs": self._input_links(d.input_observation_ids),
                        }
                        for d in rows
                    ]
                else:
                    if not self.con.execute(
                        "SELECT 1 FROM observation_all WHERE series_key = ? LIMIT 1", [ln["series"]]
                    ).fetchone():
                        raise ValueError(f"context.yaml {f['id']}: no series {ln['series']}")
                    pts = [
                        {"as_of": d.isoformat(), "value": v, "obs_ids": [i], "href": self.href_of([i])}
                        for i, d, v in self.con.execute(
                            "SELECT id, as_of_date, value_numeric FROM observations WHERE series_key = ? "
                            "AND as_of_date >= ? AND value_numeric IS NOT NULL AND NOT coalesce(disputed, false) "
                            "ORDER BY as_of_date",
                            [ln["series"], start],
                        ).fetchall()
                    ]
                if pts:  # a metric's rows exist only after `evaluate`; the figure is drawn without the line till then
                    days = [date.fromisoformat(p["as_of"]).toordinal() for p in pts]
                    steps = sorted(b - a for a, b in zip(days, days[1:]))
                    usual = steps[len(steps) // 2] if steps else 0
                    for k, p in enumerate(pts):  # a gap half again the usual step is a missing period
                        p["joined"] = k > 0 and days[k] - days[k - 1] <= 1.5 * usual
                    lines.append({"label": ln["label"], "points": pts})
            if not lines:
                continue
            xa = chart.time_axis([date.fromisoformat(p["as_of"]) for ln in lines for p in ln["points"]])
            ya = chart.axis([p["value"] for ln in lines for p in ln["points"]], f["unit"], zero=f["zero"])
            for ln in lines:
                for p in ln["points"]:
                    p["x"], p["y"] = (
                        chart.x(date.fromisoformat(p["as_of"]), xa["lo"], xa["hi"]),
                        chart.y(p["value"], ya),
                    )
            ends = sorted(lines, key=lambda ln: ln["points"][-1]["y"])
            for ln, y in zip(
                ends, chart.spread([ln["points"][-1]["y"] for ln in ends], 16.0)
            ):  # two-line labels
                ln["label_y"] = y
            ids = [i for ln in lines for p in ln["points"] for i in p["obs_ids"]]
            metrics = ", ".join(dict.fromkeys(ln["metric"] for ln in f["lines"] if "metric" in ln))
            figures.append(
                {
                    **{k: f[k] for k in ("id", "title", "unit", "caption")},
                    "page": f.get("page", spec["page"]),
                    "note": f.get("note", spec["note"]),
                    "lines": lines,
                    "x": {"ticks": xa["ticks"]},
                    "y": {
                        **{k: ya[k] for k in ("ticks", "unit", "log")},
                        "chars": max(len(t["label"]) for t in ya["ticks"]),
                    },
                    "stamps": sorted({self.stamp_of(ids)} - {None}, key=STAMPS.index),
                    "chart_sources": self._chart_sources(ids, metrics or None),
                }
            )
        return {"start": spec["start"], "figures": figures}

    def _input_links(self, ids: list[str]) -> list[dict[str, Any]]:
        """The rows a derived number was computed from, grouped by series: each row by its series and month where a
        series gives three or fewer, else the series page with the count (a twelve-month window gives twelve rows)."""
        rows = self.con.execute(
            "SELECT id, series_key, as_of_date FROM observation_all WHERE id IN ("
            + ",".join("?" * len(ids))
            + ")"
            " ORDER BY series_key, as_of_date",
            ids,
        ).fetchall()
        by: dict[str, list[tuple[str, date]]] = {}
        for i, k, d in rows:
            by.setdefault(k, []).append((i, d))
        out = []
        for k, rs in by.items():
            if len(rs) <= 3:
                out += [{"label": f"{k} {d:%b %Y}", "href": self.href_of([i])} for i, d in rs]
            else:
                out.append({"label": f"{k}, {len(rs)} rows", "href": f"/series/{k}"})
        return out

    def _ladder(self) -> dict[str, Any]:
        """Appendix E rungs with the production and research rows that sit on each, plus the current level."""
        rungs = (yaml.safe_load((SEED / "ladder.yaml").read_text()) or {}).get("rungs", [])
        rows = self.con.execute(
            "SELECT id, series_key, entity_id, as_of_date, value_numeric, tier, url, raw_snippet FROM observations "
            "WHERE series_key LIKE 'cl_ladder.%' ORDER BY as_of_date"
        ).fetchall()

        names = {e.id: e.name for e in self.seed.entities}

        def at(level: int, research: bool) -> list[dict[str, Any]]:
            return [
                {
                    "obs_id": r[0],
                    "subject": r[1].split(".")[1],
                    # a product row is its company's name; a research row is its paper's subject, in words
                    "name": (names.get(r[2]) if not research else None)
                    or r[1].split(".")[1].replace("_", " "),
                    "href": self.href_of([r[0]]),
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
        self._lay_venture(out)
        return {
            k: {
                **v,
                "quarters": v["quarters"],
                "chart_sources": self._chart_sources(
                    [i for q in v["quarters"] for seg in q.get("by_source", []) for i in seg["obs_ids"]],
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

    def _lay_venture(self, docs: dict[str, dict[str, Any]]) -> None:
        """Every strip on one quarter spine, so strips side by side line up and a quarter with no round stays as a
        gap. Equity segments stack by source (Form D below, Epoch above), scaled to the strip's own largest quarter;
        Form D debt is named under its quarter, not drawn into the equity total. Rewrites `quarters` as a list."""
        days = sorted({date.fromisoformat(d) for v in docs.values() for d in v["quarters"]})
        if not days:
            for v in docs.values():
                v["quarters"] = []
            return
        spine = [days[0]]
        while spine[-1] < days[-1]:
            spine.append(_next_quarter_end(spine[-1]))
        slot = 100 / len(spine)
        for v in docs.values():
            equity = {
                d: sum(seg["value"] for seg in q.get("by_source", []) if seg["kind"] == "equity")
                for d, q in v["quarters"].items()
            }
            top = max(equity.values(), default=0.0) or 1.0
            filled = [d.isoformat() for d in spine if equity.get(d.isoformat())]
            keep = {filled[-1], max(filled, key=lambda d: (equity[d], d))} if filled else set()
            quarters, alt = [], False
            for i, day in enumerate(spine):
                q = v["quarters"].get(day.isoformat(), {"as_of": day.isoformat()})
                yearly = i == 0 or day.month == 3
                alt = False if yearly else not alt
                cum = 0.0
                for seg in sorted(
                    q.get("by_source", []),
                    key=lambda seg: (seg["kind"] != "equity", seg["source"] != "formd"),
                ):
                    seg["stamp"] = self.stamp_of(seg["obs_ids"])
                    if seg["kind"] == "equity":
                        cum += seg["value"]
                        seg["y"], seg["height"] = (
                            round(100 - 100 * cum / top, 2),
                            round(100 * seg["value"] / top, 2),
                        )
                q.update(
                    name=f"Q{(day.month - 1) // 3 + 1} {day.year}",
                    label=f"Q{(day.month - 1) // 3 + 1}" + (f" {day.year}" if yearly else ""),
                    minor=len(spine) > 5 and not yearly and alt,
                    x=round(i * slot + slot * 0.14, 2),
                    cx=round(i * slot + slot / 2, 2),
                    width=round(slot * 0.72, 2),
                    top=round(100 - 100 * cum / top, 2) if cum else None,
                    # a phone keeps the value labels of the newest and the largest quarter only
                    label_minor=day.isoformat() not in keep,
                )
                quarters.append(q)
            v["quarters"] = quarters

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
        layer belongs to the other lens. A layer with indicators but no direction rule is not unmeasured."""
        mine = [i for i in self.seed.indicators if i.layer_id == layer.id and i.published]
        directions = [cards[i.id] for i in mine if i.direction_rule]
        status = _summarise(directions)
        if status == "unmeasured" and mine:
            status = "no_capture_rule_yet"
        return {
            **dump(layer),
            "indicators": [cards[i.id] for i in mine],
            "n_published": len(mine),
            "status": status,
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
        status = _summarise(scored)
        if status == "unmeasured" and any(
            i.layer_id == layer.id and i.published for i in self.seed.indicators
        ):
            status = "no_capture_rule_yet"
        status = status.replace("_", " ")

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
            else [
                f"{layer.name} {'has' if status.startswith('no capture rule') else 'is' if status in ('unmeasured', 'not yet measurable') else 'reads'} {status}"
            ]
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


def is_stale(as_of: date | str, cadence: str | None, today: date | None = None) -> bool:
    """Past twice its cadence, or its cadence plus a month, whichever is longer: the publication lag is real."""
    days = CADENCE_DAYS.get(cadence or "")
    if not days:
        return False
    day = date.fromisoformat(as_of[:10]) if isinstance(as_of, str) else as_of
    return ((today or date.today()) - day).days > max(2 * days, days + 30)


def _health(last_success: str | None, cadence: str) -> str:
    """ok within twice the cadence (plus a lag), stale beyond it, never when there is no success at all."""
    if not last_success:
        return "never"
    return "stale" if is_stale(last_success, cadence) else "ok"


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


def _excerpt(body: str, limit: int = 400) -> str:
    """The memo's opening, cut at a sentence or a word rather than mid-word."""
    text = body.split("\n\n")[0].strip()
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    return (cut[: stop + 1] if stop > limit // 2 else cut[: cut.rfind(" ")].rstrip(",;") + "…").strip()


def _formula(m: dict[str, Any]) -> str:
    """A metric's formula as a reader sees it: the fit and its arguments, then the SQL whose rows it runs over."""
    py = m.get("python") and (
        f"python: {m['python']}("
        + ", ".join(f"{k}={v}" for k, v in (m.get("args") or {}).items())
        + ")"
        + (" over the rows of:" if m.get("sql") else "")
    )
    return "\n".join(x for x in (py, m.get("sql")) if x)


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
    status = doc["status"].replace("_", " ")
    if status.startswith("no capture rule"):
        return f"{doc['name'].lower()} ({status})"
    return f"{doc['name'].lower()} {status}{tail}"


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


def _next_quarter_end(q: date) -> date:
    m = q.month + 3
    y, m = q.year + (m - 1) // 12, (m - 1) % 12 + 1
    return date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)


def _spark(pts: list[dict[str, Any]], w: float = 96, h: float = 28) -> dict[str, Any] | None:
    """A card's sparkline as an SVG path in a w × h box: the last 24 readings, scaled to their own range."""
    vs = [p["value"] for p in pts if p["value"] is not None][-24:]
    if len(vs) < 2:
        return None
    lo, hi = min(vs), max(vs)
    xy = [
        (1 + i * (w - 2) / (len(vs) - 1), h / 2 if hi == lo else h - 2 - (v - lo) / (hi - lo) * (h - 4))
        for i, v in enumerate(vs)
    ]
    return {
        "d": " ".join(f"{'M' if i == 0 else 'L'}{a:.1f},{b:.1f}" for i, (a, b) in enumerate(xy)),
        "end": [round(xy[-1][0], 1), round(xy[-1][1], 1)],
    }


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


# the view's key columns are for formulas, not for the web: the key itself is on every row
KEY_COLS = ("source_ns", "measure", "grain")


def _full(o: dict[str, Any]) -> dict[str, Any]:
    return {**_jsonable({k: v for k, v in o.items() if k not in KEY_COLS}), "grade": _grade(o)}


def _jsonable(d: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(d, default=lambda v: v.value if hasattr(v, "value") else str(v)))


def _write(p: Path, doc: Any) -> None:
    p.write_text(json.dumps(doc, sort_keys=True, indent=1, default=str) + "\n")
