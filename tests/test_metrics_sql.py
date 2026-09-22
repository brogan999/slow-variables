from datetime import date, timedelta

import duckdb
import yaml

from ai_tracker.store import CAPEX_TTM, DC_SITES, VENTURE_ROUNDS

METRICS = yaml.safe_load(open("semantic/metrics.yaml"))["metrics"]

# the store's view splits the series key into its four parts; a formula under test reads the same columns
KEY_SPLIT = """CREATE VIEW observations AS SELECT *, split_part(series_key, '.', 1) AS source_ns,
    array_to_string(str_split(series_key, '.')[3:-2], '.') AS measure, str_split(series_key, '.')[-1] AS grain
    FROM obs_raw"""


def run(metric: str, rows: list[tuple]) -> list[tuple]:
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE obs_raw (id VARCHAR, series_key VARCHAR, subject VARCHAR, as_of_date DATE, value_numeric DOUBLE, raw_snippet VARCHAR, disputed BOOLEAN)"
    )
    con.executemany("INSERT INTO obs_raw VALUES (?, ?, ?, ?, ?, ?, false)", rows)
    con.execute(KEY_SPLIT)
    return con.execute(METRICS[metric]["sql"]).fetchall()


def test_change_points_carry_unchanged_prices_forward():
    idx = [
        (f"i{m}", f"aa.{m}.intelligence_index.pt", m, "2026-01-01", v, "")
        for m, v in [("a", 50), ("b", 40)] + [(f"x{k}", 10) for k in range(18)]
    ]
    price = [
        (f"p{m}", f"aa.{m}.price_blended_usd_per_mtok.pt", m, "2026-09-10", 0.01, "")
        for m in (f"x{k}" for k in range(18))
    ]
    price += [  # the decile is taken among priced models: a and b are the top two of twenty
        ("pa1", "aa.a.price_blended_usd_per_mtok.pt", "a", "2026-09-10", 1.0, ""),
        ("pb1", "aa.b.price_blended_usd_per_mtok.pt", "b", "2026-09-10", 0.2, ""),
        (
            "pa2",
            "aa.a.price_blended_usd_per_mtok.pt",
            "a",
            "2026-09-20",
            0.1,
            "",
        ),  # only a changes on the 20th
    ]
    out = {str(d): (v, ids) for d, v, ids in run("aa_frontier_price_per_point", idx + price)}
    assert out["2026-09-10"] == (0.2 / 40, ["pb1", "ib"])
    assert out["2026-09-20"] == (
        0.1 / 50,
        ["pa2", "ia"],
    )  # b's unchanged price still competes, a's new one wins


def test_lab_token_hhi_groups_models_by_author():
    rows = [
        (
            f"t{i}",
            f"openrouter_rankings.m{i}.tokens.d",
            f"m{i}",
            "2026-09-09",
            v,
            f"{lab}/model-{i} 2026-09-09",
        )
        for i, (lab, v) in enumerate([("a", 40), ("a", 40), ("b", 10), ("meta-llama", 5), ("meta", 5)])
    ]
    ((d, v, ids),) = run("lab_token_hhi", rows)
    assert abs(v - (0.8**2 + 0.1**2 + 0.1**2)) < 1e-9 and len(ids) == 5  # meta-llama and meta are one lab


def test_venture_incl_debt_adds_form_d_debt_to_equity_in_the_same_quarter():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE observations (id VARCHAR, series_key VARCHAR, entity_id VARCHAR, as_of_date DATE, value_numeric DOUBLE)"
    )
    con.execute("CREATE TABLE entity_membership (entity_id VARCHAR, sublayer_id VARCHAR, is_primary BOOLEAN)")
    con.execute("INSERT INTO entity_membership VALUES ('crusoe', 'hyperscalers_neoclouds', true)")
    con.execute(VENTURE_ROUNDS)
    con.executemany(
        "INSERT INTO observations VALUES (?, ?, 'crusoe', ?, ?)",
        [
            ("e1", "epoch.crusoe.round_equity_usd.pt", "2025-02-01", 100.0),
            ("d1", "formd.crusoe.debt_sold_usd.pt", "2025-02-15", 40.0),
        ],
    )
    eq = con.execute(METRICS["venture_dollars"]["sql"]).fetchall()
    both = con.execute(METRICS["venture_dollars_incl_debt"]["sql"]).fetchall()
    assert eq[0][2] == 100.0 and both[0][2] == 140.0 and sorted(both[0][3]) == ["d1", "e1"]


