"""Epoch AI's other tables (CC BY 4.0): frontier model compute and power, ML hardware price-performance, lowest
inference price at fixed capability, benchmark scores (ECI, ARC-AGI-2, CL-bench), cumulative chip sales and the
chip components (packaging, logic wafers, memory) those chips consume.
One small connector per table so a layout change in one file never blocks the others.
"""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date
from pathlib import Path

from ...schema import Basis, Extraction, Observation, Review, Tier
from ..base import Connector, LayoutChanged, RawItem, expect, series_key, slug


def _csv(body: bytes, member: str | None = None) -> list[dict[str, str]]:
    if member:
        z = zipfile.ZipFile(io.BytesIO(body))
        # the whole file name, never a suffix: "cumulative_supply_denominators.csv" ends with "supply_denominators.csv"
        names = [n for n in z.namelist() if n == member or n.endswith("/" + member)]
        expect({member} if names else set(), {member}, "zip members")
        body = z.read(names[0])
    return list(csv.DictReader(io.StringIO(body.decode("utf-8", "ignore"))))


def _date(s: str) -> date | None:
    try:
        return date.fromisoformat(s.strip()[:10])
    except ValueError:
        return None


def _num(s: str | None) -> float | None:
    try:
        return float(s) if s not in (None, "") else None
    except ValueError:
        return None


class _EpochTable(Connector):
    kind = "api"
    member: str | None = None
    columns: set[str] = set()

    def rows(self, item: RawItem) -> list[dict[str, str]]:
        rows = _csv(item.body, self.member)
        expect(set(rows[0]) if rows else set(), self.columns, f"{self.source_id} columns")
        return rows

    def emit(
        self,
        item: RawItem,
        r: dict[str, str],
        series_key: str,
        unit: str,
        as_of: date,
        value: float,
        tier: Tier,
        basis: Basis,
        keep: list[str],
        **kw,
    ) -> Observation:
        return self.obs(
            item,
            series_key=series_key,
            unit=unit,
            as_of_date=as_of,
            published_date=kw.pop("published_date", as_of),
            value_numeric=value,
            tier=tier,
            audited_vs_reported=basis,
            extraction_method=Extraction.api,
            raw_snippet=json.dumps({k: r.get(k) for k in keep}, sort_keys=True),
            **kw,
        )


class EpochModels(_EpochTable):
    """Frontier models' training compute (frontier_ai_models.csv) and notable models' training power draw."""

    source_id = "epoch_models"
    urls = ["https://epoch.ai/data/ai_models.zip"]
    expect_series = ["epoch_models.*.training_compute_flop.pt"]
    columns = {"Model", "Publication date", "Training compute (FLOP)", "Confidence"}

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out: list[Observation] = []
        item = items[0]
        self.member = "frontier_ai_models.csv"
        for r in self.rows(item):
            d, v = _date(r.get("Publication date", "")), _num(r.get("Training compute (FLOP)"))
            if not d or not v or d < date(2015, 1, 1):
                continue
            out.append(
                self.emit(
                    item,
                    r,
                    f"epoch_models.{slug(r['Model'])}.training_compute_flop.pt",
                    "FLOP",
                    d,
                    v,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.reported if r.get("Confidence") == "Confident" else Basis.estimated,
                    [
                        "Model",
                        "Organization",
                        "Publication date",
                        "Training compute (FLOP)",
                        "Confidence",
                        "Model accessibility",
                    ],
                )
            )
        self.member = "notable_ai_models.csv"
        self.columns = {"Model", "Publication date", "Training power draw (W)"}
        for r in self.rows(item):
            d, v = _date(r.get("Publication date", "")), _num(r.get("Training power draw (W)"))
            if not d or not v or d < date(2015, 1, 1):
                continue
            out.append(
                self.emit(
                    item,
                    r,
                    f"epoch_models.{slug(r['Model'])}.training_power_w.pt",
                    "W",
                    d,
                    v,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.estimated,
                    ["Model", "Organization", "Publication date", "Training power draw (W)", "Confidence"],
                )
            )
        return out


