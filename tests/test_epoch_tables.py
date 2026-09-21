import io
import zipfile
from datetime import date, datetime, timezone

import pytest

from ai_tracker.ingest.base import LayoutChanged, RawItem
from ai_tracker.ingest.connectors.epoch_tables import EpochBench, EpochChips, EpochComponents, EpochPrices


def _item(body: bytes) -> RawItem:
    return RawItem("u", body, 200, datetime(2026, 9, 11, tzinfo=timezone.utc), "h", None)


def _zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, t in files.items():
            z.writestr(n, t)
    return buf.getvalue()


def test_bench_splits_eci_by_accessibility_and_reads_external_scores():
    z = _zip(
        {
            "epoch_capabilities_index/eci_scores.csv": "Model,Display name,eci,eci_ci_low,eci_ci_high,date,Organization,Accessibility group\n"
            "gpt-6-astra,GPT-6 Astra,166.57,160,170,2026-09-03,OpenAI,Closed weights\nkimi-k3,Kimi K3,150.1,145,155,2026-05-01,Moonshot,Open weights\n",
            "arc_agi_2_external.csv": "Model version,Score,Release date,Organization,Name,Cost per task\ngpt-6-astra_max,0.95,2026-09-03,OpenAI,GPT-6 Astra,\n",
            "cl_bench_external.csv": "Model version,Overall,Release date,Organization,Name\nMiniMax-M2.5,0.114,2026-02-12,MiniMax,MiniMax M2.5\n",
        }
    )
    rows = {r.series_key: r for r in EpochBench().extract([_item(z)])}
    eci = rows["epoch_bench.gpt_6_astra.eci_closed.pt"]
    assert (
        eci.value_numeric == 166.57
        and eci.value_low == 160
        and eci.tier == 1
        and eci.as_of_date == date(2026, 9, 3)
    )
    assert "epoch_bench.kimi_k3.eci_open.pt" in rows
    assert (
        rows["epoch_bench.gpt_6_astra_max.arc_agi_2.pt"].value_numeric == 0.95
        and rows["epoch_bench.gpt_6_astra_max.arc_agi_2.pt"].tier == 6
    )
    assert rows["epoch_bench.minimax_m2_5.cl_bench.pt"].value_numeric == 0.114


def test_chips_skip_incomplete_quarters_and_keep_ranges():
    z = _zip(
        {
            "cumulative_timelines_by_designer.csv": "Name,Chip manufacturer,Start date,End date,Compute estimate in H100e (median),Compute estimate in H100e (5th percentile),Compute estimate in H100e (95th percentile),Power in MW (5th percentile),Power in MW (median),Power in MW (95th percentile),Incomplete\n"
            "Nvidia total,Nvidia,2022-01-01,2026-06-30,20987084,19000000,23000000,9000,10918,12500,\nNvidia total,Nvidia,2022-01-01,2026-09-30,22160380,20000000,24000000,9500,11500,13000,True\nAMD total,AMD,2024-01-01,2026-06-30,1739995,1515759,1987064,,,,\n"
        }
    )
    rows = EpochChips().extract([_item(z)])
    assert [(r.series_key, r.as_of_date, r.period_start) for r in rows] == [
        ("epoch_chips.nvidia.h100e_cumulative.pt", date(2026, 6, 30), date(2022, 1, 1)),
        ("epoch_chips.nvidia.power_mw_cumulative.pt", date(2026, 6, 30), date(2022, 1, 1)),
        (
            "epoch_chips.amd.h100e_cumulative.pt",
            date(2026, 6, 30),
            date(2024, 1, 1),
        ),  # no power figure, no row
    ]
    assert rows[0].value_low == 19000000 and rows[0].value_high == 23000000
    assert (rows[1].unit, rows[1].value_numeric, rows[1].value_low, rows[1].value_high) == (
        "MW",
        10918,
        9000,
        12500,
    )


DESIGNER_HEAD = "Name,Quarter,Designer,Start date,End date," + ",".join(
    f"{m} share (%) ({p})"
    for m in ("Logic", "CoWoS", "HBM")
    for p in ("5th percentile", "median", "95th percentile")
)
SUPPLY_HEAD = "Quarter,Start date,End date," + ",".join(
    f"{m} ({p})"
    for m in ("Logic supply", "CoWoS supply", "HBM supply (USD)")
    for p in ("5th percentile", "median", "95th percentile")
)


def _components(extra: dict[str, str] | None = None, first: dict[str, str] | None = None) -> bytes:
    return _zip(
        {
            **(first or {}),
            "quarterly_by_designer.csv": DESIGNER_HEAD
            + "\nNVIDIA Q4 2025,Q4 2025,NVIDIA,2025-10-01,2025-12-31,0.1,0.2,0.3,52.2,58.8,66.5,50,55,60"
            + "\nOther Q4 2025,Q4 2025,Other,2025-10-01,2025-12-31,88.3,88.3,88.3,15.7,15.7,15.7,9,9,9"
            + "\nAMD Q1 2026,Q1 2026,AMD,2026-01-01,2026-03-31,,,,,,,,,"  # an unfinished quarter: blank shares
            + "\nAMD Q4 2026,Q4 2026,AMD,2026-10-01,2026-12-31,1,1,1,1,1,1,1,1,1\n",  # a quarter still running
            "supply_denominators.csv": SUPPLY_HEAD
            + "\nQ4 2025,2025-10-01,2025-12-31,1052516,1085023.8,1159144,183750,197812.5,211875,10260000000,11400000000,12540000000\n",
            **(extra or {}),
        }
    )


