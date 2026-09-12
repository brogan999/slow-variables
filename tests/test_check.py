import json
from datetime import datetime, timedelta, timezone

from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.cli import attention, check_errors
from ai_tracker.schema import StatusEvent


def test_check_rules_fire(monkeypatch, tmp_path):
    s = st.Store()
    s.derived = run_metrics(s.con)  # derived rows are not committed; a fresh checkout computes them
    assert check_errors(s) == []  # the committed data passes today
    # 1. a status event citing an observation that does not exist
    s.events.append(
        StatusEvent(
            target_id="metr_horizon_50",
            new_status="faster_than_normal",
            new_conf=50,
            reason="x",
            evidence_ids=["deadbeefdeadbeef"],
            author="test",
            created_at=datetime.now(timezone.utc),
        )
    )
    errs = check_errors(s)
    assert any("cites unknown observations" in e for e in errs)
    s.events.pop()
    # 2. a proposal left without a reason for more than 14 days
    monkeypatch.setattr(st, "DATA", tmp_path)
    old = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    (tmp_path / "proposed_status_events.jsonl").write_text(
        json.dumps({"id": "p1", "target_id": "btos_firm_use", "reason": "", "created_at": old}) + "\n"
    )
    assert any(
        "waited 20 days" in e for e in attention(s)
    )  # attention, not an error: it must not freeze the nightly
    assert not any("waited 20 days" in e for e in check_errors(s))
    (tmp_path / "proposed_status_events.jsonl").write_text("")
    # 3. a published indicator past twice its cadence, unless stale_ok carries a reason
    ind = next(
        i for i in s.seed.indicators if i.id == "enterprise_pilot_to_production"
    )  # latest point mid-2025
    ind.cadence_expected = "daily"
    assert any(e.startswith("enterprise_pilot_to_production: stale since") for e in attention(s))
    assert check_errors(s) == []  # one stale source never blocks the rest
    ind.stale_ok, ind.stale_reason = True, "test"
    assert not any(e.startswith("enterprise_pilot_to_production: stale") for e in attention(s))


def test_a_blank_proposal_the_evaluator_no_longer_holds_is_dropped():
    from ai_tracker.cli import _drop_stale

    rows = [
        {"target_id": "a", "new_status": "faster_than_normal", "reason": ""},  # flipped back tonight
        {"target_id": "b", "new_status": "stable", "reason": ""},  # still held
        {"target_id": "c", "new_status": "stable", "reason": "a human wrote this"},  # reasoned rows stay
        {"target_id": "p1", "new_status": "behind", "reason": ""},  # not evaluated tonight (a prediction)
    ]
    kept = _drop_stale(rows, {"a": "consistent_with_normal", "b": "stable", "c": "unclear"})
    assert [r["target_id"] for r in kept] == ["b", "c", "p1"]


def test_a_published_indicator_needs_a_timing_rationale_that_opens_with_its_tag():
    s = st.Store()
    s.derived = run_metrics(s.con)
    ind = next(i for i in s.seed.indicators if i.id == "metr_horizon_50")
    ind.timing_rationale = "Lagging: wrong tag."
    assert any(e.startswith("metr_horizon_50: published without a timing_rationale") for e in check_errors(s))


def test_a_shared_indicator_needs_a_crosswalk_row_for_its_two_addresses():
    from ai_tracker import store as st
    from ai_tracker.cli import check_errors

    s = st.Store()
    s.seed.crosswalk = [c for c in s.seed.crosswalk if (c.bucket_id, c.layer_id) != ("return_arrow", "model")]
    errs = check_errors(s)
    assert any("lab_recoupment_ratio" in e and "no crosswalk row" in e for e in errs)
    s = st.Store()  # a row for the same bucket and layer but another sub-layer does not join it either
    s.seed.crosswalk = [c for c in s.seed.crosswalk if c.sublayer_id or (c.bucket_id, c.layer_id) != ("adaptation", "deployment_application")]
    assert any(e.startswith("waymo_weekly_paid_rides: addressed to adaptation and deployment_application/consumer_ai") for e in check_errors(s))


def test_diffusion_buckets_read_flow_statuses_only():
    from ai_tracker import store as st

    s = st.Store()
    cards = {i.id: s._card(i) for i in s.seed.indicators}
    mine = [i for i in s.seed.indicators if i.bucket_id == "methods"]
    assert any(i.direction_rule for i in mine) and any(not i.direction_rule for i in mine)
    for i in mine:  # capture readings would carry the vote if they were counted
        cards[i.id]["status"] = "concentrating" if i.direction_rule else "emerging"
    lens = s._diffusion_lens(cards, [], "2026-09-11")
    methods = next(b for b in lens["buckets"] if b["id"] == "methods")
    assert any(c["id"] == "lab_run_rates" for c in methods["indicators"])  # listed on the bucket
    assert methods["status"] == "emerging"  # but never summarised there
    assert all(v["status"] != "concentrating" for v in lens["valves"])


def test_a_written_status_reason_is_held_until_it_says_what_counterevidence_was_weighed(tmp_path, monkeypatch, capsys):
    import json
    from types import SimpleNamespace as NS

    from ai_tracker import cli
    from ai_tracker import store as st

    monkeypatch.setattr(st, "DATA", tmp_path)
    monkeypatch.setattr(st, "OBS", tmp_path / "obs")
    row = {"id": "e1", "target_type": "indicator", "target_id": "hand_written", "new_status": "faster_than_normal",
           "reason": "It crossed the band because the survey changed.", "evidence_ids": ["a"], "author": "claude",
           "created_at": "2026-09-12T00:00:00+00:00"}
    auto = {**row, "id": "e2", "target_id": "machine", "reason": "Evaluator: 3.0 (BLS, 2026-01-01) reads normal. Auto-reason; band rationale: x"}
    st.write_jsonl(tmp_path / "proposed_status_events.jsonl", [row, auto])
    assert cli.cmd_approve(NS(reviewer="claude")) == 0
    committed = [json.loads(x) for x in (tmp_path / "status_events.jsonl").read_text().splitlines()]
    assert [c["target_id"] for c in committed] == ["machine"]  # the machine reason lands, the written one waits
    assert "hand_written" in capsys.readouterr().out
    st.write_jsonl(tmp_path / "proposed_status_events.jsonl", [{**row, "counterevidence_considered": "The older wave read lower; it is a different instrument."}])
    assert cli.cmd_approve(NS(reviewer="claude")) == 0
    assert len((tmp_path / "status_events.jsonl").read_text().splitlines()) == 2
