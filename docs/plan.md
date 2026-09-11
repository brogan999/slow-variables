# Slow Variables (working name ai-tracker) — build plan

## Context

Two briefs arrived on 9 Sep 2026:

- **AI Tracker Brief v2 — Technology Diffusion** (`v2`): the unified spec. One data store, one methodology, one indicator object, two L0 lenses (diffusion ⇄ capture), crosswalk as a first-class table. M0–M6, 7 weeks.
- **Value Capture Tracker Part 1** (`P1`): the earlier capture-side build prompt. Richer on 21 sub-layers with seed companies, ingestor endpoints, cleverhack directories, 13 seed indicators, circular-financing ledger, reference figures.

They describe the same product from two ends. `v2` is canonical; `P1` is the capture-lens appendix. The Notion page "Grand Theory of AI Development & Diffusion" frames the goal: *the business-relevant version of the AI 2027 tracker*, aimed at "which $1T companies exist in 2035".

Outcome: a repo at `~/ai-tracker` holding both briefs and the research corpus, shipping a **thin vertical slice first** (one connector → one indicator → one page, live data, day 2), then widening connector-by-connector in `v2`'s milestone order. Nothing publishes without a traceable observation.

### What already exists on disk (found by search)

| Brief asks for | Found | Path |
|---|---|---|
| 89-bottleneck list | ✅ complete, with 224-row raw JSON + extraction prompt | `~/normaltech-predictions/bottlenecks.md`, `bottlenecks_raw.json`, `BOTTLENECK_PROMPT.md` |
| N&K prediction material | ✅ 747 predictions with verbatim quote + URL + verified flag | `~/normaltech-predictions/predictions.json`, `normaltech-predictions.md`, `worldview-summary.md`, `corpus/` (70 posts) |
| 11-layer a private value-chain map value-chain map | ✅ | private a private value-chain map thesis notes (kept outside the public tree in `docs/private/`, gitignored) |
| Teece / Nordhaus / Perez / Ding notes | ✅ scattered | private thesis notes (`docs/private/`, gitignored); `docs/interpretation/technological-revolutions-perez.md`; Ding in `bottlenecks.md` §Theoretical foundations |
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
                worldview-summary.md
  docs/interpretation/technological-revolutions-perez.md   (copies; write nothing new)
  docs/private/            private business notes, gitignored
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

---
---

# Part 2 — Finish line: everything through M6, then public (planned 11 Sep 2026)

## Context

M0–M3 are shipped (`f979c26`): 12 connectors, 34 indicators (30 published), scored prediction ledger, thesis monitor, circular ledger, compare and bottleneck pages. Alex's bar for going public is **the whole brief, through M6**, not "complete enough". Three read-only audits (brief-vs-shipped gap list, site quality, ops) found: the nightly can never run unattended today (default branch is `master`, Actions cannot open PRs, the manual connector fails once every row is verified, nothing approves after merge, so statuses freeze); the site lacks metadata/robots/sitemap, has contrast and mobile failures, dead anchors, placeholder copy; and the brief still names ~50 indicators, ~20 free sources, six components, three routes, the query layer, the memo, the X route and enrichment. Decisions taken with Alex: scope = through M6; naming pass now (canon process, Alex locks); Alex registers an Artificial Analysis key and an Anthropic key with a spend cap; repo goes public with the site. Everything below supersedes §4's sequencing from M3 onward. `docs/plan.md` in the repo gets this Part 2 appended.

## Definition of done (all must hold before the switch is flipped)