def test_components_store_shares_in_percent_and_skip_blank_and_running_quarters():
    rows = {r.series_key: r for r in EpochComponents().extract([_item(_components())])}
    assert sorted(rows) == sorted(
        [
            f"epoch_components.{d}.{m}_share_pct.q"
            for d in ("nvidia", "other")
            for m in ("cowos", "logic", "hbm")
        ]
        + [
            f"epoch_components.global.{m}.q"
            for m in ("cowos_supply_wafers", "logic_supply_wafers", "hbm_supply_usd")
        ]
    )
    n = rows["epoch_components.nvidia.cowos_share_pct.q"]
    assert (n.unit, n.value_numeric, n.value_low, n.value_high) == ("pct", 58.8, 52.2, 66.5)
    assert (n.as_of_date, n.period_start, int(n.tier), n.audited_vs_reported.value) == (
        date(2025, 12, 31),
        date(2025, 10, 1),
        6,
        "estimated",
    )
    hbm = rows["epoch_components.global.hbm_supply_usd.q"]
    assert (hbm.unit, hbm.value_numeric) == ("USD", 11400000000)
    assert rows["epoch_components.global.cowos_supply_wafers.q"].unit == "wafers"


def test_a_cumulative_file_of_nearly_the_same_name_is_never_read():
    decoy = {
        "cumulative_supply_denominators.csv": "Cumulative through,Series start date,End date\n2025-12-31,2024-01-01,2025-12-31\n"
    }
    rows = EpochComponents().extract([_item(_components(first=decoy))])
    assert any(r.series_key == "epoch_components.global.hbm_supply_usd.q" for r in rows)
    only_decoy = _zip({"quarterly_by_designer.csv": DESIGNER_HEAD + "\n", **decoy})
    with pytest.raises(LayoutChanged):  # the real member is gone: say so, never read the look-alike
        EpochComponents().extract([_item(only_decoy)])


def test_prices_key_on_benchmark_and_threshold():
    csv_body = b'Benchmark,Threshold model,Performance range,Model Name,Release Date,USD per 1M Tokens,Predicted log price,Benchmark score\nGPQA Diamond,GPT-4-0314,"[0.35, inf]",Gemini 2.0 Flash,2025-02-05,0.175,0.2,0.6\n'
    rows = EpochPrices().extract([_item(csv_body)])
    assert (
        rows[0].series_key == "epoch_price.gpqa_diamond_gpt_4_0314.lowest_usd_per_mtok.pt"
        and rows[0].value_numeric == 0.175
        and rows[0].as_of_date == date(2025, 2, 5)
    )


def test_models_read_frontier_compute_and_notable_power_with_real_headers():
    from ai_tracker.ingest.connectors.epoch_tables import EpochModels

    head = "Model,Publication date,Organization,Training compute (FLOP),Training compute notes,Domain,Confidence,Model accessibility\n"
    z = _zip(
        {
            "frontier_ai_models.csv": head
            + "GPT-5,2025-08-07,OpenAI,5e25,,Language,Confident,API access\n"
            + "AlexNet,2012-09-30,U Toronto,4.7e17,,Vision,Confident,Open weights\n"  # before 2015: skipped
            + "Grok 4,2025-07-09,xAI,5e26,,Language,Likely,API access\n",
            "notable_ai_models.csv": "Model,Publication date,Organization,Training power draw (W),Confidence\nGPT-5,2025-08-07,OpenAI,2.5e8,Likely\n",
        }
    )
    rows = {r.series_key: r for r in EpochModels().extract([_item(z)])}
    assert rows["epoch_models.gpt_5.training_compute_flop.pt"].audited_vs_reported.value == "reported"
    assert rows["epoch_models.grok_4.training_compute_flop.pt"].audited_vs_reported.value == "estimated"
    assert rows["epoch_models.gpt_5.training_power_w.pt"].value_numeric == 2.5e8
    assert not any("alexnet" in k for k in rows)


def test_hardware_stores_fp16_flops_and_price_as_published_with_real_headers():
    from ai_tracker.ingest.connectors.epoch_tables import EpochHardware

    head = "Hardware name,Manufacturer,Type,Release date,Release price (USD),Tensor-FP16/BF16 performance (FLOP/s),Price-performance\n"
    z = _zip(
        {
            "ml_hardware.csv": head
            + "NVIDIA GB300 (Blackwell Ultra),NVIDIA,GPU,2025-08-01,43000,2.5e15,5.8e10\nNo price chip,X,GPU,2025-01-01,,1e15,\n"
        }
    )
    rows = {r.series_key: r.value_numeric for r in EpochHardware().extract([_item(z)])}
    assert rows == {
        "epoch_hw.nvidia_gb300_blackwell_ultra.fp16_flops.pt": 2.5e15,
        "epoch_hw.nvidia_gb300_blackwell_ultra.release_price_usd.pt": 43000,
    }
