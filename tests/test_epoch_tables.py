import io
import json
import zipfile
from datetime import date, datetime, timezone

import pytest

from ai_tracker.ingest.base import LayoutChanged, RawItem
from ai_tracker.ingest.connectors.epoch_tables import (
    PROJECTION,
    EpochBench,
    EpochChips,
    EpochComponents,
    EpochDataCenters,
    EpochPrices,
)
from ai_tracker.schema import Tier


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
            "arc_agi_2_external.csv": "Model version,Score,Release date,Organization,Name,Cost per task,id\ngpt-6-astra_max,0.95,2026-09-03,OpenAI,GPT-6 Astra,,recA1\n",
            "cl_bench_external.csv": "Model version,Overall,Release date,Organization,Name,id\nMiniMax-M2.5,0.114,2026-02-12,MiniMax,MiniMax M2.5,recC1\n",
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
        rows["epoch_bench.gpt_6_astra_max_reca1.arc_agi_2.pt"].value_numeric == 0.95
        and rows["epoch_bench.gpt_6_astra_max_reca1.arc_agi_2.pt"].tier == 6
    )
    assert rows["epoch_bench.minimax_m2_5_recc1.cl_bench.pt"].value_numeric == 0.114


ECI = "epoch_capabilities_index/eci_scores.csv"
ECI_ROWS = "Model,Display name,eci,eci_ci_low,eci_ci_high,date,Organization,Accessibility group\nkimi-k3,Kimi K3,150.1,145,155,2026-05-01,Moonshot,Open weights\n"
ARC_HEAD = "Model version,Score,Release date,Organization,Name,Cost per task,id\n"
CL = "Model version,Overall,Release date,Organization,Name,id\nMiniMax-M2.5,0.114,2026-02-12,MiniMax,MiniMax M2.5,recC1\n"


def test_two_runs_of_one_model_version_on_one_day_are_both_kept():
    # Epoch lists Opus 5 at Max and High effort under one model version; keyed by version, the second hid the first
    z = _zip(
        {
            ECI: ECI_ROWS,
            "arc_agi_2_external.csv": ARC_HEAD
            + "claude-opus-5_max,0.9042,2026-07-24,Anthropic,Claude Opus 5 (Max),,recMax\n"
            + "claude-opus-5_max,0.8833,2026-07-24,Anthropic,Claude Opus 5 (High),,recHigh\n",
            "cl_bench_external.csv": CL,
        }
    )
    c = EpochBench()
    arc = sorted(r.value_numeric for r in c.extract([_item(z)]) if r.series_key.endswith(".arc_agi_2.pt"))
    assert arc == [0.8833, 0.9042] and not [e for e in c.errors if "two rows share" in e]


def test_a_missing_or_reshaped_test_file_is_an_error_and_the_rest_still_read():
    c = EpochBench()
    z = _zip({ECI: ECI_ROWS, "arc_agi_2_external.csv": "Model version,Score,Release date\nx,0.5,2026-01-01\n"})
    keys = {r.series_key for r in c.extract([_item(z)])}
    assert keys == {"epoch_bench.kimi_k3.eci_open.pt"}
    assert any("id" in e for e in c.errors) and any("cl_bench_external.csv" in e for e in c.errors)


def test_an_identical_repeat_is_one_row_and_a_conflicting_one_is_an_error():
    row = "gpt-6-astra_max,0.95,2026-09-03,OpenAI,GPT-6 Astra,,recA1\n"
    c = EpochBench()  # SciCode's file repeats three rows word for word: one row, nothing to report
    z = _zip({ECI: ECI_ROWS, "arc_agi_2_external.csv": ARC_HEAD + row + row, "cl_bench_external.csv": CL})
    assert sum(r.series_key.endswith(".arc_agi_2.pt") for r in c.extract([_item(z)])) == 1
    assert not [e for e in c.errors if "two rows share" in e]
    c = EpochBench()  # the same run with a different score is a conflict the ledger would hide: say so
    other = row.replace(",0.95,", ",0.91,")
    z = _zip({ECI: ECI_ROWS, "arc_agi_2_external.csv": ARC_HEAD + row + other, "cl_bench_external.csv": CL})
    assert sum(r.series_key.endswith(".arc_agi_2.pt") for r in c.extract([_item(z)])) == 1
    assert any("two rows share" in e for e in c.errors)