1. Every route and component in brief v2 §4.3–4.4 exists (`/stack`, `/stack/[id]`, `/query`, `/memos`, `DirectionChart`, `MarginStackChart`, `ConfidenceDial`, `LadderView`, `VentureFlowStrip`, `ChatDrawer`, `QueryConsole`); `/admin` and `/data` remain the plan's deliberate substitutions (PR queue; `/series`).
2. Every indicator in Appendix A/C and P1 §7 is either published with a status and counterevidence, or `published: false` with a rendered reason ("not measurable from free sources: …"). Every free source in §5 either has a connector, a manual row with verbatim snippet, or a one-line reason.
3. The nightly has run unattended for seven consecutive nights (green or PARTIAL with a real cause), and one merged nightly PR has moved a status through `approve` without a human writing a reason.
4. Twelve golden questions pass through the query service with correct citations; the citation post-check has tests; one weekly memo PR has been produced by the memo job and merged.
5. Site: every page has its own title, robots/sitemap/OG present, 375px scroll-width clean on all pages, AA contrast, focus styles, no milestone language, sources render attribution, licences and cite/corrections on `/methodology`.
6. Name locked ≥80/100 on the canon checklist, domain live on Vercel, wordmark renamed; repo scrubbed (a private value-chain map docs and personal paths out) and public; deployment protection set to previews only.

## Sequencing — five phases, each leaves `main` deployable

Estimates are agent-hours of build; Alex's time is marked. Total ≈ 150 h build + Alex ≈ 12 h.

### Phase 0 — unattended operation (≈ 8 h) — first, because every later phase depends on a running nightly
1. **GitHub settings** (Alex or `gh`): default branch → `main` (`gh api -X PATCH repos/brogan999/ai-tracker -f default_branch=main`, delete `master`, a strict ancestor); enable "Allow GitHub Actions to create and approve pull requests" (`actions/permissions/workflow can_approve_pull_request_reviews=true`).
2. **Connector may be empty**: `Connector.may_be_empty: bool = False` in `src/ai_tracker/ingest/base.py`; `run()` raises `LayoutChanged` on zero rows only when false; `manual.py` sets true. Test: `ingest manual` → `ok=True found=0`.
3. **Nightly rewrite** (`.github/workflows/nightly.yml`): `ingest --all || failed=true` → `approve` → `build && evaluate && export` → `check || check_failed=true` → `actions/cache` on `ingest/cache` keyed by date → `create-pull-request` with `if: always()`, fixed branch `nightly`, title prefixes `PARTIAL`/`CHECK FAILED`, `add-paths` + `docs/thesis.md` → exit 1 if either flag. Design: approve runs **inside** the nightly so the PR shows what merge will commit; merge remains the gate. `CLAUDE.md` bullet 5 and README updated to say so.
4. **Evaluator reasons** (`cli.py`): `_auto_reason(ind, value, as_of, new, source)` writes a machine reason only for a first scoring or an unscored→scored move inside a band (quotes value, source, date, band edge, band rationale); band-crossing changes keep a blank reason for a human. **Prediction pass**: `window_start > today` → propose `not_yet_testable`; `window_end < today` with status ∉ {confirmed, ahead, behind} → propose `behind`; `target_type="prediction"`. First live trigger: `openai_research_intern_sep_2026` on 1 Oct.
5. **check hardening** (`cli.check_errors(store)` split out for tests): published indicator with `stale_as_of` and not `Indicator.stale_ok` (new field, requires `stale_reason`) → error; blank-reason proposal older than 14 days → error; every `StatusEvent.evidence_ids` must exist (fix the one dangling id on `aei_augmentation_share`).
6. **thesis.py**: `Data.series` drops rows older than the source cadence rule (same `CADENCE_DAYS` test as `_card`); `rents_migrate_up` first condition says "waiting on a lab/app margin series"; `normal_tech_strengthened` says "untestable until the continual-learning ladder series exists" (Phase 2 lands it).
7. **Tests**: `test_fred.py` (fixture exists), `test_census_btos.py` (extract split to `_from_sheets`), `test_sec_segments.py` (minimal inline-XBRL fixture), `test_check.py` (one assertion per rule via monkeypatched `st.OBS`/`st.DATA`).
8. **Dry run**: `gh workflow run nightly.yml --ref main`; inspect the `nightly` PR (summary body, `docs/thesis.md` diff, auto-reasons, `meta.json`), merge, confirm the next night's PR commits the reasoned proposals to `data/status_events.jsonl`.
Verify: `uv run pytest`, `uv run ai-tracker check`, seven nights of `gh run list --workflow nightly.yml`.

