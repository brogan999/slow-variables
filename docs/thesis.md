# Thesis monitor (2026-09-09)

Generated nightly from `thesis.py`; do not edit.


## Normal-technology thesis FALSIFIED: **does not hold**

Rule: (ratio ≤ 2 AND 80% horizon > 8 h) AND (≥ 3 trackers break) AND (hours > 20% OR TFP > trend + 1pp for 4 years)

- ✗ 50%/80% horizon ratio ≤ 2 — 6.34× as of 2026-03-05 (obs: 11a8bbd2, 858c619b)
- ✗ 80% horizon > 8 h — 186 min as of 2026-04-07 (obs: c256ff03)
- ✗ ≥ 3 labour trackers show a concurrent AI-attributable break — 0 of 4 as of 2026-07-31 (obs: 2ec713fc, 83c12bef, a9276b9d…)
- ✗ work hours assisted by AI > 20% — 6.3% as of 2026-06-30 (obs: 7a1c89cb)
- ✗ TFP > trend + 1pp for ≥ 4 consecutive years — 2022 -1.1%, 2023 +1.6%, 2024 +1.5%, 2025 +0.8% (obs: 3af5026f, 3cb18cc9, 3cb18cc9…)

## Normal-technology thesis STRENGTHENED: **does not hold**

Rule: ratio non-decreasing AND ladder ≤ L4 AND four clean tracker releases (the ladder has no series yet, so this cannot resolve)

- ✗ 50%/80% ratio non-decreasing over the last four models — 10.3×, 6.4×, 4.3×, 6.3× (obs: 39c8213a, 8f73b56b, 959db6dd…)
- ? continual-learning ladder ≤ L4 — untestable: no observations yet
- ? precise nulls persist through four monthly tracker releases — 1 readings, max break count 0 (obs: 2ec713fc, 83c12bef, a9276b9d…)

## Invention-side WARNING (bottleneck #86 under test): **untestable**

Rule: both conditions, on independently verified series (OpenAI's self-reported 3.1 and >50% do not qualify)

- ? independently verified agent-workdays per human-workday > 1 — untestable: no observations yet
- ? intervention rate on 4–8 h agent tasks < 50% — untestable: no observations yet

## Capture thesis 'rents migrate up the stack' SUPPORTED: **does not hold**

Rule: labs + apps up ≥ 5pp AND semis down (contradicted if semis hold and app margins net of inference fall)

- ? labs + apps share of stack margin up ≥ 5pp over four quarters — untestable: no filed or estimated lab/app margin series yet
- ✗ semis' share of stack margin falling over four quarters — 51.0% → 57.3% (obs: 33e002b2, 4e31dd06, 6c32c53e…)

## Capture thesis 'consumers keep most of the surplus' HOLDS: **HOLDS**

Rule: surplus > revenue (revenue side is enterprise spend only until consumer spend is sourced)

- ✓ consumer surplus (WTA) > US GenAI revenue — $172B surplus vs $37B enterprise spend (consumer spend not yet ingested) (obs: 2d481469, 6012e72e)