def run_p(metric: str, rows: list[tuple]) -> list[tuple]:
    """Like run(), with period_start: (id, series_key, subject, as_of_date, period_start, value)."""
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE obs_raw (id VARCHAR, series_key VARCHAR, subject VARCHAR, as_of_date DATE, period_start DATE, value_numeric DOUBLE)"
    )
    con.executemany("INSERT INTO obs_raw VALUES (?, ?, ?, ?, ?, ?)", rows)
    con.execute(KEY_SPLIT)
    return con.execute(METRICS[metric]["sql"]).fetchall()


def test_gross_profit_stack_by_hand_with_no_look_ahead():
    rows = [
        ("n", "sec.nvda.gross_profit.q", "nvda", "2026-04-26", "2026-01-26", 60.0),
        ("a", "sec.amd.gross_profit.q", "amd", "2026-06-27", "2026-03-29", 20.0),
        ("mr", "sec_seg.msft.intelligent_cloud.revenue.q", "msft", "2026-06-30", "2026-04-01", 50.0),
        ("mc", "sec_seg.msft.intelligent_cloud.cost_of_revenue.q", "msft", "2026-06-30", "2026-04-01", 30.0),
        ("o1", "epoch.openai.revenue_run_rate_usd.pt", "openai", "2026-05-01", None, 40.0),
        (
            "o2",
            "epoch.openai.revenue_run_rate_usd.pt",
            "openai",
            "2026-07-15",
            None,
            100.0,
        ),  # after the quarter
        ("or", "epoch.openai.revenue_usd.fy", "openai", "2025-12-31", None, 10.0),
        ("oi", "epoch.openai.inference_compute_usd.fy", "openai", "2025-12-31", None, 6.0),
        ("x1", "epoch.anthropic.revenue_run_rate_usd.pt", "anthropic", "2026-06-15", None, 20.0),
        ("xr", "epoch.anthropic.revenue_usd.fy", "anthropic", "2025-12-31", None, 10.0),
        ("xi", "epoch.anthropic.inference_compute_usd.fy", "anthropic", "2025-12-31", None, 5.0),
    ]
    out = {(r[1], r[2]): r[3] for r in run_p("gross_profit_share_by_layer", rows)}
    total = 60 + 20 + (50 - 30) + 40 / 4 * 0.4 + 20 / 4 * 0.5  # 106.5: the July run-rate never counts
    assert abs(out[("compute_semis", "filed")] - 80 / total) < 1e-9
    assert abs(out[("compute_cloud", "filed")] - 20 / total) < 1e-9
    assert abs(out[("model", "estimated")] - 6.5 / total) < 1e-9 and abs(sum(out.values()) - 1) < 1e-9


