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
        _numbers(json.loads(f.read_text()), f.name)


@pytest.mark.skipif(not (REPO / "data/observations/metr.jsonl").exists(), reason="no ingested data")
def test_metrics_refuse_missing_inputs(tmp_path):
    spec = tmp_path / "m.yaml"
    spec.write_text(
        "version: 1\nmetrics:\n  ghost:\n    inputs: ['nope.*.x.pt']\n    formula_version: 1\n    sql: 'SELECT 1'\n"
    )
    assert run_metrics(st.Store().con, spec) == []


def test_capture_layers_carry_a_number_free_reading_and_meta_carries_the_counts(tmp_path):
    import json

    s = st.Store()
    s.derived = run_metrics(s.con)
    s.export(tmp_path / "data")
    cap = json.loads((tmp_path / "data" / "lens" / "capture.json").read_text())
    assert all(layer["reading"].endswith(".") and not any(c in layer["reading"] for c in "$%") for layer in cap["layers"])
    meta = json.loads((tmp_path / "data" / "meta.json").read_text())
    assert meta["observations"] == s.con.execute("SELECT count(*) FROM observations").fetchone()[0]
