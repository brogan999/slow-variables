from ai_tracker.query.citecheck import Record, check

R = {
    "x": Record("x", "obs", [1.72e11], "USD", "reached $172 billion in March 2026"),
    "y": Record("y", "obs", [0.0627], "share"),
    "z": Record("z", "derived", [0.0], "count"),
    "h": Record("h", "obs", [185.9, 96.0, 396.0], "minutes"),
    "r": Record("r", "derived", [6.34], "ratio"),
    "i": Record("i", "ind", [213.0, 122.0], "days"),
}


def test_cited_numbers_pass_in_the_site_s_own_renderings():
    ok = check(
        "Consumer surplus reached $172B [obs:x]. Hours assisted were 6.3% [obs:y]. The 80% horizon is 3.1 h (1.6 h–6.6 h) [obs:h]. The ratio is 6.34× [derived:r]. The normal band starts at 213 days [ind:i].",
        R,
    )
    assert ok.ok, ok.failures


def test_uncited_and_wrong_numbers_fail_and_are_annotated():
    res = check("Consumer surplus reached $172B. The share was 12% [obs:y].", R)
    assert not res.ok
    assert any("uncited" in f for f in res.failures) and any("12%" in f for f in res.failures)
    assert "⟦unverified: $172B⟧" in res.annotated and "⟦unverified: 12%⟧" in res.annotated


def test_years_small_counts_and_zero_of_four_pass():
    res = check("In 2026, 0 of 4 trackers broke [derived:z]. Two sources agree.", R)
    assert res.ok, res.failures


def test_snippet_text_counts_as_a_source():
    assert check("The paper said 172 billion [obs:x].", R).ok


def test_iso_dates_are_not_numbers():
    res = check("Between 2026-09-01 and 2026-09-10 nothing moved.", R)
    assert res.ok and res.numbers == []


def test_a_bullet_is_one_claim_and_event_reasons_count():
    recs = {
        **R,
        "e1": Record("e1", "event", [55.0], "", "Evaluator: 128.7 days is inside the band. Second sentence."),
    }
    ok = check(
        "- **Horizon** moved to faster, confidence 55 [ind:i]. Evaluator: 128.7 days is inside the band. Second sentence. [event:e1]",
        recs,
    )
    assert ok.ok, ok.failures
    bad = check("Horizon moved. Evaluator: 128.7 days is inside the band. [event:e1]", recs)
    assert not bad.ok


def test_hash_ids_are_labels():
    assert check("Bottleneck #86 is under test.", R).numbers == []