def test_gross_margin_fills_the_fiscal_q4_and_reports_the_year():
    rows = [
        ("fg", "sec.nvda.gross_profit.fy", "nvda", "2026-01-25", "2025-01-27", 400.0),
        ("fr", "sec.nvda.revenue.fy", "nvda", "2026-01-25", "2025-01-27", 500.0),
    ]
    for i, (end, start, gp, rev) in enumerate(
        [
            ("2025-04-27", "2025-01-27", 90, 100),
            ("2025-07-27", "2025-04-28", 95, 120),
            ("2025-10-26", "2025-07-28", 100, 130),
        ]
    ):
        rows += [
            (f"g{i}", "sec.nvda.gross_profit.q", "nvda", end, start, gp),
            (f"r{i}", "sec.nvda.revenue.q", "nvda", end, start, rev),
        ]
    q = {str(r[0]): (r[2], len(r[3])) for r in run_p("gross_margin", rows)}
    assert (
        abs(q["2026-01-25"][0] - 115 / 150) < 1e-9 and q["2026-01-25"][1] == 8
    )  # the fill cites the 10-K and three 10-Qs
    fy = run_p("gross_margin_fy", rows)
    assert [(str(r[0]), r[2]) for r in fy] == [("2026-01-25", 0.8)]


def test_venture_4q_sums_the_trailing_year_per_layer_and_sub_layer():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE observations (id VARCHAR, series_key VARCHAR, entity_id VARCHAR, as_of_date DATE, value_numeric DOUBLE)"
    )
    con.execute(
        "CREATE TABLE entity_membership (entity_id VARCHAR, layer_id VARCHAR, sublayer_id VARCHAR, is_primary BOOLEAN)"
    )
    con.executemany(
        "INSERT INTO entity_membership VALUES (?, 'model', ?, true)",
        [("a", "frontier_labs"), ("b", "neolabs")],
    )
    con.executemany(
        "INSERT INTO observations VALUES (?, ?, ?, ?, ?)",
        [
            (
                "a1",
                "epoch.a.round_equity_usd.pt",
                "a",
                "2025-02-01",
                10.0,
            ),  # Q1 2025: drops out of the Q2 2026 window
            ("a2", "epoch.a.round_equity_usd.pt", "a", "2025-08-01", 20.0),
            ("b1", "formd.b.amount_sold_usd.pt", "b", "2026-05-01", 5.0),
            ("b2", "formd.b.debt_sold_usd.pt", "b", "2026-05-02", 99.0),  # debt never counts here
        ],
    )
    con.execute(VENTURE_ROUNDS)
    out = {(str(r[0]), r[2]): r[3] for r in con.execute(METRICS["venture_dollars_4q"]["sql"]).fetchall()}
    assert out[("2026-06-30", "all")] == 25.0 and out[("2026-06-30", "frontier_labs")] == 20.0
    assert out[("2025-03-31", "all")] == 10.0


def test_operating_income_stack_by_hand_with_a_fiscal_q4_fill():
    q = [  # five segments in calendar Q2 2026; AMD's quarter is missing and is filled from its fiscal year
        ("n", "sec_seg.nvda.compute_networking.operating_income.q", "nvda", "2026-04-26", "2026-01-26", 30.0),
        ("w", "sec_seg.amzn.aws.operating_income.q", "amzn", "2026-06-30", "2026-04-01", 10.0),
        ("g", "sec_seg.googl.cloud.operating_income.q", "googl", "2026-06-30", "2026-04-01", 5.0),
        ("m", "sec_seg.msft.intelligent_cloud.operating_income.q", "msft", "2026-06-30", "2026-04-01", 15.0),
        ("afy", "sec_seg.amd.data_center.operating_income.fy", "amd", "2026-06-27", "2025-06-29", 40.0),
    ]
    for i, (end, start, v) in enumerate(
        [
            ("2025-09-27", "2025-06-29", 8.0),
            ("2025-12-27", "2025-09-28", 10.0),
            ("2026-03-28", "2025-12-28", 12.0),
        ]
    ):
        q.append((f"a{i}", "sec_seg.amd.data_center.operating_income.q", "amd", end, start, v))
    out = {(str(r[0]), r[1]): (r[2], r[3]) for r in run_p("margin_stack_share_by_layer", q)}
    semis, cloud = 30 + (40 - 30), 10 + 5 + 15  # AMD's filled Q4 is the year minus its three quarters
    assert abs(out[("2026-06-30", "compute_semis")][0] - semis / (semis + cloud)) < 1e-9
    assert abs(out[("2026-06-30", "compute_cloud")][0] - cloud / (semis + cloud)) < 1e-9
    assert {"afy", "a0", "a1", "a2", "n"} <= set(out[("2026-06-30", "compute_semis")][1])


