"""Why the evaluator holds a number its range would score: one function beside `flow_status`, used by the argument
page's and the diffusion page's figures, and checked here against the evaluator for every ranged indicator."""

import inspect

from ai_tracker import argument, cli, diffusion_figures
from ai_tracker import store as st
from ai_tracker.analysis import bands
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.schema import UNSCORED


def test_held_reasons_agrees_with_the_evaluators_status_for_every_ranged_indicator():
    s = st.Store()
    s.derived = run_metrics(s.con)  # data/derived.jsonl is git-ignored: a clean checkout has none
    seen = 0
    for i in s.seed.indicators:
        value, _, _, tier = s.band_input(i)
        if value is None or i.normal_band is None or i.direction_rule:
            continue
        lo, hi = s.band_interval(i)
        raw = bands._band(value, i.normal_band, i.fast_band, i.falsifying_band).value
        new = bands.flow_status(value, i.normal_band, i.fast_band, i.falsifying_band, tier, lo, hi).value
        tonight = "emerging" if new not in UNSCORED and bands.single_non_primary(s, i) else new
        why = bands.held_reasons(s, i, value)
        assert set(why) <= set(bands.HELD) and len(set(why)) == len(why), (i.id, why)
        # a reason exactly when the range would score the number and the evaluator's rules do not
        assert bool(why) == (raw != "emerging" and tonight == "emerging"), (i.id, raw, tonight, why)
        seen += 1
    assert seen >= 40


def test_both_pages_and_the_evaluator_share_the_one_rule():
    assert not hasattr(argument, "_held") and not hasattr(diffusion_figures, "_held")
    assert "held_reasons(" in inspect.getsource(argument) and "held_reasons(" in inspect.getsource(diffusion_figures)
    assert cli._single_non_primary is bands.single_non_primary  # the two-source rule `evaluate` applies
