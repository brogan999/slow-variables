import hashlib
import json
import re
import shutil

import duckdb

from ai_tracker import census
from ai_tracker.query import ask
from ai_tracker.query.citecheck import check

from .test_atlas import NUMBER_WORD, YEAR


def _copy(tmp_path, monkeypatch):
    spec = census.load()
    shutil.copytree(census.bundle(spec), tmp_path / spec["version"])
    monkeypatch.setattr(census, "DATA", tmp_path)
    return spec, tmp_path / spec["version"]


def test_the_bundle_matches_its_manifest_and_every_table_sums_to_the_headline():
    assert census.problems(census.load(), census.fetches()) == []


def test_a_changed_file_or_a_table_off_the_headline_is_an_error(tmp_path, monkeypatch):
    spec, d = _copy(tmp_path, monkeypatch)
    text = (d / "functions.csv").read_text()
    freed = census.rows(d / "functions.csv")[0]["freed"]
    (d / "functions.csv").write_text(text.replace(freed, "1" + freed, 1))
    assert any("functions.csv does not match" in e for e in census.problems(spec, census.fetches()))
    m = json.loads((d / "manifest.json").read_text())
    m["files"]["functions.csv"]["sha256"] = hashlib.sha256((d / "functions.csv").read_bytes()).hexdigest()
    (d / "manifest.json").write_text(json.dumps(m))
    assert any("functions.csv sums to" in e for e in census.problems(spec, census.fetches()))


def test_a_source_link_without_a_fetch_record_is_an_error():
    assert any("no fetch record" in e for e in census.problems(census.load(), {"fetches": []}))


def _walk(x, path=""):
    if isinstance(x, dict):
        yield path, x
        for k, v in x.items():
            yield from _walk(v, f"{path}/{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from _walk(v, f"{path}/{i}")


def test_every_can_go_figure_travels_with_the_three_way_figure_and_nothing_modelled_leaves_the_method():
    index, roles = census.build(census.load(), census.fetches())
    for doc in [index, *roles.values()]:
        for path, d in _walk(doc):
            if "freed" in d:
                assert "agreed3" in d, path
            assert not any(k.endswith("_modelled") for k in d), path
    assert "sigma" in index["method"]


def test_no_three_way_figure_only_where_nothing_was_scored_by_all_three():
    index, _ = census.build(census.load(), census.fetches())
    for r in [*index["roles"], *index["functions"]]:
        assert (r["agreed3"] is None) == (r["payroll_scored_by_three"] == 0)
    assert any(r["agreed3"] == 0 for r in index["roles"])  # scored by all three, none unanimous: a real zero


def test_tables_keep_codes_as_text_and_answer_after_file_access_is_locked():
    con = duckdb.connect()
    census.create_tables(con, census.load())
    con.execute("SET enable_external_access = false")
    assert con.execute("SELECT count(*) FROM census_tasks").fetchone()[0] == 10752
    assert con.execute("SELECT typeof(naics) FROM census_industries LIMIT 1").fetchone()[0] == "VARCHAR"
    assert con.execute("SELECT count(*) FROM census_roles WHERE occ = '13-2011'").fetchone()[0] == 1


def test_a_census_figure_is_citable_and_a_modelled_one_is_not():
    t = ask.Tools.__new__(ask.Tools)
    t.pub = duckdb.connect()
    census.create_tables(t.pub, census.load())
    occ, freed, modelled = t.pub.execute(
        "SELECT occ, freed_agreed3, cost_share_stays_after_modelled FROM census_roles WHERE occ = '13-2011'"
    ).fetchone()
    rec = t._census_record(f"role.{occ}")
    assert freed in rec.values and modelled not in rec.values
    ok = check(f"Accountants have ${freed / 1e9:.1f}bn agreed by all three [census:role.{occ}].", {rec.id: rec})
    assert ok.ok, ok.failures
    assert t._census_record("function.it_software") is not None


def test_the_site_types_no_figure_on_the_census_pages():
    for s in census.strings(census.load()):
        assert all(YEAR.fullmatch(w) for w in s.split() if re.search(r"\d", w)), s
        assert not NUMBER_WORD.search(s), s


def test_the_census_pages_are_in_the_nav_and_the_sitemap():
    from pathlib import Path

    web = Path(__file__).resolve().parents[1] / "web" / "src"
    assert '"/census"' in (web / "lib" / "nav.ts").read_text()
    assert "census().roles" in (web / "app" / "sitemap.ts").read_text()
    assert (web / "app" / "census" / "roles" / "[occ]" / "page.tsx").exists()