def test_hhi_by_layer_by_hand():
    rows = [
        ("n", "sec_seg.nvda.data_center.revenue.q", "nvda", "2026-04-26", "2026-01-26", 60.0),
        ("a", "sec_seg.amd.data_center.revenue.q", "amd", "2026-06-27", "2026-03-29", 40.0),
        ("w", "sec_seg.amzn.aws.revenue.q", "amzn", "2026-06-30", "2026-04-01", 50.0),
        ("g", "sec_seg.googl.cloud.revenue.q", "googl", "2026-06-30", "2026-04-01", 25.0),
        ("m", "sec_seg.msft.intelligent_cloud.revenue.q", "msft", "2026-06-30", "2026-04-01", 25.0),
        ("r1", "ramp.anthropic.business_paid_share.m", "anthropic", "2026-07-31", None, 0.3),
        ("r2", "ramp.openai.business_paid_share.m", "openai", "2026-07-31", None, 0.1),
    ]
    out = {(str(r[0]), r[1]): r[2] for r in run_p("hhi_by_layer", rows)}
    assert abs(out[("2026-06-30", "compute_semis")] - (0.6**2 + 0.4**2)) < 1e-9
    assert abs(out[("2026-06-30", "compute_cloud")] - (0.5**2 + 0.25**2 + 0.25**2)) < 1e-9
    assert abs(out[("2026-07-31", "model")] - (0.75**2 + 0.25**2)) < 1e-9  # lab shares renormalised to one


def test_hardware_price_performance_pairs_flops_and_price_by_chip_and_date():
    rows = [
        ("f1", "epoch_hw.h100.fp16_flops.pt", "h100", "2023-03-21", 1e15, ""),
        ("p1", "epoch_hw.h100.release_price_usd.pt", "h100", "2023-03-21", 25000.0, ""),
        ("f2", "epoch_hw.a100.fp16_flops.pt", "a100", "2020-05-14", 3e14, ""),  # no price: not a point
    ]
    assert run("perf_per_dollar_doubling_days", rows) == [(date(2023, 3, 21), 4e10, ["f1", "p1"])]