def test_the_new_tests_are_read_with_their_keys_tiers_and_run_dates():
    z = _zip(
        {
            ECI: ECI_ROWS,
            "arc_agi_2_external.csv": ARC_HEAD,
            "cl_bench_external.csv": CL,
            # Epoch runs FrontierMath itself: tier 1, published when the run started
            # (never before the model's release: a pre-release run is published on release day)
            "frontiermath_tier_4_v2.csv": "Model version,mean_score,Best score (across scorers),Release date,Started at,id\n"
            "gpt-6-astra_high,0.9,0.976,2026-09-03,2026-09-05T10:00:00,recF1\n"
            "gpt-6-astra_low,0.8,0.9,2026-09-03,2026-08-20T10:00:00,recF2\n",
            # FrontierSWE carries no row id: its model version and harness name the run
            "frontierswe_external.csv": "Model version,Harness,Score,Release date,Name\n"
            "gpt-6-astra_max,proximus,0.655,2026-09-03,GPT-6 Astra\ngpt-6-astra_max,codex,0.61,2026-09-03,GPT-6 Astra\n",
        }
    )
    c = EpochBench()
    rows = {r.series_key: r for r in c.extract([_item(z)])}
    fm = rows["epoch_bench.gpt_6_astra_high_recf1.frontiermath_t4.pt"]
    assert (fm.tier, fm.published_date, fm.value_numeric) == (Tier.BENCHMARK, date(2026, 9, 5), 0.976)
    assert rows["epoch_bench.gpt_6_astra_low_recf2.frontiermath_t4.pt"].published_date == date(2026, 9, 3)
    swe = rows["epoch_bench.gpt_6_astra_max_proximus.frontierswe.pt"]
    assert swe.tier == Tier.PUBLISHED_ANALYSIS and "proximus" in swe.raw_snippet
    assert rows["epoch_bench.gpt_6_astra_max_codex.frontierswe.pt"].value_numeric == 0.61  # a second harness, kept
    assert any("apex_agents_external.csv" in e for e in c.errors)  # a file not in this zip is named, not fatal


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


DC_HEAD = "Data center,Date,Construction status,Buildings operational,IT power (MW),Power (MW)\n"


def _dc(rows: str, ledger: list[dict] | None = None, tmp_path=None) -> list:
    p = tmp_path / "epoch_datacenters.jsonl"
    p.write_text("".join(json.dumps(r) + "\n" for r in ledger or []))
    z = _zip({"data_center_timelines.csv": DC_HEAD + rows})
    return EpochDataCenters(ledger=p).extract([_item(z)])  # read on 2026-09-11


def _ledger(obs: list, **changes) -> list[dict]:
    return [{**json.loads(o.model_dump_json()), **changes} for o in obs]


def test_datacentres_keep_zeros_mark_projections_and_drop_the_status_prose(tmp_path):
    rows = _dc(
        "Hyperion,2026-06-01,Land cleared and a very long status note,0,0.0,0.0\n"
        "Hyperion,2028-01-01,Expected online,4,1700,2262\n"
        "Cedar Rapids,2026-04-16,Blank power,1,,\n",
        tmp_path=tmp_path,
    )
    assert [(r.series_key, r.as_of_date, r.value_numeric) for r in rows] == [
        ("epoch_dc.hyperion.power_mw.pt", date(2026, 6, 1), 0.0),  # a cleared site is a reading, not a blank
        ("epoch_dc.hyperion.power_mw.pt", date(2028, 1, 1), 2262.0),
    ]
    built, planned = rows
    assert built.note is None and built.published_date == date(2026, 6, 1)
    assert planned.note == PROJECTION and planned.published_date == date(2026, 9, 11)  # never a future date
    assert (planned.unit, int(planned.tier), planned.audited_vs_reported.value) == ("MW", 6, "estimated")
    assert "status note" not in built.raw_snippet and "Construction status" not in built.raw_snippet