class EpochHardware(_EpochTable):
    """FP16 tensor FLOP/s and release price, as Epoch publishes them, per accelerator with both (ml_hardware.csv).

    Epoch's own Price-performance column divides its best-precision figure (FP8 or INT8 where it exists), so it
    jumps when a chip adds a lower precision; the FP16 ratio is computed in metrics.yaml instead."""

    source_id = "epoch_hardware"
    urls = ["https://epoch.ai/data/ml_hardware.zip"]
    member = "ml_hardware.csv"
    expect_series = ["epoch_hw.*.fp16_flops.pt", "epoch_hw.*.release_price_usd.pt"]
    columns = {
        "Hardware name",
        "Release date",
        "Release price (USD)",
        "Tensor-FP16/BF16 performance (FLOP/s)",
    }

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for r in self.rows(items[0]):
            d, p, f = (
                _date(r.get("Release date", "")),
                _num(r.get("Release price (USD)")),
                _num(r.get("Tensor-FP16/BF16 performance (FLOP/s)")),
            )
            if not d or not p or not f:
                continue
            hw = slug(r["Hardware name"])
            for measure, unit, value, col in (
                ("fp16_flops", "FLOP/s", f, "Tensor-FP16/BF16 performance (FLOP/s)"),
                ("release_price_usd", "USD", p, "Release price (USD)"),
            ):
                out.append(
                    self.emit(
                        items[0],
                        r,
                        f"epoch_hw.{hw}.{measure}.pt",
                        unit,
                        d,
                        value,
                        Tier.MODEL_RELEASE,
                        Basis.reported,
                        ["Hardware name", "Manufacturer", "Release date", col],
                    )
                )
        return out


class EpochPrices(_EpochTable):
    """Lowest USD per million tokens among models clearing a fixed benchmark threshold, by release date."""

    source_id = "epoch_prices"
    urls = ["https://epoch.ai/data/charts/llm-inference-price-trends/lowest_price_models_data.csv"]
    expect_series = ["epoch_price.gpqa_diamond_gpt_4_0314.lowest_usd_per_mtok.pt"]
    columns = {"Benchmark", "Threshold model", "Model Name", "Release Date", "USD per 1M Tokens"}

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for r in self.rows(items[0]):
            d, v = _date(r.get("Release Date", "")), _num(r.get("USD per 1M Tokens"))
            if not d or not v:
                continue
            out.append(
                self.emit(
                    items[0],
                    r,
                    f"epoch_price.{slug(r['Benchmark'])}_{slug(r['Threshold model'])}.lowest_usd_per_mtok.pt",
                    "USD",
                    d,
                    v,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.reported,
                    [
                        "Benchmark",
                        "Threshold model",
                        "Model Name",
                        "Release Date",
                        "USD per 1M Tokens",
                        "Benchmark score",
                    ],
                )
            )
        return out


EXTERNAL = (  # (member of benchmark_data.zip, measure, score column) for Epoch's compilations of external results
    ("arc_agi_2_external.csv", "arc_agi_2", "Score"),
    ("cl_bench_external.csv", "cl_bench", "Overall"),
)


