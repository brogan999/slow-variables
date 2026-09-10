# ai-tracker — build plan

## Context

Two briefs landed in ~/Downloads on 9 Sep 2026:

- **AI Tracker Brief v2 — Technology Diffusion** (`v2`): the unified spec. One data store, one methodology, one indicator object, two L0 lenses (diffusion ⇄ capture), crosswalk as a first-class table. M0–M6, 7 weeks.
- **Value Capture Tracker Part 1** (`P1`): the earlier capture-side build prompt. Richer on 21 sub-layers with seed companies, ingestor endpoints, cleverhack directories, 13 seed indicators, circular-financing ledger, reference figures.

They describe the same product from two ends. `v2` is canonical; `P1` is the capture-lens appendix. The Notion page "Grand Theory of AI Development & Diffusion" frames the goal: *the business-relevant version of the AI 2027 tracker*, aimed at "which $1T companies exist in 2035".

Outcome: a repo at `~/ai-tracker` holding both briefs and the research corpus, shipping a **thin vertical slice first** (one connector → one indicator → one page, live data, day 2), then widening connector-by-connector in `v2`'s milestone order. Nothing publishes without a traceable observation.

### What already exists on disk (found by search)

| Brief asks for | Found | Path |
|---|---|---|
| 89-bottleneck list | ✅ complete, with 224-row raw JSON + extraction prompt | `~/normaltech-predictions/bottlenecks.md`, `bottlenecks_raw.json`, `BOTTLENECK_PROMPT.md` |
| N&K prediction material | ✅ 747 predictions with verbatim quote + URL + verified flag | `~/normaltech-predictions/predictions.json`, `normaltech-predictions.md`, `worldview-summary.md`, `corpus/` (70 posts) |
| 11-layer a private value-chain map value-chain map | ✅ | `~/Documents/a private value-chain map Thesis/competitive/competitive-landscape.md`; ten→eleven crosswalk paragraph in `value-chain-scorecard.md` |
| Teece / Nordhaus / Perez / Ding notes | ✅ scattered | `~/Documents/a private value-chain map Thesis/06-theory-of-value-capture/theory-of-value-capture.md`; `~/vc-frameworks-project/phase1/3-modern-era/technological-revolutions-perez.md`; Ding in `bottlenecks.md` §Theoretical foundations |
| Prior attempt at this product | ✅ `~/ai-value-chain` (Aug 2026, Next 16 + Prisma/Postgres, not git-inited, DB tables never created). Has a working Epoch ZIP connector with declarative column maps (`config/sources.yaml`), SEC XBRL connector (`src/lib/ingest/connectors/sec-xbrl.ts`: quarterly filter, restatement dedupe), 23-layer taxonomy, honesty rules | Port the *patterns*; do not fork (Postgres ≠ brief; TS parquet story is weak) |
| "Diffusion Tracker v2" report, "Measuring AI Value Capture" report, venture-sources output, five-tier dependency graph | ❌ not on disk — live in chat only | Value-capture chat linked from the Notion page: `[private chat]…`. **Alex exports these**; not a blocker |

Live-verified today: Epoch ships ZIPs (`epoch.ai/data/ai_companies.zip`, `ai_models.zip`, `ml_hardware.zip`, `ai_chip_sales.zip`), not the CSV paths in `P1`; SEC companyfacts works for NVDA (needs `User-Agent`); METR publishes `metr.org/assets/benchmark_results_1_1.yaml`; Census BTOS has **no API** (404) and a JS-rendered downloads page; ai2027-tracker methodology = 7 tiers, 6 proxy types, 6 statuses, 0–95 confidence, 9-section page.

Toolchain present: python3.12 + uv, node 25 + pnpm, gh, vercel, fly. Postgres 14 running (unused by this plan).

## 1. Step 0 — the folder

