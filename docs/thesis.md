# Thesis monitor (2026-09-12)

Generated nightly from `thesis.py`; do not edit.


## Normal-technology thesis, falsification test: **does not hold**

Rule: (ratio ≤ 2 AND 50% horizon below the ceiling AND 80% horizon > 8 h) AND (≥ 3 trackers break) AND (hours > 20% OR TFP > trend + 1pp for 4 years)

- ✗ 50%/80% horizon ratio ≤ 2 — 6.34× as of 2026-03-05 (obs: 11a8bbd2, 858c619b)
- ✗ 50% horizon below the suite's 16 h ceiling, so a falling ratio is not censoring — 1045 min as of 2026-04-07 (obs: a3cd6bce)
- ✗ 80% horizon > 8 h — 186 min as of 2026-04-07 (obs: c256ff03)
- ✗ ≥ 3 labour trackers show a concurrent AI-attributable break — 0 of 4 as of 2026-07-31 (obs: 14ca8a23, 1fce2bb8, 4b51d49e…)
- ✗ work hours assisted by AI > 20% — 6.3% as of 2026-06-30 (obs: 7a1c89cb)
- ✗ TFP > trend + 1pp for ≥ 4 consecutive years — 2022 -1.1%, 2023 +1.6%, 2024 +1.5%, 2025 +0.8% (obs: 3af5026f, 3cb18cc9, 3cb18cc9…)

## Normal-technology thesis, strengthening test: **does not hold**

Rule: ratio non-decreasing (within 10%) AND ladder ≤ L4 AND four releases with at most one break each

- ✗ 50%/80% ratio non-decreasing over the last four models — 10.3×, 6.4×, 4.3×, 6.3× (obs: 39c8213a, 8f73b56b, 959db6dd…)
- ✓ continual-learning ladder ≤ L4 — L3 as of 2026-05-27 (obs: 1b7d08db, dc983a81)
- ? at most one tracker breaking through four monthly releases — 1 readings, max break count 0 (obs: 14ca8a23, 1fce2bb8, 4b51d49e…)

## Invention-side WARNING (bottleneck #86 under test): **untestable**

Rule: both conditions, on independently verified series (OpenAI's self-reported 3.1 and >50% do not qualify)

- ? independently verified agent-workdays per human-workday > 1 — untestable: only self-reported (tier 7) 3.1 as of 2026-08-15 (obs: 6cd4efa0)
- ? intervention rate on 4–8 h agent tasks < 50% — untestable: only self-reported (tier 7) 50% as of 2026-07-31 (obs: fcf1e544)

## Capture thesis 'rents migrate up the stack': **CONTRADICTED**

Rule: supported when labs are up ≥ 5pp and chips down, on gross profit; contradicted when chips' share is flat or rising (the brief's app-margin branch needs margins net of inference, which are not public)

- ✗ labs' share of stack gross profit up ≥ 5pp over four quarters (apps unmeasured) — 2.6% → 7.3%; the lab layer is a grade C estimate (run-rate × revenue-minus-inference margin) (obs: 0b6d0c8c, 1a2c7e77, 2a23fc81…)
- ✗ chips' share of stack gross profit down ≥ 5pp over four quarters — 60.6% → 69.5% (obs: 0b6d0c8c, 1a2c7e77, 2a23fc81…)
- ? Contradicted when: — 
- ✓ chips' share of stack gross profit flat or rising over four quarters — 60.6% → 69.5% (obs: 0b6d0c8c, 1a2c7e77, 2a23fc81…)

## Capture thesis 'consumers keep most of the surplus': **untestable**

Rule: surplus above twice the approximate revenue ceiling holds, below the enterprise-spend floor fails, in between is untestable; the doubling covers the willingness-to-accept wedge and the consumer subscriptions the ceiling omits

- ? consumer surplus (WTA) > twice the approximate revenue ceiling, bracketed — $172B surplus against a floor of $37B (US enterprise spend) and a bar of $292B, twice the $146B ceiling (lab run-rates plus enterprise spend; consumer subscriptions sit outside it, and a WTA estimate runs at least twice WTP) (obs: 2d481469, 6012e72e, 143dcf3e…)
