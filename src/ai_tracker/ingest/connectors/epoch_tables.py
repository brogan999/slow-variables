"""Epoch AI's other tables (CC BY 4.0): frontier model compute and power, ML hardware price-performance, lowest
inference price at fixed capability, benchmark scores (ECI, ARC-AGI-2, CL-bench) and cumulative chip sales.
One small connector per table so a layout change in one file never blocks the others.
"""

from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from datetime import date

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def _csv(body: bytes, member: str | None = None) -> list[dict[str, str]]:
    if member:
        z = zipfile.ZipFile(io.BytesIO(body))
        name = next(n for n in z.namelist() if n.endswith(member))
        body = z.read(name)
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
            published_date=as_of,
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
    """FP16 tensor FLOP/s per release-price dollar, per accelerator with both fields (ml_hardware.csv)."""

    source_id = "epoch_hardware"
    urls = ["https://epoch.ai/data/ml_hardware.zip"]
    member = "ml_hardware.csv"
    expect_series = ["epoch_hw.*.price_performance_flops_per_usd.pt"]
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
            out.append(
                self.emit(
                    items[0],
                    r,
                    f"epoch_hw.{slug(r['Hardware name'])}.price_performance_flops_per_usd.pt",
                    "FLOP/s per USD",
                    d,
                    f / p,
                    Tier.MODEL_RELEASE,
                    Basis.reported,
                    [
                        "Hardware name",
                        "Manufacturer",
                        "Release date",
                        "Release price (USD)",
                        "Tensor-FP16/BF16 performance (FLOP/s)",
                    ],
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
        for member, measure, col in (
            ("arc_agi_2_external.csv", "arc_agi_2", "Score"),
            ("cl_bench_external.csv", "cl_bench", "Overall"),
        ):
            self.member, self.columns = member, {"Model version", col, "Release date"}
            for r in self.rows(item):
                d, v = _date(r.get("Release date", "")), _num(r.get(col))
                if not d or v is None:
                    continue
                out.append(
                    self.emit(
                        item,
                        r,
                        f"epoch_bench.{slug(r['Model version'])}.{measure}.pt",
                        "share",
                        d,
                        v,
                        Tier.PUBLISHED_ANALYSIS,
                        Basis.reported,
                        ["Model version", "Name", col, "Release date", "Organization", "Cost per task"],
                    )
                )
        return out


class EpochChips(_EpochTable):
    """Cumulative AI chip sales in H100-equivalents by designer, with Epoch's 5th-95th percentile range; incomplete quarters skipped."""

    source_id = "epoch_chips"
    urls = ["https://epoch.ai/data/ai_chip_sales.zip"]
    member = "cumulative_timelines_by_designer.csv"
    expect_series = ["epoch_chips.nvidia.h100e_cumulative.pt"]
    columns = {
        "Chip manufacturer",
        "Start date",
        "End date",
        "Compute estimate in H100e (median)",
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
        return out