```
~/ai-tracker/
  docs/briefs/ai-tracker-brief-v2.md              ← git mv from Downloads
  docs/briefs/value-capture-tracker-part1.md      ← git mv from Downloads
  docs/research/bottlenecks.md, bottlenecks_raw.json, BOTTLENECK_PROMPT.md, predictions.json,
                worldview-summary.md, betterbrain-competitive-landscape.md, betterbrain-value-chain-scorecard.md
  docs/interpretation/theory-of-value-capture.md, technological-revolutions-perez.md   (copies; write nothing new)
  docs/prior-art.md      ← 10 lines pointing at ~/ai-value-chain and what was ported
```

`git init`, `gh repo create ai-tracker --private`. Move (not copy) the two briefs so Downloads stops being the source of truth.

## 2. Decisions (spec reconciliation + review outcomes)

| Topic | Decision | Why |
|---|---|---|
| Stack | **Python 3.12 (uv) spine + Next.js 16 site**, per `v2` §9. Deps: `httpx pydantic duckdb pyyaml`; `pdfplumber` only with the manual connector. No polars (DuckDB reads CSV/JSON/XLSX itself) | Brief is explicit; DuckDB/parquet are Python-native. Alternative (TS-only, lift `~/ai-value-chain`) rejected: Postgres + weak TS parquet story |
| Layers | **7** (`v2` Appendix D) | Crosswalk distinguishes bucket 3 adopters from bucket 4 labour/consumers. Note: bucket→layer is not one-to-one; build nothing that assumes it |
| Sub-layer 2 | Rename to "Hyperscalers, neoclouds & GPU clouds" | `capex_to_revenue_stack` needs MSFT/GOOGL/AMZN/ORCL a home; no 22nd sub-layer |
| Evidence grade | Store tier 1–7; letter A–D derived (`grade_from_tier`). Tier 4 `reported` (gov stats) → A; tier 4 `company_stated` (8-K) → B | `v2` §1.2 rule as written would grade BLS "C" |
| Basis flag | `audited_vs_reported` ∈ {audited, company_stated, reported, estimated}. `10-K → audited`; `10-Q/8-K → company_stated` | 10-Qs are unaudited |
| Committed data | **Append-only `data/observations/<source>.jsonl`**, sorted, new/superseding rows only. Parquet, `.duckdb`, raw cache gitignored. Raw cache uploaded as a GitHub Actions artifact | Readable PR diffs; no GB/yr of binary snapshots. Deviation from `v2` "parquet in repo" — rebuild guarantee holds from `seed/ + data/` |
| Review queue | **A PR is the queue.** Tier 1/4 API rows land `approved`; `manual`/`scrape`/`llm_extract` land `pending`; merge to main flips `pending→approved`; reject = delete row, reason in commit message. No admin page | `v2` §8 says PRs; one operator |
| Status changes | `evaluate` writes `data/proposed_status_events.jsonl` with blank `reason`; human fills or deletes; merge appends to `data/status_events.jsonl`; `check` fails if current status ≠ latest StatusEvent | `v2` §10 rule 1 |
| Unmeasured indicators | `published: false` until ≥1 approved observation. L0 renders an "unmeasured" glyph, no status word. `proposed_status` stays a private YAML field `check` uses to flag disagreement once data lands | `not_yet_measurable` means *cannot* be measured, not *not yet fetched*; showing "expected: fast" is model knowledge |
| Appendix A/C figures | Enter via the **`manual` connector** (§3.2), never typed into indicators | `v2` §10 rule 2 |
| Series breaks | Separate `series_key` per instrument (`btos_firm_use_v1/_v2`, BBD waves); `disputed` reserved for contested figures | |
| Web | Next.js App Router, **no `output: 'export'`**; no route handlers ⇒ static by construction. Reads committed `web/data/*.json`. Vercel root = `web/`, runs only `next build` | M5 query console needs a dynamic route; the flag buys nothing today |
| Query service (M5) | Python on Fly (DuckDB + semantic layer live there); web calls it | Decided now so the JSON contract doesn't move |
| CI blocking | `ruff`, `pytest`, `ai-tracker check`, `next build`. `mypy --strict` advisory for month 1 | duckdb/pydantic stub fights |
| Models | `claude-sonnet-5` routine, `claude-fable-5-1` synthesis (M5) | `P1`'s sonnet-4-6 is stale |

