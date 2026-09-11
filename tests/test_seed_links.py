from ai_tracker.store import Seed


def test_bottlenecks_and_compare_reference_real_things():
    s = Seed.load()
    inds = {i.id for i in s.indicators}
    preds = {p.id for p in s.predictions}
    assert [b.id for b in s.bottlenecks] == list(range(1, 90))
    codes = {e.code for e in s.essays}
    assert all(c in codes for b in s.bottlenecks for c in b.source_codes)
    assert all(i in inds for b in s.bottlenecks for i in b.related_indicators)
    assert {b.bucket_id for b in s.bottlenecks} <= {b.id for b in s.buckets}
    assert s.compare and all(r.indicator in inds for r in s.compare)
    assert all(p in preds for r in s.compare for p in r.nk_predictions + r.ai2027_predictions)


def test_skipped_sources_are_unique_and_the_paid_tier_is_listed():
    from ai_tracker.ingest.connectors.paid import PAID
    from ai_tracker.store import Seed

    seed = Seed.load()
    skipped = [s.id for s in seed.skipped]
    sources = {s.id for s in seed.sources}
    assert len(skipped) == len(set(skipped)) and not set(skipped) & sources
    assert {c.source_id for c in PAID} <= set(
        skipped
    ) | sources  # the paid tier shows on /sources, never silently
