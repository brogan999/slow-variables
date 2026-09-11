from datetime import date

from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.memo import digest, facts
from ai_tracker.query.ask import Tools
from ai_tracker.query.citecheck import CITE, check


def test_digest_is_deterministic_and_passes_the_citation_check():
    s = st.Store()
    s.derived = run_metrics(s.con)
    s.semantic_tables()
    f = facts(s, date(2026, 9, 1), date(2026, 9, 10))
    assert f["events"] and f["new_observations"] > 0
    body = digest(f)
    assert body == digest(f)
    res = check(body, Tools(s).records(CITE.findall(body)))
    assert res.ok, res.failures[:5]


def test_ops_notes_list_a_waiting_crossing(monkeypatch, tmp_path):
    import json

    from ai_tracker.memo import ops_notes

    s = st.Store()
    monkeypatch.setattr(st, "DATA", tmp_path)
    (tmp_path / "proposed_status_events.jsonl").write_text(
        json.dumps(
            {
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


def test_a_model_error_falls_back_to_the_digest(monkeypatch):
    import anthropic
    import httpx

    from ai_tracker import memo

    class Down:
        def __init__(self, *a, **k):
            self.messages = self

        def create(self, **k):
            raise anthropic.APIConnectionError(request=httpx.Request("POST", "https://api.anthropic.com"))

    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setattr(anthropic, "Anthropic", Down)
    assert memo.prose({"since": "2026-09-01"}, None) == (None, "model error (APIConnectionError)")


def test_refresh_list_names_hand_entered_series_but_not_connector_fed_or_one_off_ones():
    from datetime import date

    from ai_tracker import store as st
    from ai_tracker.memo import due_for_refresh

    s = st.Store()
    due = "\n".join(due_for_refresh(s, date(2030, 1, 1)))
    assert "edd.ca_high_exposure.claims_3mma_mom.m" in due  # hand-entered, monthly, behind a published indicator
    assert "ramp.us_businesses.paid_ai_adoption_share.m" not in due  # the connector now writes its newest row
    assert "metr_blog.rct_2025" not in due  # a one-off study is never due