Repo `CLAUDE.md` = `v2` §10 verbatim + `P1` rule 3 (prompt-injection scrub) + `P1` rule 5 (robots.txt) + `~/ai-value-chain/AGENTS.md`'s warning: read `node_modules/next/dist/docs/` before writing Next 16 routes.

## 3. Architecture

```
ai-tracker/
  CLAUDE.md README.md pyproject.toml .github/workflows/{ci,nightly}.yml
  docs/{briefs,research,interpretation}/ methodology.md sources.md bands.md changelog.md(generated) thesis.md(generated)
  seed/ buckets.yaml layers.yaml sublayers.yaml crosswalk.yaml entities.yaml sources.yaml
        indicators/diffusion.yaml indicators/capture.yaml manual_observations.yaml
        predictions.yaml bottlenecks.yaml            (M3)
  semantic/metrics.yaml
  src/ai_tracker/
    schema.py            models + enums + grade_from_tier + tier guards        (Appendix A)
    store.py             seed YAML + data/*.jsonl → in-memory DuckDB; export → web/data/*.json
    ingest/base.py       Connector: urls, fetch (cache, robots, UA), extract, run → FetchLog; LayoutChanged; expect()
    ingest/scrub.py      html→text, drop hidden/comment nodes, regex agent-directed phrases, return (text, flags)
    ingest/connectors/   metr.py sec_xbrl.py manual.py bls.py epoch.py         (slice order)
    analysis/bands.py direction.py metrics.py                                   (fits.py M1, thesis.py M2)
    cli.py               ingest [src|--all] [--day] [--refetch] · build · evaluate · export · check · approve
  data/observations/<source>.jsonl  data/status_events.jsonl  data/proposed_status_events.jsonl  data/fetchlog.jsonl
  ingest/cache/<source>/<YYYY-MM-DD>/<sha8(url)>.<ext> + .meta.json          gitignored
  web/                   Next 16 + TS + Tailwind + Recharts; web/data/*.json committed; web/public/data/<series>.csv
  tests/  tests/fixtures/
```

Flow: `seed/*.yaml` + `data/*.jsonl` → `build` (DuckDB in memory; `observations` view = approved, non-superseded, + `subject`, `q`) → `evaluate` (metrics → Derived; bands/direction → proposed StatusEvents; staleness) → `export` (deterministic JSON, `sort_keys`, `generated_at` in its own file) → `next build`. **The web never computes a number.** Every exported number is `{value, unit, as_of, obs_ids[]}`.

### 3.1 Confabulation guard, in code
- `Observation` requires `url retrieved_at http_status content_hash tier audited_vs_reported extraction_method raw_snippet`; exactly one of `value_numeric`/`value_text`; `audited` only with tier 4; `llm_extract ⇒ pending`. Nullable `value_low`/`value_high` for CIs (METR, Epoch P5/P95).
- `Derived.input_observation_ids` min 1; `metrics.py` skips (with a warning) any formula whose `inputs` globs match no series — never fabricates.
- `Indicator.published ⇒ counterevidence non-empty AND ≥1 approved observation AND (≥2 distinct source_ids OR single source with tier ∈ {1,2,4}) for any status outside {emerging, not_yet_measurable}` — all in `check`.
- `cap_status_by_tier`: tier 7 evidence proposes at most `emerging`.
- Manual rows: `ingest manual` fetches each URL, stores status/hash/text, **asserts `raw_snippet` is a verbatim substring of the fetched text** (html→text via scrub; PDF via pdfplumber). Fail ⇒ row rejected. 403/paywalled ⇒ stored, `disputed`, unpublished.

