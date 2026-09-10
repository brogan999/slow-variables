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