def test_a_row_epoch_removes_is_disputed_once_and_clears_if_it_returns(tmp_path):
    rest = "".join(
        f"S{i},2026-01-01,s,1,8,10\n" for i in range(4)
    )  # enough rows that losing one is ordinary churn
    both = rest + "B,2026-02-01,s,1,40,50\n"
    first = _dc(both, tmp_path=tmp_path)
    b = first[-1]
    gone = _dc(rest, ledger=_ledger(first), tmp_path=tmp_path)
    flagged = [r for r in gone if r.disputed]
    assert [r.series_key for r in flagged] == ["epoch_dc.b.power_mw.pt"] and flagged[0].id == b.id
    assert "removed or re-dated" in flagged[0].dispute_text and "2026-09-11" in flagged[0].dispute_text
    after = _ledger(first[:-1]) + _ledger([b], disputed=True, dispute_text=flagged[0].dispute_text)
    assert not [
        r for r in _dc(rest, ledger=after, tmp_path=tmp_path) if r.disputed
    ]  # flagged once, not nightly
    back = _dc(
        both, ledger=after, tmp_path=tmp_path
    )  # Epoch restores the row: emitted clean, so the flag clears
    assert [(r.id, r.disputed) for r in back][-1] == (b.id, False) and not any(r.disputed for r in back)


def test_a_revised_value_is_left_for_the_store_to_supersede_and_a_revert_disputes_the_live_row(tmp_path):
    a = _dc("A,2026-01-01,s,1,80,100\n", tmp_path=tmp_path)
    revised = _dc("A,2026-01-01,s,1,80,120\n", ledger=_ledger(a), tmp_path=tmp_path)
    assert len(revised) == 1 and not revised[0].disputed and revised[0].id != a[0].id  # never "removed"
    ledger = _ledger(a) + _ledger(revised, supersedes_id=a[0].id)
    reverted = _dc("A,2026-01-01,s,1,80,100\n", ledger=ledger, tmp_path=tmp_path)  # A, then B, then A again
    flagged = [r for r in reverted if r.disputed]
    assert [r.id for r in flagged] == [revised[0].id] and "reverted" in flagged[0].dispute_text


def test_a_shrunken_file_or_two_names_for_one_site_withdraw_nothing(tmp_path):
    five = "".join(f"S{i},2026-01-01,s,1,8,10\n" for i in range(5))
    ledger = _ledger(_dc(five, tmp_path=tmp_path))
    with pytest.raises(LayoutChanged, match="rows against"):
        _dc("S0,2026-01-01,s,1,8,10\n", ledger=ledger, tmp_path=tmp_path)
    with pytest.raises(LayoutChanged, match="share a series key"):
        _dc("Meta Hyperion,2026-01-01,s,1,8,10\nMeta  hyperion,2026-02-01,s,1,8,10\n", tmp_path=tmp_path)


def test_the_ledger_flags_a_withdrawn_row_in_place_and_clears_it_on_return(tmp_path, monkeypatch):
    from ai_tracker import store as st

    monkeypatch.setattr(st, "OBS", tmp_path)
    rest = "".join(f"S{i},2026-01-01,s,1,8,10\n" for i in range(4))
    ledger = tmp_path / "epoch_datacenters.jsonl"

    def night(rows: str) -> list[dict]:
        z = _zip({"data_center_timelines.csv": DC_HEAD + rows})
        st.append_observations("epoch_datacenters", EpochDataCenters(ledger=ledger).extract([_item(z)]))
        return st.read_jsonl(ledger)

    assert len(night(rest + "B,2026-02-01,s,1,40,50\n")) == 5
    after = {r["series_key"]: r for r in night(rest)}
    assert len(after) == 5 and after["epoch_dc.b.power_mw.pt"]["disputed"] is True  # flagged, never deleted
    back = {r["series_key"]: r for r in night(rest + "B,2026-02-01,s,1,40,50\n")}
    assert len(back) == 5 and back["epoch_dc.b.power_mw.pt"]["disputed"] is False
    revised = night(rest + "B,2026-02-01,s,1,40,60\n")
    old, new = sorted(
        (r for r in revised if r["series_key"].endswith(".b.power_mw.pt")), key=lambda r: r["value_numeric"]
    )
    assert new["supersedes_id"] == old["id"] and not old["disputed"] and not new["disputed"]
