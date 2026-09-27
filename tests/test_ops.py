import json
from datetime import date

from ai_tracker import store as st


def test_ops_notes_list_a_waiting_crossing(monkeypatch, tmp_path):
    from ai_tracker.ops import ops_notes

    s = st.Store()
    monkeypatch.setattr(st, "DATA", tmp_path)
    (tmp_path / "proposed_status_events.jsonl").write_text(
        json.dumps(
            {
                "id": "p1",
                "target_id": "btos_firm_use",
                "old_status": None,
                "new_status": "faster_than_normal",
                "reason": "",
                "created_at": "2026-09-01T00:00:00+00:00",
                "target_type": "indicator",
            }
        )
        + "\n"
    )
    notes = ops_notes(s, date(2026, 9, 11))
    assert "`btos_firm_use`: unscored → faster than normal, waiting 10 days" in notes
    assert notes.startswith("## Operator notes") and "Newest fetch on main:" in notes


def test_refresh_list_names_hand_entered_series_but_not_connector_fed_or_one_off_ones():
    from ai_tracker.ops import due_for_refresh

    s = st.Store()
    due = "\n".join(due_for_refresh(s, date(2030, 1, 1)))
    assert "edd.ca_high_exposure.claims_3mma_mom.m" in due  # hand-entered, monthly, behind a published indicator
    assert "ramp.us_businesses.paid_ai_adoption_share.m" not in due  # the connector now writes its newest row
    assert "metr_blog.rct_2025" not in due  # a one-off study is never due
    assert "menlo.enterprise.multi_model_share.pt" not in due  # its source no longer states the figure (NOT_DUE)
