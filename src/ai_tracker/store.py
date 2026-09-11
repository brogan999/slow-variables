"""Seed YAML + data/*.jsonl -> in-memory DuckDB; export -> web/data/*.json. The web never computes a number."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import duckdb
import yaml

from .schema import (
    UNSCORED,
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
        return cls(
            [Bucket(**r) for r in rows("buckets")],
            [Layer(**r) for r in rows("layers")],
            [Sublayer(**r) for r in rows("sublayers")],
            [Crosswalk(**r) for r in rows("crosswalk")],
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


def append_observations(source_id: str, rows: list[Observation]) -> int:
    """Append-only, sorted by id. A changed value for the same key gets a new row that supersedes the old one."""
    p = OBS / f"{source_id}.jsonl"
    existing = read_jsonl(p)
    ids = {r["id"] for r in existing}
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
    for o in rows:
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
        latest[k] = (o.id, o.retrieved_at.isoformat())
        ids.add(o.id)
        new.append(dump(o))
    if new:
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
        self.con = duckdb.connect()
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
        self.derived = [Derived(**r) for r in read_jsonl(DATA / "derived.jsonl")]
        self.events = [StatusEvent(**r) for r in read_jsonl(DATA / "status_events.jsonl")]
        self.fetchlog = [FetchLog(**r) for r in read_jsonl(DATA / "fetchlog.jsonl")]
        self.semantic_tables()

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
                    m.get("sql") or f"python: {m.get('python')}",
                )
                for k, m in spec.items()
            ]
            or [(None,) * 7],
        )
        for t in ("derived", "status_events", "metrics"):
            con.execute(f"DELETE FROM {t} WHERE {'id' if t != 'metrics' else 'name'} IS NULL")

    # ---- queries -------------------------------------------------------------------------------------------
    def observations(self, *globs: str) -> list[dict[str, Any]]:
        cur = self.con.execute("SELECT * FROM observations ORDER BY as_of_date, series_key")
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
                + ", ".join(
                    f"{layer.name.lower()} {status.replace('_', ' ')}"
                    for layer in self.seed.layers
                    for status in [
                        _summarise(
                            [
                                cards[i.id]
                                for i in self.seed.indicators
                                if i.layer_id == layer.id and i.published and i.direction_rule
                            ]  # the capture lens reads directions; a flow status on the same layer belongs to the other lens
                        )
                    ]
                    if status
                )
                + ".",
                "what_would_change": [
                    f"{i.name}: {i.direction_rule.rationale}"
                    for i in self.seed.indicators
                    if i.published and i.layer_id and i.direction_rule
                ],
                "recent_status_events": recent,
                "margin_shares": self._margin_shares(),
                "margin_stack_series": [
                    {
                        "as_of": d.as_of_date.isoformat(),
                        "layer_id": d.dims.get("layer_id"),
                        "value": d.value,
                        "obs_ids": d.input_observation_ids,
                    }
                    for d in self.derived_for("margin_stack_share_by_layer")
                ],
                "layers": [
                    {
                        **dump(layer),
                        "indicators": [
                            cards[i.id]
                            for i in self.seed.indicators
                            if i.layer_id == layer.id and i.published
                        ],
                        "status": _summarise(
                            [
                                cards[i.id]
                                for i in self.seed.indicators
                                if i.layer_id == layer.id and i.published and i.direction_rule
                            ]
                        ),
                    }
                    for layer in self.seed.layers
                ],
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
        (out / "meta.json").write_text(
            json.dumps({"generated_at": datetime.now(timezone.utc).isoformat()}) + "\n"
        )

    def _card(self, ind: Indicator) -> dict[str, Any]:
        pts = self.headline(ind)
        ev = self.current(ind.id)
        latest = pts[-1] if pts else None
        tiers = [Tier(o["tier"]) for o in self.evidence_obs(ind)]
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
            "grade": _grade(min(tiers)) if tiers else None,
            "latest": latest,
            "sparkline": pts[-24:],
            "stale_as_of": None if ind.stale_ok else stale,
            "stale_reason": ind.stale_reason,
            "pending": self._awaiting().get(ind.id),
            "n_observations": len(self.evidence_obs(ind)),
        }

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
            inds = [cards[i.id] for i in self.seed.indicators if i.bucket_id == b.id and i.published]
            buckets.append({**dump(b), "indicators": inds, "status": _summarise(inds)})
        valves = []
        for v in VALVES:
            inds = [cards[i.id] for i in self.seed.indicators if i.valve_measured == v["id"] and i.published]
            valves.append({**v, "status": _summarise(inds), "indicator_ids": [i["id"] for i in inds]})
        verdict = (
            "As of %s: " % as_of
            + ", ".join(f"{b['name'].lower()} {b['status'].replace('_', ' ')}" for b in buckets)
            + "."
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

    def _margin_shares(self) -> dict[str, Any]:
        """Latest complete quarter of margin_stack_share_by_layer, keyed by layer id, with provenance."""
        rows = self.derived_for("margin_stack_share_by_layer")
        if not rows:
            return {}
        latest = max(r.as_of_date for r in rows)
        return {
            r.dims["layer_id"]: {
                "value": r.value,
                "as_of": latest.isoformat(),
                "obs_ids": r.input_observation_ids,
            }
            for r in rows
            if r.as_of_date == latest
        }

    def evidence_for(self, *targets: str) -> list[dict[str, Any]]:
        """Dated evidence records: observations whose series is evidence.<target>.<for|against|context>.pt."""
        if not targets:
            return []
        rows = self.con.execute(
            "SELECT id, series_key, as_of_date, value_text, url, tier, source_id, raw_snippet, entity_id FROM observations "
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
        return {
            k: {**v, "quarters": [v["quarters"][d] for d in sorted(v["quarters"])]} for k, v in out.items()
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

        return {
            "sections": self.seed.sections,
            "essays": [dump(e) for e in self.seed.essays],
            "items": [{**dump(b), "related": rel(b)} for b in self.seed.bottlenecks],
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
            rows.append(
                {
                    **r.model_dump(),
                    "card": c,
                    "leans": LEAN.get(c["status"] or "", "open") if c["published"] else "open",
                    "nk_predictions": [pred(p) for p in r.nk_predictions],
                    "ai2027_predictions": [pred(p) for p in r.ai2027_predictions],
                }
            )
        tally = {k: sum(1 for x in rows if x["leans"] == k) for k in ("nk", "ai2027", "open")}
        return {"rows": rows, "tally": tally}

    def _ledger(self) -> list[dict[str, Any]]:
        """The circular / vendor-financing ledger: every `circular.*` and `markets.*` observation with parties and instrument."""
        rows = []
        for o in self.observations("circular.*", "markets.*"):
            parts = o["series_key"].split(".")
            parties = parts[1].split("_") if parts[0] == "circular" else [parts[1]]
            instrument = parts[2].rsplit("_", 1)[0] if parts[0] == "circular" else parts[2]
            rows.append({**_full(o), "parties": parties, "instrument": instrument, "obs_id": o["id"]})
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


def _grade(t: Tier) -> str:
    from .schema import grade_from_tier

    return grade_from_tier(t)


def _summarise(cards: list[dict[str, Any]]) -> str:
    """Mode of the scored statuses; unscored ones (emerging, not yet measurable) never outvote a scored reading."""
    statuses = [c["status"] for c in cards if c.get("status")]
    if not statuses:
        return "unmeasured"
    scored = [x for x in statuses if x not in UNSCORED]
    if not scored:
        return "emerging" if "emerging" in statuses else statuses[0]
    statuses = scored
    counts = sorted(((statuses.count(x), x) for x in set(statuses)), reverse=True)
    if len(counts) > 1 and counts[0][0] == counts[1][0]:
        return "mixed"  # no majority: say so rather than pick one
    return counts[0][1]


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
        "grade": _grade(Tier(o["tier"])),
    }


def _full(o: dict[str, Any]) -> dict[str, Any]:
    return {**_jsonable(o), "grade": _grade(Tier(o["tier"]))}


def _jsonable(d: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(d, default=lambda v: v.value if hasattr(v, "value") else str(v)))


def _write(p: Path, doc: Any) -> None:
    p.write_text(json.dumps(doc, sort_keys=True, indent=1, default=str) + "\n")
