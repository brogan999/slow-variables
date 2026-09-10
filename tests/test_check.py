import json
from datetime import datetime, timedelta, timezone

from ai_tracker import store as st
from ai_tracker.cli import check_errors
from ai_tracker.schema import StatusEvent


def test_check_rules_fire(monkeypatch, tmp_path):
    s = st.Store()
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
    assert any("waited 20 days" in e for e in check_errors(s))
    (tmp_path / "proposed_status_events.jsonl").write_text("")
    # 3. a published indicator past twice its cadence, unless stale_ok carries a reason
    ind = next(
        i for i in s.seed.indicators if i.id == "enterprise_pilot_to_production"
    )  # latest point mid-2025
    ind.cadence_expected = "daily"
    assert any(e.startswith("enterprise_pilot_to_production: stale since") for e in check_errors(s))
    ind.stale_ok, ind.stale_reason = True, "test"
    assert not any(e.startswith("enterprise_pilot_to_production: stale") for e in check_errors(s))
