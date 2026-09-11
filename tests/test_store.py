import json
import os
from pathlib import Path

import pytest

from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _chdir():
    cwd = os.getcwd()
    os.chdir(REPO)
    yield
    os.chdir(cwd)


def _numbers(doc, path=""):
    """Every dict with a numeric `value` must sit beside a non-empty obs_ids list."""
    if isinstance(doc, dict):
        if isinstance(doc.get("value"), (int, float)):
            assert doc.get("obs_ids"), f"{path}: number without obs_ids"
        for k, v in doc.items():
            _numbers(v, f"{path}/{k}")
    elif isinstance(doc, list):
        for i, v in enumerate(doc):
            _numbers(v, f"{path}[{i}]")


@pytest.mark.skipif(not (REPO / "data/observations/metr.jsonl").exists(), reason="no ingested data")
def test_export_is_deterministic_and_every_number_has_provenance(tmp_path):
    s = st.Store()
    a, b = tmp_path / "a", tmp_path / "b"
    s.export(a)
    st.Store().export(b)
    for f in sorted(a.rglob("*.json")):
        if f.name == "meta.json":
            continue
        assert f.read_bytes() == (b / f.relative_to(a)).read_bytes(), f.name
        if "_repo" not in f.parts:  # the JSON schemas are not data
            _numbers(json.loads(f.read_text()), f.name)
    for name in ("sources.md", "bands.md", "changelog.md"):  # the generated spec documents are stable too
        assert (a / "_repo/docs" / name).read_bytes() == (b / "_repo/docs" / name).read_bytes(), name
    assert (a / "_repo/schema/Observation.schema.json").exists()


@pytest.mark.skipif(not (REPO / "data/observations/metr.jsonl").exists(), reason="no ingested data")
def test_metrics_refuse_missing_inputs(tmp_path):
    spec = tmp_path / "m.yaml"
    spec.write_text(
        "version: 1\nmetrics:\n  ghost:\n    inputs: ['nope.*.x.pt']\n    formula_version: 1\n    sql: 'SELECT 1'\n"
    )
    assert run_metrics(st.Store().con, spec) == []


def test_capture_readings_meta_counts_and_chart_sources(tmp_path):
    import json

    s = st.Store()
    s.derived = run_metrics(s.con)
    s.export(tmp_path / "data")
    cap = json.loads((tmp_path / "data" / "lens" / "capture.json").read_text())
    assert all(
        layer["reading"].endswith(".") and not any(c in layer["reading"] for c in "$%")
        for layer in cap["layers"]
    )
    meta = json.loads((tmp_path / "data" / "meta.json").read_text())
    assert meta["observations"] == s.con.execute("SELECT count(*) FROM observations").fetchone()[0]
    # P1 §9: every chart document with points names its sources
    d = tmp_path / "data"
    for f in (d / "indicators").glob("*.json"):
        doc = json.loads(f.read_text())
        assert not doc.get("points") or doc["chart_sources"]["sources"], f.name
    for f in (d / "venture").glob("*.json"):
        doc = json.loads(f.read_text())
        assert not any(q.get("by_source") for q in doc["quarters"]) or doc["chart_sources"]["sources"], f.name
    for series, sources in (
        ("gross_profit_stack_series", "gross_profit_stack_sources"),
        ("margin_stack_series", "margin_stack_sources"),
    ):
        assert not cap[series] or cap[sources]["sources"], series
    lad = json.loads((d / "lens" / "ladder.json").read_text())
    assert not any(r["production"] or r["research"] for r in lad["rungs"]) or lad["chart_sources"]["sources"]
