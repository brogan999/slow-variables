# Automatability Census — data bundle (v3)

Which US knowledge work passes a **structural hand-over screen**, task by task, role by role, industry by industry.
Each version lives in `out/bundle/<version>/`, and `out/bundle/latest` points at the newest (a `--draft` export never moves it).
`manifest.json` holds sha256s, row counts and the reconciliation. Every table's "passes" and "agreed by all three" sum to
the same headlines, and **the published per-scorer columns reproduce 100% of the verdicts**. Rebuild with
`uv run python src/export_bundle.py <version>`.

## What the screen is, and is not
A task **passes** when at least two of three scorers (Claude Sonnet, Gemini 3.1 Pro, GPT-6 Sol) each find:
- it can be checked within hours (`horizon` ≤ 1);
- a check that exists today settles the property that defines success (`check` = 2);
- a single failure costs up to about $10k (`stakes` ≤ 2).

It must also be neither **physical** (either physical labeller, or O*NET's physical-activity codes) nor an **accountable
sign-off**: approving, authorising, certifying, assigning others' work, or documenting a diagnosis (`src/verb_gate.py`).
A task without three valid scores is **not called**: it never passes, and its payroll stays in the denominator.

**It is structural, not a capability claim and not a forecast.** The scorers were told to ignore whether today's AI can
do a task. So a task can pass and still be beyond current systems, which is why `ai_exposure` (observed use, the
published measure) sits beside every role. **Passing is not saving.** `modelled_saving_usd` is what a 36% cost cut on
passing tasks would save under a CES at σ = 0.5. It is modelled, not measured, and far below the payroll that passes.

The rule, the rubric (`rubric/v2.md`), the gates, the vote and the stop rules were frozen in `preregistration_v3.md` and
committed before any v3 score existed.

## Files
| file | grain | key columns |
|---|---|---|
| `tasks.csv` | one O*NET task (knowledge tasks) | `passes`, `why`, `not_called`, `physical` (+ `physical_both`, per-labeller and O*NET-code columns), `accountable`, `agreed_all_three`, `contested`, `blocked_by_missing_check`, `time_share`, `task_payroll_usd`; **per scorer** `horizon_*` 0 instant … 5 never, `check_*` 0 outcome only / 1 a person's judgement / 2 an existing check, `stakes_*` 0 <$100 … 4 ≥$1M, `spec_entropy_sum_*` 0–12, `passes_by_*` |
| `roles.csv` | SOC occupation | `share_passes`; `rule_strict`/`rule_loose` (the share under the stricter and looser rules, **not** an uncertainty band); `scorer_min`/`scorer_max` and `share_<scorer>` (the share under each scorer's own verdict); `passes_usd`, `agreed3_usd`, `contested_usd`, `payroll_scored_by_three`, `not_called_usd`; gate removals; `time_share_basis` (rated / partly — unrated tasks carry the role's median weight / equal — no ratings); `split` (equal = BLS publishes the role only with its siblings, split evenly); `ai_exposure`; `modelled_saving_usd` |
| `role_industry.csv` | occupation × 4-digit NAICS | OEWS staffing: `emp`, `wage_bill`, `passes_usd`, `agreed3_usd`, `payroll_scored_by_three` |
| `industries.csv` | 4-digit NAICS | `total` (every worker), `know`, `passes_usd`, `agreed3_usd`, `payroll_scored_by_three`, `blocked`, `share_total` |
| `functions.csv` | business function | `payroll`, `passes_usd`, `share_passes`, `rule_strict`/`rule_loose`, `agreed3_usd`, `payroll_scored_by_three`, `blocked_by_missing_check_usd` |
| `deal_sheets.json` | archetype cards + not carded | per card: `passes_usd`, `agreed3_usd`, `payroll_scored_by_three`, `rule_strict_usd`/`rule_loose_usd` (payroll passing under the stricter / looser rule); per role: `title`, `wage_bill`, `share_passes`, `passes_usd`, `agreed3_usd`, `payroll_scored_by_three`. The v2 keys (`freed*`, `t/b/g/f/a3/s3`) remain one more version as deprecated aliases; stance is **reasoned from invoice structure, not measured**; occupation-anchored cards are sized by one occupation; disclosures cover PEOs inside NAICS 5613 and the labs / revenue-cycle overlap (not additive); comps illustrate revenue models |
| `validation.json` | — | `gates`, each with `k`: `pre17` (pre-registered 17 Sep), `pre24` (pre-registered 24 Sep), `post` (post hoc); `validation` (AI-alone test raw and within occupation, agreement κs, R1–R4 v3 rerun beside the 17 Sep run); `channel` (two-part model); `dial` with `dial_fields`; `physical_gate` (removals, sensitivity grid, two-sided spot-check); `not_called`; `scorers` |

## Caveats that must travel with any figure
- **Post hoc vs confirmatory.** Every v3 comparison against the 2026-06-26 Economic Index release is post hoc: the rule was
  shaped after seeing it. The AI-alone and channel tests are pre-committed to run once, unchanged, on the next release.
- **Scorers disagree.** Show verdict κ and each scorer's own total beside the headline, and show "all three pass" beside
  every "passes".
- **Retention is not measured.** Don't publish "keeps X%".
- **Physical gate error runs both ways.** See `validation.json → physical_gate.spotcheck` (95% intervals).
- **No human has judged individual tasks.** The human anchor is the Labor Department's occupation-level worker survey.
- **O*NET's task lists under-describe coordination and exception handling,** which biases "passes" upward.

## Identifiers
- `task_id` is O*NET's own Task ID (Task Statements, database 30.2).
- `occ` is the 6-digit SOC 2018 code.
- `naics` is OEWS's 6-character form of a 4-digit NAICS.

## Text fields
`why` is one of a few fixed phrases, chosen by code from the scores and gates. It is not model prose.

## Terms
- O*NET 30.2: CC BY 4.0 (U.S. Department of Labor, ETA).
- BLS OEWS and industry productivity: public domain.
- Anthropic Economic Index: MIT.
- Scores and verdicts: produced with Claude, Gemini and GPT-6 Sol under their providers' commercial terms, which leave
  output ownership with the customer. Released here under CC BY 4.0.

This is the project's reading of the published terms, not legal advice.