### Phase 1 — site launch quality (≈ 20 h)
9. **Metadata**: `web/src/lib/site.ts` (`SITE = {name, url, description}`, the single rename point); `layout.tsx` `metadataBase`, title template, openGraph/twitter; `generateMetadata` in `indicators/[slug]`, `buckets/[id]`, `layers/[id]`, `series/[key]`; `app/robots.ts`, `app/sitemap.ts` (~574 URLs from `index()` + `seriesKeys()`), `app/opengraph-image.tsx`, new favicon, delete `public/*.svg`, `not-found.tsx`, `error.tsx`. Read `web/node_modules/next/dist/docs/…/01-metadata/` first (Next 16).
10. **Mobile + a11y**: `globals.css` `--muted #6f6e68`, `--slow #b84a1c` (light), `:focus-visible` ring, skip link; nav `overflow-x-auto` strip under `md`; `StackVertical` one column under `sm`, drop `whitespace-nowrap`; `StockFlowDiagram` fontSize 15/14, replace `role="img"` with `<title>`+`aria-labelledby` (it wraps links); `Grade` sr-only text; series link text "source page"; `th scope="col"` everywhere; layer names as headings; dispute text visible; derived-rows table wrapped.
11. **Edge states**: unpublished indicators show "unpublished" text and no detail page (`generateStaticParams` filters); `Provenance.Num` renders plain text on an obsIndex miss; `predictions` `<li id>` (fixes all `/compare` anchors); text-only series column header; feed licences; `/changelog` grouped by month in `<details>`; `/bottlenecks` families in `<details>`; `store._source_health` adds `health: ok|stale|never` from cadence, `/sources` badge and attribution column (CC BY); empty-layer note on `/capture`; `Freshness` footer with UTC time and a >3-day warning.
12. **Copy + methodology**: remove milestone language (`page.tsx:29`, `capture/page.tsx:18`, `layers/[id]/page.tsx:28`, `sources/page.tsx:8`, `methodology/page.tsx:29`, `indicators/[slug]/page.tsx:56,:103`); methodology gains tier table with enum names, band rubric (`band_input`, PR-only changes), leading/coincident/lagging, "tier-5 run-rate never audited", cadence line, Reuse/cite/corrections with licences; credit line generated from `sources()`; a private value-chain map disclosure repeated on `/layers/deployment_application`.
13. **Vercel**: `next.config.ts` `headers()` (X-Content-Type-Options, Referrer-Policy, basic CSP, CSV cache); pin `recharts`; document root directory (`web/`, `.vercel` linked at both levels, gitignored).
Verify: `npx playwright screenshot --viewport-size=375,800` on every route + 1280; `document.scrollWidth === 375`; `pnpm build`; sitemap count.

