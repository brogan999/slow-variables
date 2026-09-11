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