### 3.2 Connectors in the slice
| connector | fetch | emits (`series_key = <source>.<subject>.<measure>.<grain>`) | tier / basis | fixture |
|---|---|---|---|---|
| `metr` | `benchmark_results_1_1.yaml` | `metr.<model>.horizon_50.pt`, `.horizon_80.pt` (minutes, CI in low/high); `disputed` when > 960 min ("beyond suite ceiling") | 1 / reported | 3-model yaml |
| `sec_xbrl` | companyfacts per entity with `cik` (NVDA AMD MSFT GOOGL AMZN META ORCL CRWV NBIS; CIKs from `sec.gov/files/company_tickers.json`, fetched once). `SEC_USER_AGENT` env | `Revenues`∥`RevenueFromContractWithCustomerExcludingAssessedTax`, `GrossProfit`, `CostOfRevenue`, `PaymentsToAcquirePropertyPlantAndEquipment`→`capex`, `RevenueRemainingPerformanceObligation`→`rpo`, `DepreciationDepletionAndAmortization`→`da`. Forms 10-K/10-Q, USD, dedupe (start,end) by latest `filed`; 80–100 d → `.q`, 350–380 d → `.fy`; `as_of=end`, `published=filed`. Q4 = FY − 9M as a **Derived** (M2, with margin stacking) | 4 / 10-K audited, 10-Q company_stated | `sec_nvda_companyfacts.json` (5 concepts) |
| `manual` | `seed/manual_observations.yaml` rows: series_key value unit as_of_date url raw_snippet tier basis dispute_text | as declared; snippet-in-page assertion; lands `pending` | per row | one html + one pdf fixture |
| `bls` | POST `api.bls.gov/publicAPI/v2/timeseries/data/` (v1 unkeyed is enough); ids under the source in `sources.yaml` (`PRS85006092`; TFP id verified day 4 — may be a table download) | `bls.<id>.q`/`.a` | 4 / reported | one API JSON |
| `epoch` | `ai_companies.zip` first (funding rounds, revenue reports); `ai_models.zip`, `ml_hardware.zip` when an indicator needs them. `zipfile` + `expect()` on member names/columns. Port column maps from `~/ai-value-chain/config/sources.yaml`. CC-BY attribution string on the source row, rendered on every Epoch chart | **per table**: funding 5/reported (Debt `Type` dropped); revenue 5/reported + `run_rate`; training compute 6/estimated; hardware 2; `Confidence` → basis only | 20-row CSV heads zipped in-memory |

Dropped from the slice: `fred` (no flagship indicator uses FRED; "St. Louis Fed" in the briefs is the BBD paper → manual row), `census_btos` XLSX (manual row now; automate in M1 after reading the file twice), Form D (M4), Artificial Analysis / OpenRouter (M2).

Base class rules: per-source try/except (one outage never blocks the run), `FetchLog.ok=false` + PR still opens with a failure section, exit non-zero at end; `expect_series` per source so renamed columns raise `LayoutChanged` instead of yielding zero mapped values; `urllib.robotparser` for html/pdf kinds; SEC ≤10 req/s.

## 4. Build sequence

### Day 1–2 — the spine (definition of done: one L2 page rendering live METR data)
1. Step 0 folder + repo + `CLAUDE.md`.
2. `schema.py`: Observation, Derived, Indicator, StatusEvent, FetchLog, Source, Bucket, Layer, Sublayer, Crosswalk (+ enums, `grade_from_tier`, guards). Entity/Membership/Evidence/Prediction/Bottleneck wait for their first consumer.
3. `metr` connector → JSONL store → `metrics.yaml` with `horizon_ratio_80_50` → `bands.py` → `evaluate` proposes a StatusEvent.
4. Seed: 5 buckets, 7 layers, 21 sub-layer names, 6 crosswalk rows, 1 source, 3 indicators (`metr_horizon_50`, `metr_horizon_80`, `horizon_ratio_80_50`) with bands + rationale + counterevidence.
5. `export` → `web/data/`. Next 16 app, `/indicators/[slug]` in the 9-section ai2027 shape (claim/definition → how we track → interpretation → evidence → status + reasoning → timeline → counterevidence → update history → confidence; related bottlenecks/indicators/predictions as empty-tolerant sections). `BandChart` with CI band, `TierBadge`, `ProvenanceLink`, `StatusChip`. Screenshot 390/1280.