### Phase 2 — M4 data and surfaces (≈ 87 h, 13 PRs; order 14→15→16→17, 18→19, others any time, 23 with the key)
14. **Evidence records**: observations with `series_key = evidence.<target_id>.<for|against|context>.pt`, `value_text` summary, verbatim snippet via the manual connector (same trick as the ledger); export into `indicators/<id>.json.evidence[]` and `predictions.json[].evidence[]`; `check` accepts ≥1 `against` row as counterevidence; safety-brake rows (Astra critical-cyber 3 Sep 2026, 20 Jul incident + RL pause, GPU reallocation, Pachocki) target `safety_brake_events`; RSI rows target `rsi_agent_workdays_per_human` and `nk_rsi_external_limits`. openai.com rows via the Internet Archive URL pattern already in use.
15. **Entities + `/stack`**: P1 §4.2 seed companies into `seed/entities.yaml` with dated memberships (`from_date`/`to_date`; Scale→Meta 2025-06, OpenRouter→Stripe 2026-08) and CIKs for private filers (Mercor 0002103986, X.AI 0002079267, Baseten 0001865393, Harvey 0001974654 verified); `entity_membership` DuckDB table in `store.py`; `stack.json` export; `/stack` and `/stack/[id]` pages; sub-layer chips in `StackVertical` and layer pages link there; nav entry.
16. **Form D connector** (`formd`): parse the data-sets index page for every `*_d.zip` (prefix changed in 2026q2, never hard-code), TSVs `ISSUERS`/`OFFERING`; EFTS `search-index?q="<alias>"&forms=D&dateRange=custom` for the current quarter, `primary_doc.xml` per hit; map issuers by CIK first, then exact normalised alias (never substring: "surge" hits surgery centres, "Anthropic" hits SPVs); drop pooled funds; series `formd.<entity>.amount_sold_usd.pt`, `.offering_amount_usd.pt`, `.debt_sold_usd.pt`; tier 4 company_stated; D/A supersedes; `candidates` CLI prints unmapped issuers for a human to add CIKs. Fixture: six-row TSVs zipped in memory + one XML.
17. **Venture metrics + strip**: `venture_rounds` CTE (best-tier source per entity-quarter across Form D, Epoch rounds, `aifunding` connector `/api/v1/rounds`), `venture_dollars`, `round_count`, `median_round_size`, `stage_mix`, `top3_concentration`, `venture_capital_intensity`, `frontier_share_of_venture_dollars`, `post_money_to_arr_multiple`, `lab_vertical_integration_events_4q` (acquisition ledger rows), `founding_to_100m_arr_quarters`; indicators P1 #8, #9, #11, #12, #13 (`not_yet_measurable` until 8 quarters); `web/data/venture/<sublayer>.json`; `VentureFlowStrip` (stacked by source tier, equity/debt toggle) on `/layers/[id]` and `/stack/[id]`.
18. **Epoch tables**: `epoch_models` (`ai_models.zip`: training compute, power), `epoch_hardware` (`ml_hardware.zip`: price-performance), `epoch_prices` (chart CSVs: lowest price at fixed capability); `fits.loglinear(decay=True)`; metrics `training_compute_doubling_days`, `training_power_doubling_days`, `perf_per_dollar_doubling_days`, `inference_price_halving_days`; indicators `epoch_training_compute_growth` (normal ≥300 d, fast ≤182 d), `epoch_training_power_growth`, `perf_per_dollar_growth`, `epoch_inference_price_fixed_capability` (halving normal ≥230 d, fast ≤110 d), `epoch_data_exhaustion_year` (manual row; normal ≥2028, fast ≤2026).
19. **Epoch benchmarks + chips**: `epoch_bench` (`benchmark_data.zip`: ECI with accessibility group, ARC-AGI-2, CL-bench), `epoch_chips` (`ai_chip_sales.zip`); metrics `open_vs_closed_gap` (months for a closed ECI score to be matched by open), `arc_agi_frontier`, `custom_silicon_share` (non-Nvidia H100e share); indicators for each (open gap normal ≥9 mo, fast ≤3 mo; ARC normal <0.5, fast ≥0.85).
20. **Continual-learning ladder**: manual rows `cl_ladder.<entity>.rung.pt` (verbatim from lab posts: Trajectory weekly LoRA → 3, Harvey+Engram → 4, Cursor Tab → 2) and research rows; `feeds` connector gains `kind: html` page-watch rows (emit on content-hash change) for feedless blogs plus DeepMind RSS and arXiv Atom queries; metric `continual_learning_level` (max production rung); indicator (normal ≤3, fast ≥5, tier 7 → emerging); `lens/ladder.json`; `LadderView` on `/buckets/return_arrow` and `/layers/training_input`; `thesis.normal_tech_strengthened` reads the metric.
21. **Regulatory/physical**: `fda_devices` (media/178541 CSV, 1,614 rows), `ncsl` (2025 table; 2026 URL when it exists, scrape → pending), Waymo and MultiState manual rows; indicators `fda_ai_devices_cumulative` (y/y), `state_ai_bills_introduced`, `waymo_weekly_paid_rides`, `safety_brake_events` (trailing-12-month count from evidence rows); metric `ord_half_life_minutes` (constant-hazard misfit from h50/h80) and indicator.
22. **Bucket 2–4 manual indicators + second sources**: `call_center_uplift`, `exec_reported_impact`, `harvey_lab_frontier_completion`, `pass_hat_k_tau_bench`, `surprise_index`, `bbd_adult_use`/`bbd_work_use_weekly`/`bbd_work_use_daily` (series exist), `aei_occupation_depth_25`, `openai_work_share`, `exposure_vs_usage_gap`, `yale_occupational_mix_dissimilarity`, `humlum_precise_null`, `upwork_freelancer_effects`, `pwc_ai_skill_wage_premium`, `expert_data_market_run_rate`, `rl_environment_vendor_count` (`rl_list` JSON), `internal_external_deployment_gap_months`; publish `lab_run_rates` (add `cnbc`/`yahoo_finance` series keys → two sources), `lab_recoupment_ratio`, `canaries_exposed_employment_yoy` (Canaries paper PDF row). Each manual row: fetched URL, verbatim snippet, tier, counterevidence.
23. **Artificial Analysis + OpenRouter rankings** (needs `ARTIFICIAL_ANALYSIS_API_KEY` from Alex; connector reports `ok=false` cleanly if unset): `aa.<model>.intelligence_index.pt`, `.price_blended_usd_per_mtok.pt`, change-point ledger like `openrouter.py`; `openrouter_rankings` scrapes the dehydrated JSON in `/rankings` (token share by model, weekly, `scrape` → pending); `hhi_by_layer` gains a token-share slice; price-per-capability gets the AA axis alongside the METR axis.
24. **Capture cross-layer**: `capex_to_revenue_stack` (hyperscaler capex ÷ lab run-rates + enterprise spend, grade C), `enterprise_multi_homing_share` (Menlo), `depreciation_useful_life_changes` (useful-life facts via `sec_segments.py` members), `neocloud_debt_terms` (CoreWeave 10-Q rates), `startup_share_of_app_revenue`, `valuation_multiple_by_layer`; `published: false` with rendered reasons for `lab_gross_margin`, `compute_share_of_spend`, `app_gross_margin_net_of_inference`, `gpu_rental_price_per_hour`, `secondary_marks_between_rounds`, `revenue_per_employee_exposed_sectors`, `fda_first_llm_device`, `reliability_framework_adoption`, `agent_calibration`, `agent_operational_safety`, `deployment_data_share_of_training`.
25. **Components**: `DirectionChart` (last N+1 points, dead-band ribbon, replaces `BandChart` when `direction_rule`), `MarginStackChart` (from new `lens/capture.json.margin_stack_series`; unmeasured layers hatched), `ConfidenceDial` (SVG arc with rubric bands) on indicator page and card.
26. **Directories + stubs**: `owid` (two grapher CSVs), `rl_list`, cleverhack candidate file (entity seeding only; robots allows), bottleneck `domain` axis from `bottlenecks_raw.json` (there is no mechanism field; grid becomes family × domain), `paid.py` with eight stub classes gated on `PAID_SOURCES=true` (test asserts a clear error), methodology credits regenerated.
Verify per PR: fixture extract test, `check`, `export`, screenshot of the touched page at 375/1280.

