from datetime import date

from ai_tracker.ingest.connectors.anthropic_ei import FILES, AnthropicEi


def test_raw_release_buckets_follow_anthropic_definition(raw):
    c = AnthropicEi()
    items = [raw("anthropic_ei_raw.csv"), raw("anthropic_ei_raw.csv"), raw("anthropic_ei_monthly.csv")]
    assert len(items) == len(FILES)
    rows = {(r.series_key, r.as_of_date): r for r in c.extract(items)}
    nov = rows[("anthropic_ei.global.augmentation_share.pt", date(2025, 11, 19))]
    assert (
        abs(nov.value_numeric - 0.5327) < 0.001 and nov.tier == 2 and nov.grade == "B"
    )  # (19.7+27.2+4.8)/(100-3.0)
    assert (
        abs(rows[("anthropic_ei.global.automation_share.pt", date(2025, 11, 19))].value_numeric - 0.4673)
        < 0.001
    )
    may = rows[("anthropic_ei.global.augmentation_share.pt", date(2026, 5, 31))]
    assert may.value_numeric == 0.5138  # the published bucket metric is used as-is
    # published bucket equals the mode sum normalised without `none`, so the two formats agree
    modes = {
        k: rows[(f"anthropic_ei.global.mode_{k}_share.pt", date(2026, 5, 31))].value_numeric
        for k in ("learning", "task_iteration", "validation", "none")
    }
    assert (
        abs(
            (modes["learning"] + modes["task_iteration"] + modes["validation"]) / (1 - modes["none"]) - 0.5138
        )
        < 0.002
    )
