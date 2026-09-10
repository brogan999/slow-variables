from datetime import date

from ai_tracker.ingest.connectors.census_btos import EXCEL_EPOCH, CensusBtos


def xl(d: date) -> str:
    return str((d - EXCEL_EPOCH).days)


SHEETS = {
    "Collection and Reference Dates": (
        ["Smpdt", "Ref Start", "Ref End"],
        [
            ("202617", xl(date(2026, 7, 27)), xl(date(2026, 8, 9))),
            ("202510", xl(date(2025, 4, 28)), xl(date(2025, 5, 11))),
        ],
    ),
    "Response Estimates": (
        ["Question ID", "Question", "Answer ID", "Answer", "202510", "202617"],
        [
            (
                "7",
                "In the last two weeks, did this business use Artificial Intelligence in any of its business functions?",
                "1",
                "Yes",
                "19.8%",
                "22.4%",
            ),
            (
                "7",
                "In the last two weeks, did this business use Artificial Intelligence in producing goods or services?",
                "1",
                "Yes",
                "9.1%",
                "",
            ),
            (
                "8",
                "During the next six months, do you think this business will be using Artificial Intelligence in any of its business functions?",
                "1",
                "Yes",
                "",
                "24.0%",
            ),
            (
                "7",
                "In the last two weeks, did this business use Artificial Intelligence in any of its business functions?",
                "2",
                "No",
                "80.2%",
                "77.6%",
            ),
        ],
    ),
    "Response Standard Errors": (
        ["Question ID", "Question", "Answer ID", "Answer", "202510", "202617"],
        [("7", "x", "1", "Yes", "0.5%", "0.4%")],
    ),
}


def test_two_instruments_and_next_six_months(raw):
    rows = CensusBtos()._from_sheets(raw("bls_response.json"), lambda n: SHEETS[n])
    by = {(r.series_key, r.as_of_date): r for r in rows}
    v2 = by[("census_btos.us.ai_use_share_v2.2w", date(2026, 8, 9))]
    assert abs(v2.value_numeric - 0.224) < 1e-9 and v2.period_start == date(2026, 7, 27) and v2.tier == 4
    assert round(v2.value_high - v2.value_numeric, 4) == round(1.96 * 0.004, 4)
    assert ("census_btos.us.ai_use_share_v1.2w", date(2025, 5, 11)) in by
    assert by[("census_btos.us.ai_use_next6m_share_v2.2w", date(2026, 8, 9))].value_numeric == 0.24
    assert len(rows) == 4  # "No" answers and blank cells are skipped
