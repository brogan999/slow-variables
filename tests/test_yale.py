from datetime import datetime, timezone

import pytest

from ai_tracker.ingest.base import LayoutChanged, RawItem
from ai_tracker.ingest.connectors.yale import GRADUATES, WORKFORCE, YaleDissimilarity

WF = """time,series,variant,value
40,Baseline Nov 2022 (AI),indexed,7.1
41,Baseline Nov 2022 (AI),indexed,
40,Baseline Jan 2021,indexed,6.2
41,Baseline Jan 2021,indexed,6.4
2026-03-02,12-Month Rolling Baseline,rolling,3.5
"""
GR = """time,series,value
2026-02-02,Dissimilarity,33.1
2026-03-02,Dissimilarity,
"""


def run(wf=WF, gr=GR, retrieved=datetime(2026, 4, 15, tzinfo=timezone.utc)):
    c = YaleDissimilarity()
    items = [RawItem(u, body.encode(), 200, retrieved, "h" * 64) for u, body in ((WORKFORCE, wf), (GRADUATES, gr))]
    return c, c.extract(items)


def test_months_map_to_dates_blank_cells_are_skipped_and_graduates_have_their_own_key():
    c, obs = run()
    got = {(o.series_key, str(o.as_of_date)): o.value_numeric for o in obs}
    assert got == {
        ("yale_budget_lab_data.us_workers.occupation_dissimilarity_pp.m", "2026-03-01"): 7.1,  # month 40 from Nov 2022
        ("yale_budget_lab_data.us_workers.occupation_dissimilarity_pp_jan2021.m", "2024-05-01"): 6.2,
        ("yale_budget_lab_data.us_workers.occupation_dissimilarity_pp_jan2021.m", "2024-06-01"): 6.4,
        ("yale_budget_lab_data.recent_vs_older_grads.occupation_dissimilarity_pp.m", "2026-02-01"): 33.1,
    }  # the rolling baseline is not stored
    assert c.errors == []


def test_a_renamed_series_is_a_layout_change_and_an_old_newest_month_is_a_note():
    with pytest.raises(LayoutChanged):
        run(wf=WF.replace("Baseline Jan 2021", "Baseline January 2021"))
    with pytest.raises(LayoutChanged):
        run(gr=GR.replace("Dissimilarity", "Index"))
    c, obs = run(retrieved=datetime(2026, 11, 1, tzinfo=timezone.utc))
    assert obs and c.errors == ["newest month 2026-03-01; the tracker may have moved, so check its manifest"]
