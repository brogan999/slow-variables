# Automatability Census — data bundle

Which US knowledge work can be handed to AI today, task by task, role by role, industry by industry.
Built in `~/automatability-census`; the published page is https://claude.ai/artifact/DpV6DMm47BsrKhjinG7hqg.
`manifest.json` holds sha256s, row counts and the reconciliation: every table's "can go" sums to the same
headline ($1,014.5bn of $7.00T knowledge payroll). Each version lives in `out/bundle/<version>/`; `out/bundle/latest`
points at the newest. Rebuild with `uv run python src/export_bundle.py <version>`.

## The rule
A task **goes** when it can be checked within hours (`horizon` ≤ 1), something other than a human expert can
check it (`grader` = 2), a single failure costs ≤ ~$10k (`stakes` ≤ 2), and it doesn't need a body. Each task is
scored by up to three models (Sonnet, Haiku, Gemini); the verdict is a vote, ties go to the most precise scorer
(Gemini, then Sonnet), and Haiku never decides alone.

## Files
| file | grain | key columns |
|---|---|---|
| `tasks.csv` | one O*NET task (10,752 knowledge tasks) | `horizon` 0 instant … 5 never; `spec_entropy` 1–5; `grader` 0 none / 1 expert only / 2 automated; `stakes` 0 <$100 … 4 ≥$1M or irreversible; `goes`, `why`, `physical`, `contested`, `agreed_all_three`, per-scorer votes; `blocked_by_verifier` (fast, cheap to get wrong, but only an expert can check it today); `time_share` of the role's task time; `task_payroll_usd` = time_share × role wage bill |
| `roles.csv` | SOC occupation (425) | `share_goes` with `band_lo`–`band_hi` (strict/loose rule); `freed` (can go, $), `freed_agreed3` (all three scorers agree), `freed_contested`; `payroll_scored_by_three` (payroll in tasks all three scored — 0 means Gemini never scored the role, so a 0 `freed_agreed3` there means *not scored by all three*, not *nobody agrees*); `ai_exposure` (task time AI already touches, ρ 0.878 vs the published measure); `cost_share_stays_after_modelled` is **modelled** at σ = 0.5 |
| `role_industry.csv` | occupation × 4-digit NAICS (22,001) | OEWS staffing: `emp`, `wage_bill`, `freed` = wage_bill × the role's share that goes, `agreed3` the same for the all-three-agree share. Both sum to their headlines |
| `industries.csv` | 4-digit NAICS (247) | `total` payroll (every worker), `know` (scored knowledge roles), `freed`, `agreed3`, `payroll_scored_by_three`, `blocked`, `share_total` |
| `functions.csv` | business function (22) | `payroll`, `freed`, `agreed3`, `payroll_scored_by_three`, `share_goes` + range, `blocked_by_verifier_usd` |
| `deal_sheets.json` | 9 archetype cards + 5 not carded | stance keeps / check / passes is **reasoned from invoice structure, not measured**; each card carries `freed_agreed3` and `payroll_scored_by_three`, each of its roles `a3` and `s3` (0 = not scored by all three); two cards are occupation-anchored (sized by one occupation, not an industry); comps illustrate revenue models, are not researched targets; every factual claim has a source URL |
| `validation.json` | — | pre-registered gates (passed and failed), confidence dial (each step with `agreed3`; field meanings in `dial_fields`), `scorers` (letter → model), `physical_gate` (removed payroll and the spot-check), σ table, the exploratory API-vs-chat channel test, scorer adjudication, retention placebo |

## Caveats that must travel with any figure
- **Structural, not a forecast.** Says what *can* go by the rule today — not when, how fast, or who keeps the saving.
- **Scorer disagreement is large.** On tasks all three scored, "can go" ranges $370bn (Gemini) to $1.11T (Haiku). Lead
  with `agreed_all_three` ($213bn) where confidence matters; treat role figures as bands, not ranks.
- **Gemini gap.** Gemini hit a spending cap before scoring Sales, Office & Admin and part of healthcare: $481bn of the
  headline was decided without it ($434bn where both Claude models agree).
- **Retention is not measured** — every estimator tried failed a noise placebo or flipped sign. Don't publish "keeps X%".
- **Specification entropy** is not in the rule. The channel test (harder to specify → less of a task's AI use comes via the
  API) is **exploratory**: designed after seeing the data; pre-committed to one unchanged re-run on the next Economic Index release.
- No human has judged individual tasks; the human anchor is the Labor Department's occupation-level worker survey.
- O*NET under-describes coordination and exception handling, which biases "can go" upward.
- Physical-work gate: a reproducible spot-check (60 payroll-weighted draws, seed 7, labels in the census repo's
  `rubric/physical_spotcheck_labels.csv`) found 10% of the removed payroll is really desk work (90% interval 4–19%),
  so the headline may be ~$18–76bn low. Figures in `validation.json` → `physical_gate`.
- "Agreed by all three" is only as wide as Gemini's coverage: where `payroll_scored_by_three` is 0 it cannot be positive.

## Identifiers
- `task_id` is O*NET's own **Task ID** (Task Statements, database 30.2), unique per row: e.g. 1 = Sales Managers,
  "Resolve customer complaints regarding sales and service." The Economic Index keys its task rows on the same id.
- `occ` is the 6-digit SOC 2018 code (O*NET-SOC without the `.00`); `naics` is OEWS's 6-character form of a 4-digit NAICS.

## Text fields
`why` is **not model prose**: it is one of 10 fixed phrases chosen by code from the voted scores (e.g. "no automated
way to check it"). The models returned numbers only; their free-text justifications are not in the bundle.
Deal-sheet text was written for the census and fact-checked against the linked sources.

## Terms
- O*NET 30.2: CC BY 4.0 (U.S. Department of Labor, Employment and Training Administration).
- BLS OEWS and industry productivity: U.S. government works, public domain.
- Anthropic Economic Index (Hugging Face `Anthropic/EconomicIndex`): MIT licence.
- Scores and verdicts: produced by this project with Claude (Anthropic API) and Gemini (Google API) under their
  commercial terms, which leave output ownership with the customer; released here under CC BY 4.0.
This is the project's reading of the published terms, not legal advice.