def test_capex_to_revenue_differences_year_to_date_capex_and_needs_four_quarters_per_filer():
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE obs_raw (id VARCHAR, series_key VARCHAR, subject VARCHAR, entity_id VARCHAR, as_of_date DATE, period_start DATE, value_numeric DOUBLE)"
    )
    rows = [  # Alphabet files capex only year to date: quarters 10, 15, 20, 25
        ("g1", "sec.googl.capex.q", "googl", "googl", "2025-03-31", "2025-01-01", 10.0),
        ("g2", "sec.googl.capex.h1", "googl", "googl", "2025-06-30", "2025-01-01", 25.0),
        ("g3", "sec.googl.capex.9m", "googl", "googl", "2025-09-30", "2025-01-01", 45.0),
        ("g4", "sec.googl.capex.fy", "googl", "googl", "2025-12-31", "2025-01-01", 70.0),
        (
            "mh1",
            "sec.msft.capex.h1",
            "msft",
            "msft",
            "2025-06-30",
            "2025-01-01",
            10.0,
        ),  # a filed quarter beats it
    ]
    ends = {
        "msft": ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
        "amzn": ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
        "meta": ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31"],
        "orcl": ["2025-02-28", "2025-05-31", "2025-08-31", "2025-11-30"],
    }
    for s, es in ends.items():
        for i, e in enumerate(es):
            start = str(date.fromisoformat(e).replace(day=1) - (date(2025, 3, 1) - date(2025, 1, 1)))
            rows.append((f"{s[0]}{i + 1}", f"sec.{s}.capex.q", s, s, e, start, 5.0))
    rows += [
        ("rr", "epoch.openai.revenue_run_rate_usd.pt", "openai", "openai", "2025-12-15", None, 40.0),
        ("me", "menlo.us_enterprise.genai_spend_usd.fy", "us_enterprise", None, "2025-11-01", None, 10.0),
    ]
    con.executemany("INSERT INTO obs_raw VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute(KEY_SPLIT)
    out = {str(d): (v, ids) for d, v, ids in con.execute(METRICS["capex_to_revenue_stack"]["sql"]).fetchall()}
    assert list(out) == ["2025-12-31"]  # earlier windows lack a quarter for someone
    v, ids = out["2025-12-31"]
    assert abs(v - (70 + 4 * 20) / (40 + 10)) < 1e-9
    assert {"g1", "g2", "g3", "g4", "rr", "me"} <= set(ids) and "mh1" not in ids
    # the store's view holds a second copy of the differencing: it must give the same trailing total
    con.execute(CAPEX_TTM)
    assert con.execute("SELECT cq::DATE, v FROM hyperscaler_capex_ttm").fetchall() == [
        (date(2025, 10, 1), 150.0)
    ]

    # a year on, every filer spends half as much again: the growth metric reads the same view
    def year_on(d: str) -> str:
        return str(date.fromisoformat(d).replace(year=date.fromisoformat(d).year + 1))

    later = [
        (f"{i}y", k, s_, e_, year_on(a_), year_on(p_), x * 1.5)
        for i, k, s_, e_, a_, p_, x in rows
        if ".capex." in k
    ]
    con.executemany("INSERT INTO obs_raw VALUES (?, ?, ?, ?, ?, ?, ?)", later)
    ((d, g, gids),) = con.execute(METRICS["hyperscaler_capex_ttm_yoy"]["sql"]).fetchall()
    assert str(d) == "2026-12-31" and abs(g - 0.5) < 1e-9 and {"g4", "g4y"} <= set(gids)


def test_vendor_financing_flow_reads_every_completed_quarter_so_it_can_fall():
    rows = [
        ("d1", "circular.nvda_openai.commitment_usd.pt", "nvda_openai", "2025-02-10", 100.0, ""),
        ("d2", "circular.amd_openai.commitment_usd.pt", "amd_openai", "2025-08-20", 50.0, ""),
    ]
    out = {str(d): (v, ids) for d, v, ids in run("circular_commitments_new_4q", rows)}
    assert out["2025-03-31"] == (100.0, ["d1"]) and out["2025-06-30"] == (
        100.0,
        ["d1"],
    )  # a quiet quarter still reads
    assert out["2025-09-30"] == (150.0, ["d1", "d2"])
    assert out["2026-03-31"] == (50.0, ["d2"])  # the February deal has left the window: the flow falls
    assert (
        "2026-09-30" not in out and "2026-12-31" not in out
    )  # nothing left to cite a year after the last deal


def _chips(measure: str, by_date: dict[str, dict[str, float]]) -> list[tuple]:
    return [
        (f"{d}{n}", f"epoch_chips.{n}.{measure}.pt", n, d, v, "")
        for d, names in by_date.items()
        for n, v in names.items()
    ]


def test_designer_shares_wait_for_a_full_panel_of_at_least_three():
    rows = _chips(
        "h100e_cumulative",
        {
            "2023-12-31": {"nvidia": 90, "google": 10},  # a complete panel of two: too few to call a market
            "2024-12-31": {"nvidia": 60, "google": 30, "amd": 10},
            "2025-03-31": {
                "nvidia": 70,
                "amd": 10,
            },  # google has started reporting and is missing: not a panel
        },
    )
    out = {str(d): v for d, v, _ in run("chip_designer_hhi", rows)}
    assert list(out) == ["2024-12-31"] and abs(out["2024-12-31"] - (0.36 + 0.09 + 0.01)) < 1e-9


def test_fleet_power_growth_compares_like_panels_only():
    rows = _chips(
        "power_mw_cumulative",
        {
            "2023-12-31": {"nvidia": 100, "google": 20, "amd": 5},
            "2024-12-31": {"nvidia": 200, "google": 40, "amd": 10, "amazon": 50},  # a fourth designer joins
            "2025-12-31": {"nvidia": 400, "google": 80, "amd": 20, "amazon": 100},
        },
    )
    out = {str(d): v for d, v, _ in run("chip_fleet_power_yoy", rows)}
    assert (
        list(out) == ["2025-12-31"] and abs(out["2025-12-31"] - 1.0) < 1e-9
    )  # 2024 over 2023 would mix panels


def test_cowos_buyer_hhi_counts_other_as_one_buyer_and_ignores_the_unit():
    rows = [
        (f"s{n}", f"epoch_components.{n}.cowos_share_pct.q", n, "2025-12-31", v, "")
        for n, v in {"nvidia": 60.0, "google": 20.0, "other": 20.0}.items()
    ]
    ((_, v, ids),) = run("cowos_buyer_hhi", rows)
    assert abs(v - (0.36 + 0.04 + 0.04)) < 1e-9 and sorted(ids) == ["sgoogle", "snvidia", "sother"]


def test_the_basket_keeps_gemini_pro_and_drops_small_tiers_and_variants():
    def price(i: str, model: str, usd: float, d: str = "2026-09-10") -> tuple:
        subject = model.replace("/", "_").replace("-", "_").replace(".", "_").replace(":", "_")
        return (
            i,
            f"openrouter.{subject}.price_completion_usd_per_mtok.pt",
            subject,
            d,
            usd,
            f"{model} pricing.completion x",
        )

    rows = [
        price("g", "google/gemini-2.5-pro", 10.0),  # "gemini" contains "mini": it must stay
        price("m", "openai/gpt-5-mini", 2.0),
        price("f", "google/gemini-3-flash-lite", 0.3),
        price("v", "openai/gpt-5:batch", 0.1),
        price("o", "meta-llama/llama-3.2-1b-instruct", 0.01),  # not in the basket at all
        price("d", "deepseek/deepseek-v3.2", 0.4, "2026-09-15"),
        price("e", "deepseek/deepseek-v4-pro", 0.4, "2026-09-15"),  # a tie: the lower id is cited, every run
        price("x", "deepseek/deepseek-v3.2-exp", 0.2, "2026-09-15"),  # experimental and image builds are out
        price("i", "openai/gpt-5-image", 0.1, "2026-09-15"),
    ]
    out = {str(d): (v, ids) for d, v, ids in run("basket_min_output_price_per_mtok", rows)}
    assert out == {"2026-09-10": (10.0, ["g"]), "2026-09-15": (0.4, ["d"])}


def test_supply_growth_is_per_input_against_the_same_quarter_a_year_before():
    rows = [
        ("c0", "epoch_components.global.cowos_supply_wafers.q", "global", "2024-12-31", 100.0, ""),
        ("c1", "epoch_components.global.cowos_supply_wafers.q", "global", "2025-12-31", 170.0, ""),
        (
            "h1",
            "epoch_components.global.hbm_supply_usd.q",
            "global",
            "2025-12-31",
            9.0,
            "",
        ),  # no year-ago row
    ]
    assert run("chip_input_supply_yoy", rows) == [
        (date(2025, 12, 31), "cowos_supply_wafers", 0.7, ["c1", "c0"])
    ]


def _yr(k: int) -> str:
    return str(
        date.today() + timedelta(days=365 * k)
    )  # never date.replace(year=...): it raises on 29 February


READ = "2026-09-01T00:00:00+00:00"


def _dc_ratio(sites: list[tuple[str, float, float]], extra: list[tuple] = ()) -> dict:
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE obs_raw (id VARCHAR, series_key VARCHAR, subject VARCHAR, as_of_date DATE, value_numeric DOUBLE, retrieved_at VARCHAR, disputed BOOLEAN)"
    )
    rows = []
    for name, built, planned in sites:
        key = f"epoch_dc.{name}.power_mw.pt"
        rows += [
            (f"{name}b0", key, name, _yr(-2), 1.0, READ, False),
            (f"{name}b", key, name, _yr(-1), built, READ, False),
            (f"{name}p", key, name, _yr(1), planned, "2026-09-02T00:00:00+00:00", False),
            (f"{name}p2", key, name, _yr(2), planned / 2, READ, False),
        ]
    con.executemany("INSERT INTO obs_raw VALUES (?, ?, ?, ?, ?, ?, ?)", rows + list(extra))
    con.execute(KEY_SPLIT)
    con.execute(DC_SITES)
    sql = METRICS["dc_projected_to_observed_power"]["sql"]
    ratio = {s_: (d, v, ids) for d, s_, v, ids in con.execute(sql).fetchall()}
    count = {s_: v for _, s_, v, _ in con.execute(METRICS["dc_sites_compared"]["sql"]).fetchall()}
    return {"ratio": ratio, "count": count}


