from datetime import date, datetime, timezone

import pytest

from ai_tracker.schema import (
    Basis,
    Extraction,
    Observation,
    Review,
    Tier,
    cap_status_by_tier,
    grade_from_tier,
)

BASE = dict(
    series_key="x.y.z.pt",
    unit="u",
    as_of_date=date(2026, 1, 1),
    published_date=date(2026, 1, 1),
    retrieved_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    url="https://e.test",
    content_hash="h",
    http_status=200,
    source_id="s",
    tier=Tier.CREDIBLE_REPORTING,
    audited_vs_reported=Basis.reported,
    extraction_method=Extraction.api,
    extractor_version="s-1",
    raw_snippet="snip",
)


def test_required_fields_and_one_value():
    with pytest.raises(ValueError):
        Observation(**{**BASE, "url": None}, value_numeric=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        Observation(**BASE)  # no value at all
    with pytest.raises(ValueError):
        Observation(**BASE, value_numeric=1, value_text="one")


def test_tier_guards():
    with pytest.raises(ValueError):
        Observation(**{**BASE, "audited_vs_reported": Basis.audited}, value_numeric=1)  # tier 5 never audited
    assert cap_status_by_tier("faster_than_normal", Tier.ACTOR_STATEMENT) == "emerging"
    assert cap_status_by_tier("faster_than_normal", Tier.BENCHMARK) == "faster_than_normal"


def test_manual_lands_pending_and_ids_are_deterministic():
    a = Observation(**{**BASE, "extraction_method": Extraction.manual}, value_numeric=1)
    assert a.review_status == Review.pending
    b = Observation(**BASE, value_numeric=1)
    c = Observation(**BASE, value_numeric=1)
    d = Observation(**BASE, value_numeric=2)
    assert b.id == c.id and b.id != d.id and b.review_status == Review.approved


@pytest.mark.parametrize(
    "tier,basis,single,grade",
    [
        (Tier.BENCHMARK, Basis.reported, False, "A"),
        (Tier.OFFICIAL_FILING, Basis.reported, False, "A"),
        (Tier.OFFICIAL_FILING, Basis.company_stated, False, "B"),
        (Tier.PUBLISHED_ANALYSIS, Basis.reported, False, "B"),
        (Tier.PUBLISHED_ANALYSIS, Basis.estimated, False, "C"),
        (Tier.CREDIBLE_REPORTING, Basis.reported, False, "C"),
        (Tier.ACTOR_STATEMENT, Basis.reported, False, "D"),
        (Tier.BENCHMARK, Basis.reported, True, "D"),
    ],
)
def test_grade_table(tier, basis, single, grade):
    assert grade_from_tier(tier, basis, single) == grade