### Day 3 — capture's first honest numbers
6. `sec_xbrl` for NVDA/ORCL/MSFT → `nvda_gross_margin` (direction evaluator, `P1` §7 #1) and `rpo_backlog`. `direction.py`.
7. `manual` connector + 6 rows (BBD work-hours-assisted, Stanford DEL WTA, NANDA 5%, METR RCT −19%, BTOS cell, Menlo $37B) each with the `v2` §8 dispute text where it applies. `check` with the two-source rule and the StatusEvent-consistency rule.

### Days 4–7 — width + the two L0s
8. `bls` (productivity, TFP), `epoch` `ai_companies` (run-rates, rounds → `ai_native_run_rates`, `lab_recoupment_ratio`). Add indicators only as their source lands; target ≥1 real number per bucket or the valve renders "unmeasured".
9. Routes: `/` diffusion L0 (`StockFlowDiagram`: hand SVG, **vertical layout for 390px**, valves coloured by status, leak → `/capture`, last three StatusEvents, "what would change our mind"), `/capture` L0 (layer list with live cards; margin-bulge vertical is M2), `/buckets/[id]`, `/layers/[id]`, `/data/[series]` (L3 table + CSV), `/crosswalk`, `/sources` (health from FetchLog + staleness `now − last as_of > 2×cadence` → "stale as of"), `/methodology` (tiers, grade derivation, vocabularies, rubric, discipline rules, Epoch + Joy Larkin credits, a private value-chain map conflict disclosure), `/changelog` (from `status_events.jsonl`).
10. Two accent colours for status, icon + text always, never red/green. Epoch attribution footer on every chart using it.

### Slice 3 — CI + nightly
`ci.yml`: ruff, pytest, `check`, `next build`. `nightly.yml`: `ingest --all → build → evaluate → check → export`, commit `data/*.jsonl` + `web/data/*.json` on a branch, open PR with `data/summary.md` (readable diff) and failure section; upload `ingest/cache` as artifact. Repo setting "Allow GitHub Actions to create and approve pull requests". Vercel root `web/`.

### Then, `v2` M-order, one connector at a time
M1: Canaries/Revelio/CAIT/Yale + Anthropic EI, BTOS XLSX automation, `fits.py` (exp/hyperbolic/Ord), concordance → M2: segment data (SEC Financial Statement & Notes datasets — companyfacts has no segments), `margin_stack_share_by_layer`, Q4-fill Derived, `capex_to_revenue_stack`, `StackVertical` sized by margin share, HHI, Ramp/Menlo/Clouded Judgment, circular-deals ledger, AA + OpenRouter, `thesis.py` → M3: `predictions.yaml` (`nk` rows from `predictions.json` verbatim; `lab`/`ai2027`/`capture` rows each need a fetch), `bottlenecks.yaml` (regex over `bottlenecks.md`; stage from `##` headers; `stage × mechanism` grid from `BOTTLENECK_PROMPT.md`), `/predictions`, `/compare`, `/bottlenecks`, `/stack`; **public** → M4: Form D venture flows, continual-learning ladder + watchlist, `VentureFlowStrip` → M5: query service on Fly, citation post-check, chat drawer, weekly memo PR → M6: X route, a11y, enrichment via Explorium/Swarm/Clay in the PR flow. Paid tier stays behind `PAID_SOURCES=true` stubs.

## 5. Open questions — defaults taken (override any)

| # | Question | Default |
|---|---|---|
| 1 | Name/domain | `ai-tracker` working name; naming pass later via the naming skill |
| 2 | Repo visibility | Private now; public after M3 |
| 3 | Paid data | None; Form D + reporting only |
| 4 | X access | Manual URL drop until M6 |
| 5 | Hosting | Vercel (web) + Fly (M5 query service) |
| 6 | Community evidence | Editors only |
| 7 | AI 2027 columns on `/compare` | Yes, M3 |
| 8 | Default landing lens | Diffusion; capture one toggle away |
| 9 | a private value-chain map in sub-layer 17 | Listed, conflict disclosed on `/methodology` |
| 10 | Beehiiv push of the memo | Not until the memo exists (M5) |
| 11 | Missing research reports | Alex exports from the claude.ai chats into `docs/research/`; build proceeds without them |

## 6. Verification

- `uv run pytest` (15 tests, Appendix B): schema guards; band + direction tables; margin-stack hand-computed (M2); metric refuses missing input; each connector's `extract()` on its fixture; `LayoutChanged` on empty payload and missing column; scrub removes an injected line and logs it; manual snippet-in-page assertion passes/fails; export determinism (build+export twice, byte-identical); every exported `value` has non-empty `obs_ids`; StatusEvent consistency.
- `uv run ai-tracker check`: publish rules from §3.1; status ≠ latest StatusEvent fails.
- Site: `pnpm build`, then `npx playwright screenshot` of `/`, `/capture`, one L1, one L2, one L3 at 390 and 1280; review before calling a slice done. Click-through: leak → `/capture`; every number on L0–L2 resolves to an L3 row; Epoch attribution visible; unmeasured valves show the glyph, not a status word.
- Nightly dry-run on a branch: PR opens with `summary.md`; a connector with `ok=false` shows in the failure section and the job exits non-zero.
- Slice DoD: day 2 = METR page live; day 3 = NVDA gross margin + RPO cards live; day 7 = ≥1 real number per bucket or "unmeasured".

---

## Appendix A — schema (field lists; `req` unless marked)

Enums: `Tier` 1–7 (IntEnum) · `Basis` audited|company_stated|reported|estimated · `ExtractionMethod` api|xbrl|scrape|pdf|llm_extract|manual · `ReviewStatus` pending|approved|rejected · `SourceKind` api|xbrl|formd|csv|rss|html|pdf|arxiv|x|manual · `Lens` diffusion|capture|both · `ProxyType` benchmark deployment product behaviour policy model_release market_structure price capital_flow welfare · `FlowStatus` consistent_with_normal|faster_than_normal|slower_than_normal|emerging|not_yet_measurable · `Direction` concentrating|dispersing|stable|unclear|emerging|not_yet_measurable · `LeadLag` · `PredStatus` confirmed|ahead|on_track|behind|emerging|not_yet_testable · `Relation` same_valve|input_to|leak_from|return_arrow · `Ledger` nk|lab|ai2027|capture.

- **Observation**: id series_key unit as_of_date published_date retrieved_at url content_hash http_status source_id tier audited_vs_reported extraction_method extractor_version raw_snippet; `value_numeric|value_text` (exactly one); opt `value_low value_high period_start entity_id run_rate_vs_booked gross_vs_net disputed dispute_text review_status(=approved) reviewer_id supersedes_id`. id = sha1(source, series_key, entity, as_of_date, period_start)[:16]; changed value ⇒ new row + `supersedes_id`.
- **Derived**: id metric value as_of_date input_observation_ids(min 1) formula_version computed_at; `dims: dict` (e.g. layer_id). id = sha1(metric|as_of|sorted dims)[:16].
- **Indicator**: id(slug) name definition why_it_matters proxy_types unit cadence_expected tracker_interpretation counterevidence; `series_keys[] metric`; diffusion address `bucket_id valve_measured normal_band fast_band falsifying_band band_rationale flow_status`; capture address `layer_id sublayer_id direction_rule direction leading_lagging`; `confidence(0–95) proposed_status override_note related_* published updated_at`. Validators: bucket_id or layer_id; published ⇒ counterevidence.
- **Band** lo|hi (≥1 bound). **DirectionRule** periods=4 dead_band higher_is rationale.
- **StatusEvent**: id target_type target_id old_status new_status old_conf new_conf reason evidence_ids author created_at.
- **FetchLog**: id source_id started_at finished_at ok http_status bytes items_found items_new error scrubbed[].
- **Source**: id name org url kind default_tier cadence lens connector license attribution robots_ok expect_series[] people[]. Health derived from FetchLog at export, never stored.
- **Bucket** id name order speed_limit stock valve · **Layer** id name order description dependency_tier · **Sublayer** id layer_id name order · **Crosswalk** bucket_id layer_id sublayer_id relation note shared_indicators[].
- Later: Entity (cik crunchbase_id pitchbook_id aliases verified), EntityMembership (is_primary from_date to_date), Evidence, Prediction (published ⇒ claim_url), Bottleneck (1..89 stage mechanism text source_codes).

`grade_from_tier(tier, basis, single_source)`: single_source or tier 7 → D; tier 1, or tier 4 with audited/reported → A; tier 2/3, tier 4 company_stated, tier 6 non-estimated → B; else C.

## Appendix B — evaluators and metrics

- `flow_status(value, normal, fast, falsifying, best_tier)`: None value/band → `not_yet_measurable`; in falsifying or fast → `faster_than_normal`; in normal → `consistent_with_normal`; far side of normal from fast → `slower_than_normal`; gap → `emerging`; then `cap_status_by_tier`. Compound thresholds (e.g. ratio ≤ 2 AND h80 > 8h) live in `thesis.py`, not bands.
- `direction(points, rule, best_tier)`: < periods+1 points → `not_yet_measurable`; |Δ| ≤ dead_band → `stable`; < half of step deltas share sign → `unclear`; else sign via `higher_is`; cap by tier.
- `metrics.yaml` entry: `description grain unit lead_lag formula_version inputs[] caveats sql`. SQL returns `as_of_date, value, obs_ids` (+ dims). Slice formula:
  ```sql
  -- horizon_ratio_80_50
  SELECT a.as_of_date, a.subject AS model, a.value_numeric / b.value_numeric AS value, [a.id, b.id] AS obs_ids
  FROM observations a JOIN observations b ON a.subject = b.subject AND a.as_of_date = b.as_of_date
  WHERE a.series_key LIKE 'metr.%.horizon_50.pt' AND b.series_key LIKE 'metr.%.horizon_80.pt'
  ```
  M2: `margin_stack_share_by_layer` (segment gross profit by layer via `entity_membership`, denominator obs_ids cited via `list_distinct(flatten(...)) OVER (PARTITION BY q)`), `capex_to_revenue_stack`, `sec_q4_fill`, `hhi_by_layer`.
- Export shapes (top-level keys): `lens/diffusion.json {as_of verdict buckets[] valves[] leak recent_status_events[] what_would_change[]}`; `lens/capture.json {as_of verdict layers[] …}`; `bucket|layer|sublayer/<id>.json {…, indicators[card]}` where `card = {id name flow_status direction leading_lagging confidence grade latest{value unit as_of obs_ids} sparkline[] stale_as_of}`; `indicator/<id>.json` (all fields + series[] derived[] evidence[] status_events[] crosswalk[]); `series/<key>.json`; `index.json sources.json changelog.json`.

## Appendix C — tests (slice)
1 schema guards · 2 bands table · 3 direction table · 4 metrics refuses missing input · 5 metr extract (two series/model, >960 disputed) · 6 sec extract (FY26 GM ≈ 0.711 from fixture, 10-K audited, 10-Q company_stated, restatement dedupe) · 7 manual snippet-in-page pass/fail · 8 bls period→date · 9 epoch extract (keys, Debt dropped, Confidence→basis, per-table tier) · 10 LayoutChanged on empty and on missing column; `run()` → ok=false · 11 scrub removes injected line, logs to FetchLog · 12 export determinism · 13 every exported value has obs_ids · 14 check: two-source rule · 15 check: status = latest StatusEvent.
