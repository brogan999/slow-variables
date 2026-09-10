from ai_tracker.ingest.connectors.sec_xbrl import SecXbrl
from ai_tracker.schema import Basis, Entity, Membership


def test_sec_extract(raw):
    nvda = Entity(
        id="nvda", name="NVIDIA", cik="0001045810", memberships=[Membership(layer_id="compute_physical")]
    )
    rows = SecXbrl([nvda]).extract([raw("sec_nvda_companyfacts.json")])
    by = {(r.series_key, r.as_of_date.isoformat()): r for r in rows}
    fy = by[("sec.nvda.gross_profit.fy", "2026-01-25")], by[("sec.nvda.revenue.fy", "2026-01-25")]
    assert abs(fy[0].value_numeric / fy[1].value_numeric - 0.711) < 0.005  # FY26 GAAP gross margin 71.1%
    assert fy[0].audited_vs_reported == Basis.audited and fy[0].tier == 4 and fy[0].grade == "A"
    q = by[("sec.nvda.revenue.q", "2026-07-26")]
    assert (
        q.audited_vs_reported == Basis.company_stated and q.period_start is not None and q.entity_id == "nvda"
    )
    assert ("sec.nvda.rpo.q", "2026-07-26") in by  # instants keep the q grain
    # year-to-date rows (no frame) never leak in: no 6-month duration for a .q series
    assert all(
        (r.as_of_date - r.period_start).days < 100
        for r in rows
        if r.series_key.endswith(".q") and r.period_start
    )
