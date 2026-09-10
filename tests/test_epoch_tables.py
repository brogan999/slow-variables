import io
import zipfile
from datetime import date, datetime, timezone

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.epoch_tables import EpochBench, EpochChips, EpochPrices


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
            "cumulative_timelines_by_designer.csv": "Name,Chip manufacturer,Start date,End date,Compute estimate in H100e (median),Compute estimate in H100e (5th percentile),Compute estimate in H100e (95th percentile),Incomplete\n"
            "Nvidia total,Nvidia,2022-01-01,2026-06-30,20987084,19000000,23000000,\nNvidia total,Nvidia,2022-01-01,2026-09-30,22160380,20000000,24000000,True\nAMD total,AMD,2024-01-01,2026-06-30,1739995,1515759,1987064,\n"
        }
    )
    rows = EpochChips().extract([_item(z)])
    assert [(r.series_key, r.as_of_date, r.period_start) for r in rows] == [
        ("epoch_chips.nvidia.h100e_cumulative.pt", date(2026, 6, 30), date(2022, 1, 1)),
        ("epoch_chips.amd.h100e_cumulative.pt", date(2026, 6, 30), date(2024, 1, 1)),
    ]
    assert rows[0].value_low == 19000000 and rows[0].value_high == 23000000


def test_prices_key_on_benchmark_and_threshold():
    csv_body = b'Benchmark,Threshold model,Performance range,Model Name,Release Date,USD per 1M Tokens,Predicted log price,Benchmark score\nGPQA Diamond,GPT-4-0314,"[0.35, inf]",Gemini 2.0 Flash,2025-02-05,0.175,0.2,0.6\n'
    rows = EpochPrices().extract([_item(csv_body)])
    assert (
        rows[0].series_key == "epoch_price.gpqa_diamond_gpt_4_0314.lowest_usd_per_mtok.pt"
        and rows[0].value_numeric == 0.175
        and rows[0].as_of_date == date(2025, 2, 5)
    )
