from ai_tracker.ingest.connectors.sec_xbrl import SecXbrl
from ai_tracker.schema import Basis, Entity, Membership


def test_sec_extract(raw):
    nvda = Entity(
        id="nvda", name="NVIDIA", cik="0001045810", memberships=[Membership(layer_id="compute_physical")]
    )
    url = "https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json"
    rows = SecXbrl([nvda]).extract([raw("sec_nvda_companyfacts.json", url)])
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


def test_a_skipped_filer_does_not_shift_the_next_filers_rows(raw):
    """A private filer's 404 is skipped in fetch; the next download must still land on its own company."""
    private = Entity(id="xai", name="xAI", cik="0002079267", memberships=[Membership(layer_id="model")])
    nvda = Entity(
        id="nvda", name="NVIDIA", cik="0001045810", memberships=[Membership(layer_id="compute_physical")]
    )
    c = SecXbrl([private, nvda])
    rows = c.extract([raw("sec_nvda_companyfacts.json", c.urls[1])])  # only NVIDIA's download came back
    assert rows and all(r.entity_id == "nvda" and r.series_key.startswith("sec.nvda.") for r in rows)


def test_year_to_date_capex_is_kept_as_h1_and_9m_and_other_measures_are_not():
    import json
    from datetime import datetime, timezone

    from ai_tracker.ingest.base import RawItem

    def fact(start, end, val, filed, frame=None, form="10-Q"):
        return {
            "start": start,
            "end": end,
            "val": val,
            "filed": filed,
            "form": form,
            **({"frame": frame} if frame else {}),
        }

    capex = [
        fact("2026-01-01", "2026-03-31", 35, "2026-04-30", "CY2026Q1"),
        fact("2026-01-01", "2026-06-30", 70, "2026-07-01"),
        fact("2026-01-01", "2026-06-30", 80, "2026-07-23"),  # a later filing of the same period wins
        fact("2025-01-01", "2025-09-30", 63, "2025-10-30"),
    ]
    revenue = [fact("2026-01-01", "2026-06-30", 190, "2026-07-23")]  # year to date, no frame: skipped
    doc = {
        "facts": {
            "us-gaap": {
                "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": capex}},
                "Revenues": {"units": {"USD": revenue}},
            }
        }
    }
    googl = Entity(
        id="googl", name="Alphabet", cik="0001652044", memberships=[Membership(layer_id="compute_physical")]
    )
    c = SecXbrl([googl])
    body = json.dumps(doc).encode()
    item = RawItem(c.urls[0], body, 200, datetime(2026, 9, 13, tzinfo=timezone.utc), "x", None)
    by = {r.series_key: r for r in c.extract([item])}
    assert by["sec.googl.capex.h1"].value_numeric == 80 and by["sec.googl.capex.9m"].value_numeric == 63
    assert by["sec.googl.capex.q"].value_numeric == 35 and not any(
        k.startswith("sec.googl.revenue") for k in by
    )