### Phase 3 — M5/M6 services (≈ 34 h)
27. **Semantic views + citation check**: `Store` gains DuckDB tables `derived`, `status_events`, `indicators`, `metrics`; `src/ai_tracker/query/citecheck.py` (`check(text, records)`: number extraction incl. `$172B`, `6.3%`, `6.34×`, `3.1 h`, ranges; unit normalisation mirroring `format.ts`; match against cited observation/derived values, low/high, band edges, or verbatim snippet; uncited numbers fail; `annotate()` wraps failures); `tests/test_citecheck.py`; `seed/golden.yaml` (12 questions, six per lens, expected records by series/metric, plus one refusal case); `seed/analyses.yaml` + `analyses.json` export.
28. **Query service** (`src/ai_tracker/query/server.py`, `ask.py`): stdlib `ThreadingHTTPServer` on Fly (`ai-tracker-query`, staging app first), boots `Store` from the image (`Dockerfile`, `fly.toml`, `.github/workflows/deploy-query.yml` on push to main touching data/seed/semantic/src); bearer `QUERY_TOKEN`; `/sql` read-only with row cap and 5 s interrupt; `/ask` = claude-sonnet-5 tool loop (tools `sql`, `metric`, `indicator`, `changes_since`; frozen cached system prompt with methodology + metric descriptions; every number must carry `[obs:]`/`[derived:]`; post-check with one revise turn, else `blocked`); `/golden`; `/health`; in-memory daily spend ledger with `QUERY_DAILY_USD_CAP` (default $5, ~100 questions) → 429; logs hash the question. New dependency `anthropic`. CLI `ai-tracker ask|golden`. Amend Part 1 §2 Web row: one route handler is allowed.
29. **Drawer + console**: `web/src/app/api/ask/route.ts` (POST proxy holding the token, 20 s timeout, 503 `offline`); `ChatDrawer` on native `<dialog>`, scope from pathname, citations → `/series/<key>#<id>` links, honest offline/blocked/429 copy; `/query` page renders saved analyses and a SQL console. Vercel env `QUERY_URL`, `QUERY_TOKEN`.
30. **Weekly memo**: `src/ai_tracker/memo.py` assembles deterministic facts (status events since last memo, new observations by indicator, staleness, watchlist posts, thesis changes, opposing crosswalk moves), asks claude-fable-5-1 for prose under the §6.2 prompt with hard citation rules, runs `citecheck`, falls back to the deterministic digest when the key or check fails; writes `docs/memos/YYYY-MM-DD.md` (front matter with thesis snapshot) and `web/data/memos/*.json`; `.github/workflows/memo.yml` Mondays 09:17 UTC → PR; merge = approval; `/memos`, `/memos/[date]`, home headline. Secret `ANTHROPIC_API_KEY`.
31. **X route**: `x_list` connector (X API v2 `lists/{id}/tweets`, `X_BEARER_TOKEN`; the curated List's membership is the handle verification), `watch.x.<author>.pt` tier 7, linked tier 1–6 artifacts listed in `summary.md` with a manual-row stub; `seed/x_drop.yaml` fallback via the oEmbed endpoint; fix `append_observations` supersede key to include `url` for `watch.*`. **Checkpoint for Alex**: buy X API Basic or stay on the drop file (default: drop file).
32. **Enrichment**: `enrich.py` at the end of `evaluate` proposes `entities.yaml` lines for unresolved names using free EDGAR lookups only; "Suggested enrichment" section in `summary.md`; Explorium/Swarm/Clay stay in Alex's Claude session.
33. **A11y final + docs**: `<dialog>` semantics, `aria-live` answer region, `aria-current` nav, `prefers-reduced-motion`, axe run at 375/1280; methodology sections for the query layer, memo policy, X policy; README.

### Phase 4 — name, scrub, public (Alex ≈ 8 h, build ≈ 3 h)
34. **Naming pass** per the naming canon (private) Part XI: foundation lock, divergent longlist, harness sentence + competitor test to ~15, screening record (DNS/SERP/handles/TM/linguistic) to 3–5, one-page brand world each, Alex locks at ≥80/100. Output `AI-TRACKER-NAMING.md` in the private naming folder (outside the repo). Alex buys the domain; Vercel Domains apex + www. Rename = `site.ts`, wordmark, `web/package.json` name, README.
35. **Repo scrub** (checkpoint with Alex before the flip): move the private business notes (and any others he names) to a gitignored `docs/private/` and rewrite history for those paths; remove `web/AGENTS.md`/`web/CLAUDE.md` scaffolds; strip personal paths from `docs/plan.md`, `docs/research/BOTTLENECK_PROMPT.md`; add `LICENSE` (MIT), `LICENSE-DATA` (CC BY 4.0 compilation, upstream terms govern rows), `CONTRIBUTING.md`; `.env` stays untracked.
36. **Flip**: `gh repo edit --visibility public`; Vercel Deployment Protection → "Only Preview Deployments"; confirm the domain resolves, sitemap fetches, `/api/ask` answers a golden question, nightly PR previews stay gated.

## Checkpoints that need Alex
- Before Phase 2 PR 23: paste `ARTIFICIAL_ANALYSIS_API_KEY` into `.env` and `gh secret set`.
- Before Phase 3 PR 28: `ANTHROPIC_API_KEY` with a monthly cap in the Anthropic console; `fly secrets set` on the staging app; `FLY_API_TOKEN` repo secret.
- Phase 3 PR 31: X API purchase or not.
- Phase 4: pick the name, buy the domain, confirm the private-docs list, approve the visibility flip.

## Verification (end to end)
- `uv run pytest -q` (target ≥ 60 tests), `uv run ruff check src tests`, `uv run ai-tracker check` clean, `uv run ai-tracker golden` 12/12.
- Seven nightly runs in `gh run list --workflow nightly.yml`; one status moved via a merged nightly PR.
- `pnpm build` prerenders every page; `curl /sitemap.xml | grep -c "<url>"` ≈ page count; `npx playwright screenshot` at 375 and 1280 for every route with scroll-width check; axe clean.
- Staging Fly app: `/health`, golden via drawer on a Vercel preview, `QUERY_DAILY_USD_CAP=0.01` → 429, machine stopped → drawer says offline.
- Memo `workflow_dispatch` opens a PR; with the key removed the fallback digest PR opens.
- Public: domain resolves over HTTPS, headers present, repo visible, previews gated.

## Status against the definition of done (10 Sep 2026, end of day)

| # | Criterion | State |
|---|---|---|
| 1 | Routes and components in brief v2 §4.3–4.4 | Done: `/stack`, `/stack/[id]`, `/query`, `/memos`, `DirectionChart`, `MarginStackChart`, `ConfidenceDial`, `LadderView`, `VentureFlowStrip`, `ChatDrawer`, `QueryConsole`. `/admin` and `/data` remain the PR-queue and `/series` substitutions. |
| 2 | Every indicator published with status + counterevidence, or unpublished with a rendered reason | Done for 87 indicators (68 published): the Yale workbook connector, the OpenRouter rankings scrape, the CoreWeave/Nebius debt rows, the 10-K useful-life rows, the Menlo multi-model rows and a fifteen-deal acquisition ledger all landed; the Artificial Analysis connector is built and optional until the key exists. |
| 3 | Seven consecutive unattended nightlies; one merged nightly PR moving a status without a human reason | In progress: two green nightlies (PR #2 merged, the 10 Sep dispatch after the robots.txt and private-filer fixes); the streak needs the calendar. Auto-reasons are in place. |
| 4 | Twelve golden questions pass; citecheck tested; one memo PR produced and merged | citecheck tested (7 tests); memo job dispatched (branch `memo`). Golden run waits for `ANTHROPIC_API_KEY` on the Fly app. |
| 5 | Site metadata, 375px, AA contrast, focus, no milestone language, attribution and licences | Done; axe-core clean on twenty routes at 375 and 1280. |
| 6 | Name locked ≥80, domain live, wordmark renamed; repo scrubbed and public; previews-only protection | Done except the domain form: name locked **Slow Variables** (94); wordmark, site URL and licence renamed; history rewritten into `brogan999/slow-variables` (public, ruleset, push protection, Dependabot), old repo archived; Vercel re-linked, team slug `alexbrogan`, protection standard (custom domain public, previews gated). slowvariables.com was already registered, so the domain is slowvariables.ai; Alex completes Vercel's registrant form, then nameservers switch automatically. |

Checkpoints still with Alex: complete `vercel domains buy slowvariables.ai` (registrant contact form), `ANTHROPIC_API_KEY` (Fly secret + repo secret on brogan999/slow-variables + `.env`), `ARTIFICIAL_ANALYSIS_API_KEY` (repo secret + `.env`). X stays on the drop file.

## Redesign status (10 Sep 2026)

Part 4 shipped on the `redesign` branch and merged: editorial-instrument tokens with a dark toggle, Instrument Serif / Sans / JetBrains Mono, shadcn (Base UI) button, sheet, input, textarea, toggle-group, Magic UI number-ticker, a dependency-free More menu, the new home (hero with both lens verdicts and live figures, diagram, stack, this week's memo, thesis monitor), the indicator rail and filterable index, editorial memos, rethemed charts, OG image with the serif. Verified: `tsc`, `eslint`, `pnpm build`, axe-core with zero violations and no horizontal overflow on 23 routes at 375 and 1280 in both themes, a staff review whose findings were applied (ticker animation, stale links, sheet width, toggle pressed state, focus ring duplication, OG font claims, shared JS from the dropdown).