class EpochBench(_EpochTable):
    """Epoch Capabilities Index (Epoch-run: tier 1) with open/closed split, plus ARC-AGI-2 and CL-bench external results (tier 6)."""

    source_id = "epoch_bench"
    urls = ["https://epoch.ai/data/benchmark_data.zip"]
    expect_series = ["epoch_bench.*.eci_closed.pt", "epoch_bench.*.arc_agi_2.pt"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item, out = items[0], []
        self.member, self.columns = (
            "eci_scores.csv",
            {"Model", "eci", "eci_ci_low", "eci_ci_high", "date", "Accessibility group"},
        )
        for r in self.rows(item):
            d, v = _date(r.get("date", "")), _num(r.get("eci"))
            if not d or v is None:
                continue
            group = {"Open weights": "open", "Closed weights": "closed"}.get(
                r.get("Accessibility group", ""), "other"
            )
            out.append(
                self.emit(
                    item,
                    r,
                    f"epoch_bench.{slug(r['Model'])}.eci_{group}.pt",
                    "index",
                    d,
                    v,
                    Tier.BENCHMARK,
                    Basis.reported,
                    [
                        "Model",
                        "Display name",
                        "eci",
                        "eci_ci_low",
                        "eci_ci_high",
                        "date",
                        "Organization",
                        "Accessibility group",
                    ],
                    value_low=_num(r.get("eci_ci_low")),
                    value_high=_num(r.get("eci_ci_high")),
                )
            )
        seen: set[tuple[str, date]] = set()
        for member, measure, col in EXTERNAL:
            # keyed on Epoch's own row id: one model version recurs across evaluation runs (effort settings,
            # re-tested snapshots), and two rows sharing a key and a date would hide each other in the ledger
            self.member, self.columns = member, {"Model version", col, "Release date", "id"}
            try:  # one missing or reshaped file must not stop the index and the other tests
                rows = self.rows(item)
            except LayoutChanged as e:
                self.errors.append(str(e))
                continue
            for r in rows:
                d, v = _date(r.get("Release date", "")), _num(r.get(col))
                if not d or v is None:
                    continue
                key = series_key("epoch_bench", f"{r['Model version']}_{r['id']}", measure, "pt")
                if (key, d) in seen:
                    self.errors.append(f"{member}: two rows share {key} on {d}")
                    continue
                seen.add((key, d))
                out.append(
                    self.emit(
                        item,
                        r,
                        key,
                        "share",
                        d,
                        v,
                        Tier.PUBLISHED_ANALYSIS,
                        Basis.reported,
                        ["Model version", "Name", col, "Release date", "Organization", "Cost per task", "id"],
                    )
                )
        return out


class EpochChips(_EpochTable):
    """Cumulative AI chip sales by designer, in H100-equivalents and in the megawatts those chips draw, each with
    Epoch's 5th-95th percentile range; incomplete quarters skipped."""

    source_id = "epoch_chips"
    urls = ["https://epoch.ai/data/ai_chip_sales.zip"]
    member = "cumulative_timelines_by_designer.csv"
    expect_series = ["epoch_chips.nvidia.h100e_cumulative.pt"]
    columns = {
        "Chip manufacturer",
        "Start date",
        "End date",
        "Compute estimate in H100e (median)",
        "Power in MW (median)",
        "Incomplete",
    }

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for r in self.rows(items[0]):
            s, e, v = (
                _date(r.get("Start date", "")),
                _date(r.get("End date", "")),
                _num(r.get("Compute estimate in H100e (median)")),
            )
            if not s or not e or not v or r.get("Incomplete", "").strip().lower() == "true":
                continue
            out.append(
                self.emit(
                    items[0],
                    r,
                    f"epoch_chips.{slug(r['Chip manufacturer'])}.h100e_cumulative.pt",
                    "H100e",
                    e,
                    v,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.estimated,
                    [
                        "Name",
                        "Chip manufacturer",
                        "Start date",
                        "End date",
                        "Compute estimate in H100e (median)",
                        "Compute estimate in H100e (5th percentile)",
                        "Compute estimate in H100e (95th percentile)",
                    ],
                    period_start=s,
                    value_low=_num(r.get("Compute estimate in H100e (5th percentile)")),
                    value_high=_num(r.get("Compute estimate in H100e (95th percentile)")),
                )
            )
            mw = _num(r.get("Power in MW (median)"))
            if mw is None:
                continue
            out.append(
                self.emit(
                    items[0],
                    r,
                    series_key("epoch_chips", r["Chip manufacturer"], "power_mw_cumulative", "pt"),
                    "MW",
                    e,
                    mw,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.estimated,
                    [
                        "Name",
                        "Chip manufacturer",
                        "Start date",
                        "End date",
                        "Power in MW (median)",
                        "Power in MW (5th percentile)",
                        "Power in MW (95th percentile)",
                    ],
                    period_start=s,
                    value_low=_num(r.get("Power in MW (5th percentile)")),
                    value_high=_num(r.get("Power in MW (95th percentile)")),
                )
            )
        return out


class EpochComponents(_EpochTable):
    """What AI chips consume, by quarter: each designer's share of advanced packaging (CoWoS), leading-edge logic
    wafers and high-bandwidth memory, and the supply of each. Epoch's estimates with 5th-95th percentile ranges.
    The shares of one input sum to 100 across designers by construction ("Other" is the residual), so a
    consumed-over-supply ratio would always read 1; per-designer wafer counts are not stored for that reason.
    """

    source_id = "epoch_components"
    urls = ["https://epoch.ai/data/ai_chip_components.zip"]
    expect_series = ["epoch_components.nvidia.cowos_share_pct.q", "epoch_components.global.hbm_supply_usd.q"]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item, out = items[0], []
        read_on = item.retrieved_at.date()
        shares = {"cowos": "CoWoS share (%)", "logic": "Logic share (%)", "hbm": "HBM share (%)"}
        self.member = "quarterly_by_designer.csv"
        self.columns = {"Designer", "Start date", "End date"} | {f"{c} (median)" for c in shares.values()}
        for r in self.rows(item):
            s, e = _date(r.get("Start date", "")), _date(r.get("End date", ""))
            if not s or not e or e > read_on:
                continue
            for m, col in shares.items():
                v = _num(r.get(f"{col} (median)"))
                if v is None:  # a quarter Epoch has not finished lists some designers with blank shares
                    continue
                out.append(
                    self.emit(
                        item,
                        r,
                        series_key("epoch_components", r["Designer"], f"{m}_share_pct", "q"),
                        "pct",
                        e,
                        v,
                        Tier.PUBLISHED_ANALYSIS,
                        Basis.estimated,
                        [
                            "Designer",
                            "Quarter",
                            f"{col} (5th percentile)",
                            f"{col} (median)",
                            f"{col} (95th percentile)",
                        ],
                        period_start=s,
                        value_low=_num(r.get(f"{col} (5th percentile)")),
                        value_high=_num(r.get(f"{col} (95th percentile)")),
                    )
                )
        supply = {
            "cowos_supply_wafers": ("CoWoS supply", "wafers"),
            "logic_supply_wafers": ("Logic supply", "wafers"),
            "hbm_supply_usd": ("HBM supply (USD)", "USD"),
        }
        self.member = "supply_denominators.csv"
        # Quarter and Start date are absent from the cumulative file of nearly the same name
        self.columns = {"Quarter", "Start date", "End date"} | {f"{c} (median)" for c, _ in supply.values()}
        for r in self.rows(item):
            s, e = _date(r.get("Start date", "")), _date(r.get("End date", ""))
            if not s or not e or e > read_on:
                continue
            for measure, (col, unit) in supply.items():
                v = _num(r.get(f"{col} (median)"))
                if v is None:
                    continue
                out.append(
                    self.emit(
                        item,
                        r,
                        series_key("epoch_components", "global", measure, "q"),
                        unit,
                        e,
                        v,
                        Tier.PUBLISHED_ANALYSIS,
                        Basis.estimated,
                        ["Quarter", f"{col} (5th percentile)", f"{col} (median)", f"{col} (95th percentile)"],
                        period_start=s,
                        value_low=_num(r.get(f"{col} (5th percentile)")),
                        value_high=_num(r.get(f"{col} (95th percentile)")),
                    )
                )
        return out


PROJECTION = "Epoch's projection: this date had not arrived when the file was read"


class EpochDataCenters(_EpochTable):
    """Epoch's timeline for each large AI data centre it tracks: total facility power in megawatts at dated
    milestones. A past date is Epoch's estimate of what stood there then; a future date is what Epoch expects, and
    is stored with a note saying so. A zero is a reading (a cleared site), not a blank. The status prose beside
    each row runs to a thousand characters and is rewritten monthly, so it is not copied into the snippet.

    Epoch removes and re-dates rows as its estimates change. An append-only ledger would keep those rows for ever,
    so a row that is no longer in the file is flagged disputed (never deleted) and clears if Epoch restores it.

    No Indicator may point at an `epoch_dc` series: its newest row is a projection, not the latest reading.
    """

    source_id = "epoch_datacenters"
    urls = ["https://epoch.ai/data/data_centers/data_centers.zip"]
    member = "data_center_timelines.csv"
    columns = {"Data center", "Date", "Power (MW)"}
    expect_series = ["epoch_dc.*.power_mw.pt"]
    SHRINK = 0.75  # Epoch drops about 7% of rows a month; far fewer than the ledger holds means a broken file

    def __init__(self, ledger: Path = Path("data/observations/epoch_datacenters.jsonl")) -> None:
        super().__init__()
        self.ledger = [json.loads(x) for x in ledger.read_text().splitlines()] if ledger.exists() else []

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item, out, sites = items[0], [], {}
        read_on = item.retrieved_at.date()
        for r in self.rows(item):
            d, v = _date(r.get("Date", "")), _num(r.get("Power (MW)"))
            if d is None or v is None:
                continue
            site = r["Data center"].strip()
            if sites.setdefault(slug(site), site) != site:
                raise LayoutChanged(
                    f"epoch_datacenters: '{site}' and '{sites[slug(site)]}' share a series key"
                )
            out.append(
                self.emit(
                    item,
                    r,
                    series_key("epoch_dc", site, "power_mw", "pt"),
                    "MW",
                    d,
                    v,
                    Tier.PUBLISHED_ANALYSIS,
                    Basis.estimated,
                    ["Data center", "Date", "Power (MW)", "IT power (MW)", "Buildings operational"],
                    published_date=min(d, read_on),
                    note=PROJECTION if d > read_on else None,
                )
            )
        return out + self._withdrawn(out, read_on)

    def _withdrawn(self, tonight: list[Observation], read_on: date) -> list[Observation]:
        """Ledger rows Epoch no longer publishes, re-emitted under their own ids with a dispute flag."""
        superseded = {r["supersedes_id"] for r in self.ledger if r.get("supersedes_id")}
        live = [
            r
            for r in self.ledger
            if r["id"] not in superseded
            and not r.get("disputed")
            and r.get("review_status") == Review.approved.value
        ]
        if len(tonight) < self.SHRINK * len(live):
            raise LayoutChanged(f"epoch_datacenters: {len(tonight)} rows against {len(live)} in the ledger")
        ids = {o.id for o in tonight}
        by_key = {(o.series_key, o.as_of_date.isoformat()): o.id for o in tonight}
        known = {r["id"] for r in self.ledger}
        out = []
        for r in live:
            if r["id"] in ids:
                continue
            now = by_key.get((r["series_key"], r["as_of_date"]))
            if now is None:
                why = f"Absent from Epoch's file when read on {read_on}: removed or re-dated by Epoch."
            elif now in known:
                # ponytail: Epoch went back to a value it published before; the store cannot re-admit that
                # superseded row, so this site-date goes unread. Fix in append_observations if it ever bites.
                why = f"Epoch reverted this value to an earlier figure, as read on {read_on}."
            else:
                continue  # a revised value: the store supersedes this row tonight
            out.append(Observation(**{**r, "disputed": True, "dispute_text": why}))
        return out
