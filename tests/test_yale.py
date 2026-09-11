from datetime import datetime, timezone

import pytest

from ai_tracker.ingest.base import LayoutChanged, RawItem
from ai_tracker.ingest.connectors.yale import YaleDissimilarity

HEADER = ("Months from baseline", "Baseline Nov 2022 (AI)", "Baseline Jan 2021")


def run(rows, retrieved=datetime(2026, 4, 15, tzinfo=timezone.utc)):
    c = YaleDissimilarity.__new__(YaleDissimilarity)
    c.scrubbed, c.errors = [], []
    item = RawItem("https://budgetlab.yale.edu/x.xlsx", b"", 200, retrieved, "h" * 64)
    return c, c._from_rows(item, rows)


def test_months_map_to_dates_and_blank_cells_are_skipped():
    c, obs = run([("title",), HEADER, ("40", "7.1", "6.2"), ("41", "", "6.4")])
    keys = {(o.series_key.split(".")[2], str(o.as_of_date)): o.value_numeric for o in obs}
    assert keys == {
        ("occupation_dissimilarity_pp", "2026-03-01"): 7.1,  # month 40 from Nov 2022
        ("occupation_dissimilarity_pp_jan2021", "2024-05-01"): 6.2,  # month 40 from Jan 2021
        ("occupation_dissimilarity_pp_jan2021", "2024-06-01"): 6.4,
    }
    assert c.errors == []


def test_a_missing_header_is_a_layout_change_and_an_old_workbook_is_a_note():
    with pytest.raises(LayoutChanged):
        run([("title",), ("Months", "Baseline Nov 2022 (AI)")])
    c, obs = run([HEADER, ("40", "7.1", "6.2")], retrieved=datetime(2026, 9, 11, tzinfo=timezone.utc))
    assert obs and c.errors == ["newest month 2026-03-01; move the workbook URL in seed/sources.yaml"]
