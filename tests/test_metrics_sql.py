import duckdb
import yaml

METRICS = yaml.safe_load(open("semantic/metrics.yaml"))["metrics"]


def run(metric: str, rows: list[tuple]) -> list[tuple]:
    con = duckdb.connect()
    con.execute(
        "CREATE TABLE observations (id VARCHAR, series_key VARCHAR, subject VARCHAR, as_of_date DATE, value_numeric DOUBLE, raw_snippet VARCHAR, disputed BOOLEAN)"
    )
    con.executemany("INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?, false)", rows)
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
        "CREATE TABLE observations (id VARCHAR, series_key VARCHAR, subject VARCHAR, as_of_date DATE, period_start DATE, value_numeric DOUBLE)"
    )
    con.executemany("INSERT INTO observations VALUES (?, ?, ?, ?, ?, ?)", rows)
    return con.execute(METRICS[metric]["sql"]).fetchall()


def test_gross_profit_stack_by_hand_with_no_look_ahead():
    rows = [
        ("n", "sec.nvda.gross_profit.q", "nvda", "2026-04-26", "2026-01-26", 60.0),
        ("a", "sec.amd.gross_profit.q", "amd", "2026-06-27", "2026-03-29", 20.0),
        ("mr", "sec_seg.msft.intelligent_cloud.revenue.q", "msft", "2026-06-30", "2026-04-01", 50.0),
        ("mc", "sec_seg.msft.intelligent_cloud.cost_of_revenue.q", "msft", "2026-06-30", "2026-04-01", 30.0),
        ("o1", "epoch.openai.revenue_run_rate_usd.pt", "openai", "2026-05-01", None, 40.0),
        ("o2", "epoch.openai.revenue_run_rate_usd.pt", "openai", "2026-07-15", None, 100.0),  # after the quarter
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
    rows = [("fg", "sec.nvda.gross_profit.fy", "nvda", "2026-01-25", "2025-01-27", 400.0),
            ("fr", "sec.nvda.revenue.fy", "nvda", "2026-01-25", "2025-01-27", 500.0)]
    for i, (end, start, gp, rev) in enumerate([("2025-04-27", "2025-01-27", 90, 100), ("2025-07-27", "2025-04-28", 95, 120), ("2025-10-26", "2025-07-28", 100, 130)]):
        rows += [(f"g{i}", "sec.nvda.gross_profit.q", "nvda", end, start, gp), (f"r{i}", "sec.nvda.revenue.q", "nvda", end, start, rev)]
    q = {str(r[0]): (r[2], len(r[3])) for r in run_p("gross_margin", rows)}
    assert abs(q["2026-01-25"][0] - 115 / 150) < 1e-9 and q["2026-01-25"][1] == 8  # the fill cites the 10-K and three 10-Qs
    fy = run_p("gross_margin_fy", rows)
    assert [(str(r[0]), r[2]) for r in fy] == [("2026-01-25", 0.8)]
