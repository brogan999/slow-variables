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


def test_layer_venture_reads_the_latest_covered_quarter_not_the_last_non_empty_one():
    from datetime import date, datetime, timezone

    from ai_tracker.schema import Derived

    def d(day, layer, value):
        return Derived(metric="venture_dollars_4q", value=value, as_of_date=day, input_observation_ids=[f"{layer}{day}"],
                       formula_version="1", computed_at=datetime.now(timezone.utc), dims={"layer_id": layer, "sublayer_id": "all"})

    s = st.Store()
    s.derived = [d(date(2025, 3, 31), "old", 5e8), d(date(2025, 6, 30), "old", 5e8), d(date(2025, 6, 30), "new", 1e8),
                 d(date(2026, 6, 30), "new", 3e8)]
    old = s._layer_venture("old")  # rounds stopped: the four quarters to 30 Jun 2026 hold none
    assert old["value"] is None and old["as_of"] == "2026-06-30" and old["arrow"] == "down" and old["obs_ids"] == []
    s.derived = [d(date(2025, 3, 31), "old", 5e8), d(date(2026, 6, 30), "new", 3e8)]
    assert s._layer_venture("new")["arrow"] == "up"  # the year-earlier window was covered and empty


def test_one_instrument_casts_one_vote_and_the_tally_names_a_lone_reading():
    from ai_tracker.store import _summarise, _tally

    def card(i, status, cluster=None, conf=50):
        return {"id": i, "name": i.upper(), "status": status, "source_cluster": cluster, "confidence": conf, "published": True}

    survey = [card("a", "faster_than_normal", "one_survey", 60), card("b", "faster_than_normal", "one_survey", 40),
              card("c", "faster_than_normal", "one_survey", 30)]
    other = [card("d", "consistent_with_normal")]
    assert _summarise(survey + other) == "mixed"  # three readings of one survey do not outvote another instrument
    assert _tally(survey + other) == {"scored": 2, "published": 4, "margin": 0, "only": None}
    assert _summarise(survey) == "faster_than_normal" and _tally(survey)["only"] == "A"  # the most confident speaks
    assert _summarise([card("e", "unclear"), card("f", "dispersing")]) == "dispersing"  # unclear is not a reading
    assert _tally([card("e", "unclear"), card("f", "dispersing")])["scored"] == 1