def test_the_data_centre_gap_sums_peak_plans_over_newest_builds_and_shows_the_bare_sites():
    sites = [(f"s{i}", 100.0, 300.0) for i in range(20)] + [(f"z{i}", 0.0, 500.0) for i in range(5)]
    soon = str(date.today() + timedelta(days=30))
    extra = [
        ("onlybuilt", "epoch_dc.ob.power_mw.pt", "ob", _yr(-1), 999.0, READ, False),  # no plan: not compared
        ("gone", "epoch_dc.s0.power_mw.pt", "s0", _yr(3), 9999.0, READ, True),  # a plan Epoch withdrew
        (
            "s1p_early",
            "epoch_dc.s1.power_mw.pt",
            "s1",
            soon,
            300.0,
            READ,
            False,
        ),  # the same peak, reached sooner
    ]
    out = _dc_ratio(sites, extra)
    d, v, ids = out["ratio"]["all"]
    assert abs(v - (20 * 300 + 5 * 500) / (20 * 100)) < 1e-9
    assert abs(out["ratio"]["built"][1] - 3.0) < 1e-9 and out["count"] == {"all": 25, "unbuilt": 5}
    assert (
        str(d) == "2026-09-02" and "s0b" in ids and "s0p" in ids and "s0b0" not in ids and "gone" not in ids
    )
    assert (
        "s1p_early" in ids and "s1p" not in ids
    )  # a tie on planned power cites the earlier milestone, every run


def test_too_few_sites_give_no_ratio():
    out = _dc_ratio([(f"s{i}", 100.0, 300.0) for i in range(19)])
    assert out["ratio"] == {} and out["count"] == {"all": 19}


def test_the_arc_frontier_emits_one_record_per_new_high_citing_the_row_that_set_it():
    rows = [
        ("r2", "epoch_bench.b_r2.arc_agi_2.pt", "b_r2", "2026-01-01", 0.5, ""),
        ("r1", "epoch_bench.a_r1.arc_agi_2.pt", "a_r1", "2026-01-01", 0.5, ""),  # a tie on one date
        ("r3", "epoch_bench.c_r3.arc_agi_2.pt", "c_r3", "2026-02-01", 0.4, ""),  # below the record: no row
        ("r4", "epoch_bench.d_r4.arc_agi_2.pt", "d_r4", "2026-03-01", 0.7, ""),
    ]
    out = [(str(d), v, ids) for d, v, ids in run("arc_agi_frontier", rows)]
    assert out == [("2026-01-01", 0.5, ["r1"]), ("2026-03-01", 0.7, ["r4"])]
