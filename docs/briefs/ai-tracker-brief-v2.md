# Build brief v2: one tracker, two lenses

Working name: `ai-tracker` (rename later). This supersedes `normal-tech-tracker-brief.md`. Read end to end before writing code. Where it says "verify", fetch before hard-coding.

Two research threads feed this build and must be treated as one product:

- **Thread D (diffusion).** Narayanan & Kapoor's "AI as Normal Technology": five buckets (methods, products, early adoption, adaptation, return arrow), valves between them, normal/fast bands, falsification thresholds. Source docs: `AI-as-Normal-Technology Diffusion Tracker v2` report; the 89-item bottleneck list (`bottlenecks.pdf`, `bottlenecks_raw.json`).
- **Thread C (capture).** Value capture across the AI stack — who keeps the surplus — measured layer by layer (semis → cloud → labs → apps → adopters → labour/consumers) with margin stacking, capex-to-revenue, price-per-token pass-through, HHI, open-vs-closed gap, consumer surplus, circular financing, and venture flows into ~21 sub-layers. Source docs: `Measuring AI Value Capture: An Inputs and Outputs Map` report; the venture-sources research output; the 11-layer a private value-chain map value-chain map, the five-tier dependency graph, and the bottleneck-migration model (enter on lab procurement, exit on lab vertical integration).

Put all of these under `docs/research/` in the repo on day one. They are the seed corpus for the metric definitions, the sub-layer taxonomy, and the query layer's retrieval index.

---

## 0. Why one product

The two threads are the same question asked from two ends. Diffusion asks *how fast* value moves through the stages; capture asks *who keeps it* at each stage. The stock-and-flow diagram in Thread D has a "leak" — surplus exiting the chain — and that leak *is* Thread C. The return arrow in Thread D (deployment → invention) *is* Thread C's training-input layer (human data, RL environments, RLaaS, evals) plus the continual-learning companies. Thread C's "lab recoupment" and "capex-to-revenue" are the financial view of the same valve that Thread D calls "dependence on diffusion."

So: **one data store, one methodology, one indicator object, one query layer, one UI spine — and two L0 screens ("lenses") that arrange the same indicators differently.** Every indicator carries both a diffusion address (bucket, valve) and a capture address (layer, sub-layer) where applicable, and the crosswalk in §3 is a first-class table, not a footnote.

Design principle inherited from Thread C: *the same object rendered at four zoom levels, not four different products.* Sub-layer venture tracking, continual-learning progress, and BLS productivity are all just indicator families.

---

## 1. Methodology (canonical, applies to both lenses)

Fetch and read https://ai2027-tracker.com/methodology/ first. Implement these as schema constraints and CI checks, not as prose.

### 1.1 Three-layer separation (the confabulation guard)

`Observation` (raw, sourced, dated) → `Derived` (formula over observations, defined in the semantic layer) → `Indicator` (the tracker object: proxies, status, confidence, evidence log, counterevidence). No derived number may exist without a traceable path to observation IDs. Thread C's first research pass caught confabulated model names and run-rates in the wild; the store must make that class of error impossible to publish.

### 1.2 Evidence tiers (canonical enum on every observation and evidence record)

1. `benchmark_or_independent_eval`
2. `model_release_details` (system cards, technical reports)
3. `public_product_behaviour`
4. `official_filing_or_policy` (SEC filings incl. XBRL, Form D, 8-K; enacted law; regulator lists)
5. `credible_reporting` (Reuters, Bloomberg, FT, WSJ, The Information)
6. `published_analysis` (papers, think tanks, VC reports, credible blogs with transparent method)
7. `statement_from_actor` (lab leaders, founders, officials — intentions, not outcomes)

Thread C used letter grades. Keep them as a **derived display label**, never as stored truth: `A` = tier 4 audited filing or tier 1; `B` = tier 2, 3, or tier 6 with transparent method and disclosed data; `C` = tier 5 or tier 6 without data; `D` = tier 7 or single-source. Rule enforced in code: tier-7 evidence never moves a status above `emerging`; a tier-5 run-rate never counts as `audited`.

### 1.3 Observation flags

`audited_vs_reported` ∈ {audited, company_stated, reported, estimated}; `run_rate_vs_booked`; `gross_vs_net`; `disputed` with text. These render on every surface where the number appears.

### 1.4 Proxy types

`benchmark`, `deployment`, `product`, `behaviour`, `policy`, `model_release`, plus Thread C's `market_structure` (margins, HHI, multiples), `price` (price-per-unit-capability), `capital_flow` (capex, venture rounds, contracts), `welfare` (consumer surplus, wages).

### 1.5 Status vocabularies

- Flow indicators (Thread D): `consistent_with_normal` / `faster_than_normal` / `slower_than_normal` / `emerging` / `not_yet_measurable`, each with `normal_band`, `fast_band`, optional `falsifying_band`.
- Capture indicators (Thread C): `direction` ∈ {concentrating, dispersing, stable, unclear} plus `leading_lagging` ∈ {leading, coincident, lagging}, with the same `emerging` / `not_yet_measurable` escape hatches.
- Predictions (both threads, one ledger): `confirmed` / `ahead` / `on_track` / `behind` / `emerging` / `not_yet_testable`; direction, magnitude, timing assessed separately.

### 1.6 Discipline (CI-enforced)

No single-source status change unless unambiguous (release, enactment, filed document). Every evidence record dated with a URL that resolved at ingestion (store status and content hash). Non-empty `counterevidence` before publish. Status and confidence (0–95) are separate fields. Every status change is a `StatusEvent` with reason, evidence IDs, author; the changelog is generated from these and cannot be hand-edited. Observations are never deleted, only superseded. `tracker_interpretation` is its own field so readers can disagree with the reading and keep the evidence.

Confidence rubric: 90–95 multiple strong independent sources; 70–89 good evidence, some ambiguity; 50–69 mixed or hard to operationalise; <50 limited or vague.

---

## 2. Data model

Store: **DuckDB + Parquet in the repo, snapshotted per pull** (Thread C's call; it makes every historical state reproducible and diffable). No database server until it hurts. Seed definitions as versioned YAML. The whole store must rebuild from `seed/` + `ingest/cache/`.

```
Source        id, name, org, url, kind ('api'|'xbrl'|'formd'|'csv'|'rss'|'html'|'pdf'|'arxiv'|'x'|'manual'),
              default_tier, cadence, connector, last_success_at, last_error, people[]  -- "why respected"

Entity        id, name, kind ('company'|'lab'|'agency'|'person'|'university'), cik, crunchbase_id,
              pitchbook_id, aliases[], founded, hq, notes
EntityMembership  entity_id, layer_id, sublayer_id, from_date, to_date   -- many-to-many with dates
                  (Scale: human-data, then partly Meta; Baseten: serving, then continual-learning infra)

Observation   id, indicator_id?, entity_id?, series_key, value_numeric, value_text, unit,
              as_of_date, published_date, retrieved_at, url, content_hash, http_status,
              source_id, tier, audited_vs_reported, run_rate_vs_booked, gross_vs_net,
              extraction_method ('api'|'xbrl'|'scrape'|'pdf'|'llm_extract'|'manual'),
              extractor_version, raw_snippet, disputed, dispute_text,
              review_status ('pending'|'approved'|'rejected'), reviewer_id, supersedes_id

Derived       id, semantic_metric_name, value, as_of_date, input_observation_ids[], formula_version

Evidence      id, target_type ('indicator'|'prediction'), target_id, source_id, tier, date, url,
              summary, for_or_against ('for'|'against'|'context'), raw_snippet, retrieved_at, hash

Indicator     id, slug, name, definition, why_it_matters, proxy_types[], unit, cadence_expected,
              -- diffusion address (nullable)
              bucket_id, valve_measured, normal_band, fast_band, falsifying_band, flow_status,
              -- capture address (nullable)
              layer_id, sublayer_id, direction, leading_lagging,
              -- shared
              confidence, tracker_interpretation, counterevidence (required), related_bottlenecks[],
              related_indicators[], related_predictions[], published, updated_at

Crosswalk     bucket_id, layer_id/sublayer_id, relation ('same_valve'|'input_to'|'leak_from'|'return_arrow'), note

Prediction    id, ledger ('nk'|'lab'|'ai2027'|'capture'), claimant_entity_id, claim_text (verbatim),
              claim_url, claim_date, window_start, window_end, operationalisation, proxy_types[],
              status, confidence, direction/magnitude/timing assessments, counterevidence

StatusEvent   id, target_type, target_id, old_status, new_status, old_conf, new_conf, reason,
              evidence_ids[], author, created_at
FetchLog      id, source_id, started_at, finished_at, ok, http_status, bytes, items_found, items_new, error
Bottleneck    id (1..89), stage, mechanism, text, source_codes[]
Layer / Sublayer   the stack taxonomy (Appendix D), with the 11-layer map and dependency tiers as attributes
Bucket        the five diffusion buckets with speed limits, stock and valve descriptions
```

**Semantic layer** (`semantic/metrics.yaml`, dbt-style): every derived metric has `name, description, formula, inputs (series_keys), grain, unit, caveats`. The UI and the query layer read metrics through this layer, never by improvised joins. Examples: `margin_stack_share_by_layer`, `capex_to_revenue_stack`, `price_per_eci_point`, `hhi_by_layer`, `lab_recoupment_ratio`, `horizon_ratio_80_50`, `cross_tracker_concordance`, `venture_capital_intensity_by_sublayer`, `surprise_index`.

**Entity resolution** is the unglamorous hard part and is shared by both lenses: one entity table keyed to CIK for public companies and Crunchbase/PitchBook IDs for private ones, alias handling, dated sub-layer membership. Explorium (Vibe Prospecting), Swarm and Clay are already connected and can enrich entities; use them in the review flow, not as autonomous writers.

---

## 3. The crosswalk (first-class, seeded, displayed)

| Diffusion bucket | Capture layers / sub-layers | Relation | Shared indicators (same observations, two addresses) |
|---|---|---|---|
| 1 Methods | Model layer (frontier labs, neolabs, open-weight/Chinese labs); Compute layer (semis, neoclouds, DC/power) as inputs | `same_valve` / `input_to` | METR horizons; Epoch compute growth; inference price at fixed capability ⇄ price-per-token pass-through; open-weights lag ⇄ open-vs-closed gap; lab run-rates; safety-brake events |
| 2 Products | Serving & orchestration (inference serving, routing/gateways, agent infra); Application layer (coding agents, vertical AI, consumer) | `same_valve` | Uplift RCTs; pilot→production; Harvey LAB completion; app-layer gross margin net of inference ("model tax"); AI-native ARR; enterprise spend by layer (Menlo) |
| 3 Early adoption | Enterprise adopters; consumers | `same_valve` | BTOS; Bick–Blandin–Deming; Ramp AI Index; Anthropic Economic Index; multi-homing share (OpenRouter, Menlo) |
| 4 Adaptation | Enterprise adopters; labour & consumers (welfare); Deployment/FDE services (sub-layer 17) | `same_valve` / `leak_from` | BLS productivity/TFP; Canaries/Revelio/CAIT/Yale; consumer surplus (Brynjolfsson–Collis WTA, GDP-B); wage effects; revenue-per-employee in exposed sectors; FDA/Waymo/legislation |
| 5 Return arrow | Training-input layer (human data, RL environments, RLaaS/post-training, synthetic data, data licensing, evals); continual-learning infra (Trajectory, Baseten, Fireworks, Engram) | `return_arrow` | Expert-data market run-rates ⇄ sub-layer 8 revenue; RSI disclosures; continual-learning ladder ⇄ sub-layer 10 venture flow and lab-procurement signal; lab recoupment ⇄ capex-to-revenue and valuation multiples; enterprise session-training policies |
| Leak (surplus exits the chain) | Cross-layer capture: margin stacking, HHI, consumer surplus, circular financing | `leak_from` | Nvidia/TSMC margins; hyperscaler capex and depreciation-life changes; RPO/backlog; circular-deal ledger; consumer surplus vs US GenAI revenue |

The two earlier discussions in Thread D ("who has typically profited most in this chain": Teece complementary assets, Nordhaus 2.2%, Perez installation/deployment; Ding diffusion capacity) are the interpretive spine for the leak column. Store them as `docs/interpretation/` and index them for the query layer.

---

## 4. UI: one spine, two lenses, four-plus depths

### 4.1 Principles

Progressive disclosure. Same indicator object at every zoom. Build for skeptics: counterevidence as prominent as evidence; disputed flags loud. Two accent colours for status; no red/green good/bad (fast ≠ good; concentrating ≠ good). Dates on everything (`as of`, `retrieved`). No number without a provenance link. Mobile-first for L0/L1.

### 4.2 Depths

- **L0 — two thesis screens, one toggle.**
  - *Diffusion lens:* the stock-and-flow diagram — five stocks, four valves coloured by status, the return loop, B1 (backlash/safety brake), B2 (goalpost moves), and the leak. One sentence verdict: "As of {date}: capability fast, products slow, adoption broad-but-shallow, adaptation at trend, return arrow emerging. Thesis: holding."
  - *Capture lens:* the stack as a single vertical — layer bars sized by gross profit share (margin bulge), arrows for capital-flow direction, sub-layer venture-flow ticks, one sentence per layer. "Who keeps it: semis, then consumers; labs commoditising; apps fragile."
  - Both show the last three status changes and "what would change our mind". Clicking the leak on the diffusion diagram lands on the capture lens; clicking the training-input layer on the capture stack lands on the return-arrow bucket.
- **L1 — bucket or layer page.** Indicator cards: latest value, sparkline, status chip (flow status or direction), leading/lagging tag, confidence, `as of`, one line on which valve or which capture question it answers. Bucket pages list the paper's speed limits; layer pages list sub-layers with venture flow and the lab-procurement / lab-vertical-integration signals.
- **L2 — indicator page** (ai2027-tracker shape): definition; how we track this (proxies, sources, cadence); band chart or direction chart; observations table; counterevidence drawer; interpretation; status history; confidence rationale; related bottlenecks; related indicators across the crosswalk; related predictions.
- **L3 — evidence and data.** Every observation and evidence record with full provenance; raw series download; grade badge derived from tier; a "query this" box that opens the chat drawer pre-scoped to the series.
- **L4 — query console** (§6) and saved analyses.

### 4.3 Cross-cutting

- **Persistent chat drawer** scoped to whatever is on screen. Its job is synthesis across indicators ("which leading indicators moved this quarter and what does that imply for lab margins in 2027"), every claim linked to an observation ID.
- **Weekly "what changed" memo** as the default entry point. Most readers will read this and never touch L2. Generated by the digest job (§6.2), approved by a human, published with its evidence links.
- `/predictions` (one ledger, four claimant families), `/compare` (Normal Technology vs AI 2027 vs lab timelines vs capture theses, same evidence), `/bottlenecks` (89 items on the stage × mechanism grid, linked to indicators), `/stack` (the sub-layer taxonomy with entities and membership dates), `/sources`, `/methodology`, `/changelog`, `/data`, `/admin`.

### 4.4 Components

`StockFlowDiagram`, `StackVertical`, `BandChart`, `DirectionChart`, `MarginStackChart` (stacked bar by layer per quarter), `IndicatorCard`, `StatusChip`, `ConfidenceDial`, `TierBadge`, `ProvenanceLink`, `CounterevidenceDrawer`, `ChangelogList`, `PredictionCard`, `LadderView` (continual-learning rungs), `VentureFlowStrip` (rounds and $ by sub-layer over time), `ChatDrawer`, `QueryConsole`, `ReviewQueue`.

---

## 5. Ingestion

### 5.1 Principles

One connector per source in `ingest/connectors/<source>.py`, exposing `fetch() -> list[RawItem]` and `extract(raw) -> list[Observation | Evidence]`. Idempotent; raw responses cached under `ingest/cache/<source>/<date>/` so extraction re-runs without refetching. Declared cadence and a health flag per source, shown on `/sources`.

Preference order: official API / XBRL → structured file the source publishes → RSS → HTML → PDF → LLM extraction from unstructured text → manual. LLM-extracted values land as `pending` and require human approval; store prompt version and model string. Scheduling via GitHub Actions cron (daily / weekly / release-date). Each run opens a PR with new observations and a diff summary; merging publishes. Respect robots.txt and ToS. Do not scrape X directly (§5.4). A source layout change must fail loudly (open an issue with the diff), never return zero items silently.

### 5.2 Tiers of effort (from Thread C)

- **Free and structured first:** SEC EDGAR — XBRL frames API (segment revenue, capex, RPO, depreciation useful-life notes), 8-K feeds, **Form D** (the only primary source for private raises; EDGAR full-text search + Form D XML data sets); Epoch CSVs (notable models, companies revenue reports, hardware, inference prices); Artificial Analysis; OpenRouter rankings; METR; BLS API; Census BTOS XLSX; St. Louis Fed; FDA device list XLSX; California Policy Lab CAIT downloads.
- **Scrape-with-consent second:** Ramp AI Index pages, Menlo PDFs, Clouded Judgment, Stanford/ADP Canaries posts, Revelio tracker, Yale Budget Lab, company research blogs (Baseten, Trajectory, Harvey, Anthropic, OpenAI). Exa (connected) is the tool for this tier.
- **Paid last:** PitchBook/Crunchbase APIs, SemiAnalysis models, The Information. Stub the connectors; wire when budget is approved.

### 5.3 Review queue

Admin page listing pending observations: indicator, proposed value, source snippet, previous value, proposed status change, approve/reject/edit. Rejections need a reason. Approvals write `StatusEvent` if status changed. Entity-enrichment suggestions (Explorium/Swarm/Clay) appear here too.

### 5.4 X / Twitter

Not scraped. In order of preference: X API v2 with a curated List (verify current tier pricing and rate limits); Exa restricted to `x.com` and thread mirrors for named accounts; weekly manual pass dropping URLs into the queue. All X content is tier 7 unless it links to a tier 1–6 artifact, in which case ingest the artifact. Tweets never move a status.

### 5.5 Source registry

The full per-bucket registry from the diffusion brief is unchanged and lives in `seed/sources.yaml`; the capture sources from Thread C's inputs table (Epoch hubs, SemiAnalysis, Artificial Analysis, OpenRouter, Ramp, Menlo, a16z, Sequoia/Cahn, Bain, Goldman/JPM/Citi/Barclays, Clouded Judgment, The Information, Sacra, Bloomberg circular-deals map, public filings, Stanford DEL GDP-B/WTA, Anthropic Economic Index, St. Louis Fed, NANDA) and the venture-flow sources (EDGAR Form D, PitchBook, Crunchbase, CB Insights, Tracxn, Dealroom, Carta/Peter Walker, Bessemer, ICONIQ, Air Street, NVCA/PitchBook Venture Monitor, OECD.AI, secondary marks from Forge/EquityZen/Caplight/Notice, China trackers) merge into the same file with `lens: [diffusion|capture|both]`. Shared sources (Epoch, METR, BTOS, BLS, Anthropic EI, Ramp, Menlo, St. Louis Fed, Stanford DEL) are fetched once and serve both lenses.

**Continual-learning watchlist** (return arrow; shared with capture sub-layers 9–10 and 14): Baseten Research (post-monolith essay Feb 2026; rank-1 LoRA continuous-merge Oct 2025; STILL KV compaction; Trajectory pipeline post May 2026; live draft-model training Jun 2026 — Charles O'Neill, Mudith Jayasekara, Matthew Blau, Aaron Ellis-Bloor); Trajectory (Ronak Malde, Arjun Karanam, Michael Elabd; $15M seed May 2026 Conviction, $40M Series A Aug 2026 Sequoia; customers Clay, Decagon, Harvey, Mercor, Rogo; SDPO extended to off-policy traces; Decagon retrained weekly); Harvey (LAB, LAB: Contracts, LAB: Firm Knowledge; Baseten post May 2026; Tenet Aug 2026 — Niko Grupen, Gabe Pereyra, Spencer Poff); Engram; Fireworks; Applied Compute; Thinking Machines (on-policy distillation, Tinker); Cursor (Tab online learning); DeepMind nested learning; arXiv weekly queries ("continual learning", "test-time training", "on-policy distillation", "learning on the job", "deployment feedback", "parametric memory", "catastrophic forgetting").

---

## 6. Query layer and digest

### 6.1 Architecture

Tools exposed to the model: `sql(query)` over read-only DuckDB views **of the semantic layer** (raw tables only via an explicit `raw=true` flag that the UI does not expose); `search_evidence(text, filters)` over evidence, observation snippets, and `docs/research` + `docs/interpretation` (BM25 + embeddings); `fit_trend(metric, since, model)`; `band_status(indicator)`; `changes_since(date)`; `concordance(indicator_ids)`; `crosswalk(indicator)`; `entity(name)`.

Models via the Anthropic API: `claude-sonnet-5` for extraction and routine queries; `claude-fable-5-1` (or `claude-opus-5`) for synthesis. Log model string and prompt version with every answer.

Every number in an answer must be cited as `obs:<id>` or `ev:<id>` and rendered as a link to L3. A post-check extracts numbers from the answer and verifies each appears in a cited record; failing answers are blocked and the model is asked to revise. Read-only: the query layer cannot write observations or statuses.

Saved analyses materialised nightly: doubling-time and half-life fits; margin-stack shares by layer per quarter; HHI by layer; capex-to-revenue; recoupment ratios; cross-tracker concordance; venture capital intensity by sub-layer; surprise index; falsification monitor.

### 6.2 Weekly memo (agentic, human-approved)

Scheduled job prompt: "Given observations and evidence added since {last_memo}, which indicators changed status or would under the band/direction rules? Which crosswalk pairs moved in opposite directions? Draft the memo, the L0 sentences for both lenses, and the changelog entries." Output is a draft PR into the review queue. Nothing publishes without approval.

---

## 7. Analytics

Band evaluation → proposed flow status (pure, unit-tested). Direction evaluation for capture indicators (trend over N periods with a dead-band). Exponential and hyperbolic fits with CIs and AIC comparison; Ord constant-hazard half-life. Margin stacking from XBRL (gross profit by layer / stack total, with the lab layer from Epoch estimates flagged as tier 6). HHI from share data by layer. Capex-to-revenue for the stack (hyperscaler + lab capex over AI revenue, semis excluded to avoid double count). Recoupment ratio with definitional caveats. Venture flow: $ and round count by sub-layer per quarter, normalised by sub-layer revenue; top-3 concentration; lead/lag of venture flow vs sub-layer revenue in quarters. Cross-tracker concordance for adaptation (Canaries, Revelio, CAIT, Yale). Surprise index. Falsification monitor (Appendix B) nightly, with a human-readable explanation of which conditions hold.

---

## 8. Governance

Data and status changes are PRs; ingestion opens them, humans merge. Status-change PRs include evidence IDs (≥2 sources unless unambiguous), reason, counterevidence considered, new confidence. Changelog generated from `StatusEvent`. Observations superseded, never deleted. Disputed figures (NANDA 95%; METR −19%; lab run-rates; Oracle $300B contract; PwC productivity claims; OpenAI's self-assessed RSI milestone) carry their dispute text everywhere they appear. Bands and formulas live in YAML with a `rationale` string; changing them is a reviewed PR.

---

## 9. Stack and repo

Python 3.12 for ingest/analysis (`httpx`, `pydantic`, `duckdb`, `polars`, `feedparser`, `arxiv`, `pdfplumber`, `beautifulsoup4`, `sec-edgar` tooling of your choice, Anthropic SDK; `mypy --strict`, `pytest`, `ruff`). DuckDB + Parquet snapshots. Next.js (App Router) + TypeScript + Tailwind; Recharts or D3 for band/stacked charts; nightly static export of public pages; dynamic query console. GitHub Actions cron; PR-based publishing; Vercel or Fly.

```
ai-tracker/
  CLAUDE.md
  README.md
  docs/
    research/          # both research reports, bottleneck list, venture-sources output, value-chain map
    interpretation/    # Teece/Nordhaus/Perez/Ding notes; the "who profits" discussion; Meadows framing
    methodology.md  sources.md  bands.md  changelog.md (generated)
  seed/
    buckets.yaml  layers.yaml  sublayers.yaml  entities.yaml  crosswalk.yaml
    indicators/diffusion.yaml  indicators/capture.yaml
    predictions.yaml  sources.yaml  bottlenecks.yaml
  semantic/metrics.yaml
  schema/               # pydantic models; JSON schema exported for web
  ingest/  connectors/  extract/ (versioned prompts + validators)  cache/ (gitignored)  run.py
  analysis/
  query/                # DuckDB views over semantic layer, tools, agent, citation post-check
  web/                  # Next.js; lenses/diffusion, lenses/capture share components
  ops/                  # GitHub Actions
  tests/
```

---

## 10. CLAUDE.md (repo root)

- Never write a status directly; propose via `StatusEvent` in a PR.
- Never hard-code a URL you have not fetched in this session; fetch, then store with `retrieved_at`.
- Every observation needs `as_of_date`, `published_date`, `retrieved_at`, `url`, `tier`, `audited_vs_reported`, `extraction_method`, `raw_snippet`.
- LLM-extracted values are `pending` until reviewed; do not approve your own extraction.
- Tier 7 never moves a status above `emerging`; tier 5 never becomes `audited`.
- Derived numbers must resolve to observation IDs through the semantic layer; if a formula needs an input that isn't an observation, the formula is wrong.
- Every indicator has at least one address (bucket or layer); shared ones have both and a `Crosswalk` row.
- Entity writes go through the entity table; no free-text company names in observations.
- Prompts live in versioned files. Prefer structured file over HTML over PDF over LLM extraction. Fail loudly on layout changes. Bands and formulas change only via reviewed PR.

---

## 11. Build plan

- **M0 (week 1) — shared core.** Schema, semantic layer skeleton, entity table with the sub-layer taxonomy seeded (Appendix D), crosswalk seeded, ingestion framework, review queue. Connectors for the sources both lenses need: SEC EDGAR XBRL + 8-K + Form D; Epoch (models, companies revenue, inference price, hardware); METR; Census BTOS; BLS; St. Louis Fed; Artificial Analysis; OpenRouter. Band and direction evaluators.
- **M1 (week 2) — diffusion lens.** Buckets and diffusion indicators (Appendix A); stock-and-flow L0; L1/L2/L3 pages; the four monthly labour trackers (Stanford/ADP, Revelio, CAIT, Yale) and Anthropic EI / OpenAI usage; concordance.
- **M2 (week 3) — capture lens.** Layers and capture indicators (Appendix C); margin stacking, capex-to-revenue, HHI, price-per-token pass-through from M0 sources; stack vertical L0; Ramp, Menlo, Clouded Judgment, Bloomberg circular-deals connectors; consumer-surplus series.
- **M3 (week 4) — predictions and compare.** One ledger, four claimant families (Appendix B); `/compare`; safety-brake and RSI evidence records; bottleneck grid page.
- **M4 (week 5) — return arrow and venture flows.** Continual-learning ladder and watchlist connectors; expert-data market and recoupment cards; Form D–based venture flow by sub-layer with PitchBook/Crunchbase stubs; lab-procurement and vertical-integration signals; `VentureFlowStrip`.
- **M5 (week 6) — query layer and memo.** Semantic-layer views, tools, citation post-check, chat drawer, weekly memo job producing draft PRs.
- **M6 (week 7) — X, sources page, hardening.** Curated X route; `/sources` with fetch health; accessibility; nightly export; connector-failure monitoring; entity-enrichment flow via Explorium/Swarm/Clay.

Private after M1; public after M3.

---

## 12. Acceptance criteria

Every published indicator has ≥1 approved observation, non-empty counterevidence, bands or direction rules with rationale, and a status consistent with the evaluator or an explicit override note. Every number on L0–L2 links to an L3 record. Every derived metric resolves to observation IDs. `pytest` covers: band and direction evaluators; trend fits on synthetic series; tier guards; the citation post-check (rejects an uncited number); connector parsers against fixtures; XBRL segment extraction against a known 10-K; Form D parsing against a known filing; margin-stack and HHI formulas against hand-computed values. Layout changes fail loudly. Store rebuilds byte-for-byte from `seed/` + cache. Query console passes twelve golden questions (six per lens) with correct citations. The crosswalk renders both directions.

---

## 13. Open questions for Alex

1. Name and domain (use the naming skill for a real pass).
2. X access route and budget.
3. Paid data: PitchBook or Crunchbase API budget, or Form D + reporting only for the first release?
4. Public after M3, or hold until venture flows are in?
5. Community-submitted evidence with review, or editors only?
6. Default query model (cost vs depth).
7. Do the AI 2027 columns ship on `/compare` at launch?
8. Which of the two L0 lenses is the default landing page? (Recommendation: diffusion, with the capture lens one toggle away — the diffusion diagram is the better twenty-second explanation and its leak is the door into capture.)

---

## Appendix A — Diffusion indicators (seed; bands and latest values as of 9 Sept 2026; re-verify on first fetch)

**Bucket 1 — Methods**
- `metr_horizon_50` — hours; ~12h (Opus 4.6), ≥16h (Mythos). n: doubling ≥7mo; f: ≤4mo. `faster_than_normal`, 80. Counter: suite saturates >16h.
- `metr_horizon_80` — ~70min (Opus 4.6), ~3h (Mythos). `faster_than_normal` but lagging.
- `horizon_ratio_80_50` — ~7–10× (was ~5×). n: ≥5×; f: →2×; x: ≤2× with 80% >8h. Gap widening (pro-normal), 70.
- `ord_half_life_minutes` — constant-hazard fit; report alongside.
- `epoch_training_compute_growth` — 4–5×/yr. `faster_than_normal`, 85. `epoch_training_power_growth` — 2.2×/yr.
- `epoch_inference_price_fixed_capability` — ~40×/yr (GPQA-Diamond @ GPT-4 level), 9–900× range. `faster_than_normal`, 80. *Shared with capture: price pass-through.*
- `epoch_data_exhaustion_year` — ~2028 (2026–2032). 55.
- `open_weights_lag_months` — *shared with capture: open-vs-closed gap.*
- `pass_hat_k_tau_bench` — collapse with k persists. `consistent_with_normal`, 80.
- `reliability_framework_adoption` — `emerging`. `agent_calibration`, `agent_operational_safety` — `not_yet_measurable`.
- `continual_learning_level` — ladder L0–L6 (Appendix E). Latest L3 production, L4 emerging. n: L0–L3; f: L5–L6. 80.
- `rsi_agent_workdays_per_human` — 3.1 (OpenAI, mid-Aug 2026; self-reported, tier 2/7). `emerging`, 65.
- `rsi_intervention_rate_4_8h` — >50% (pro-normal).
- `surprise_index` — AI Futures self-grade ~65% of predicted pace. 60. `arc_agi_frontier` — `emerging`.

**Bucket 2 — Products**
- `dev_rct_uplift` — −19% (METR early-2025); Feb 2026 redesign, weak evidence of speed-up now. n: ≤~20%, setting-dependent; f: >40% broad. `consistent_with_normal`, 70.
- `call_center_uplift` — +14%, novices.
- `enterprise_pilot_to_production` — NANDA ~5% material value vs Menlo ~47% reach production (different denominators; disputed). n: ≤10%; f: >30%. 60.
- `exec_reported_impact` — Yotzov et al. 2026: >90% no employment impact, 89% no productivity impact over 3 yrs. 75.
- `harvey_lab_frontier_completion` — <10% end-to-end (May 2026).
- `ai_native_run_rates` — OpenAI >$40B (Aug 2026), Anthropic ~$65B (Jul 2026); `run_rate_vs_booked` flagged. *Shared with capture: lab layer revenue.*

**Bucket 3 — Early adoption**
- `bbd_adult_use` ~40%; `bbd_work_use_weekly` 23–28%; `bbd_work_use_daily` 9–11%; **`bbd_work_hours_assisted` 1–5%** (headline intensive-margin metric; n: single digits; f: >20%; 80). Note Thread C's later St. Louis Fed figures (62% adults / 45% workers, May 2026) — reconcile waves and instruments on ingest; store both with instrument tags.
- `btos_firm_use` ~20% (May 2026), ~32% employment-weighted; series break Nov 2025. 70. `ramp_business_adoption` — *shared with capture.*
- `aei_augmentation_share` ~55/42 (Mar 2026). `aei_occupation_depth_25` ~49%. `openai_work_share` 27%.
- `exposure_vs_usage_gap` — usage ~20–30% of 70–90% theoretical. 60. `exposed_low_adaptive_workers` 3.3M (Manning & Aguirre).

**Bucket 4 — Adaptation**
- `canaries_exposed_employment_yoy` — −0.2% high vs +0.6% low exposure (to Apr/Jun 2026). n: ±1%; x: sustained broad AI-attributable decline. 80.
- `canaries_entry_level_gap` — 19% (Aug 2026); hiring not separations. 70. Counter: pre-ChatGPT timing (NY Fed; Iscenko & Millet).
- `revelio_exposed_vs_unexposed_growth` — ~4% less; adopters +27% headcount. 70. `cait_high_exposure_claims_3mma` — +~1% m/m (Jul 2026). 70. `yale_occupational_mix_dissimilarity` — slightly above norm, predates AI. 80.
- `cross_tracker_concordance` — derived; x: ≥3 trackers concurrent AI-attributable break.
- `bls_labor_productivity_yoy` — +2.2% (Q2 2026); cycle 2.1% = long-run. 80. `bls_tfp_private_nonfarm` — +0.8% (2025); n: Acemoglu ≤0.66%/decade; f: Goldman-scale.
- `new_grad_unemployment` 5.6%; exposed vs unexposed +0.77 vs +0.85pp (SIEPR). `humlum_precise_null` <2%. `upwork_freelancer_effects` −2% jobs / −5.2% earnings. `pwc_ai_skill_wage_premium` 62% (verify vs PDF).
- `fda_ai_devices_cumulative` ~1,524 (Mar 2026); `fda_first_llm_device` UpDoc K253281 (Dec 2025, verify). `waymo_weekly_paid_rides` 500k (Mar 2026). `state_ai_bills_introduced` 1,561/45 states (Mar 2026); 85 laws H1 2026.
- `safety_brake_events` — Astra critical-cyber (3 Sept 2026); 20 Jul incident + RL pause; 7 Aug −59.2% Astra GPU allocation; voluntary-slowdown statements.
- `consumer_surplus_wta` — $116B → $172B (Brynjolfsson–Collis, Jul 2025 → Mar 2026). *Shared with capture: the leak.*

**Bucket 5 — Return arrow**
- `continual_learning_level` and `cl_*` observables (Appendix E).
- `expert_data_market_run_rate` — Mercor >$2B gross (Jun 2026; ~35% take; >90% from labs); Surge ~$1.2B (2024); Scale guided ~$1B; Handshake ~$1B. `faster_than_normal` as input, 75. *Shared with capture: sub-layer 8.*
- `lab_recoupment_ratio` — run-rate ÷ cumulative capital; large caveat; 60. *Shared with capture.*
- `deployment_data_share_of_training` — `not_yet_measurable`. `rl_environment_vendor_count` — manual quarterly. `internal_external_deployment_gap_months` — Mythos Feb→Jun 2026 (Dwarkesh), single datum, 50.

## Appendix B — Prediction ledger and thesis rules

Ledgers: `nk` (Narayanan & Kapoor), `lab` (OpenAI, Anthropic), `ai2027`, `capture` (Sequoia $600B question; Bain $2T revenue needed by 2030; Covello "too much spend"; Cahn; Amodei "trillions before 2030").

Seed statuses as of 9 Sept 2026: OpenAI intern by Sept 2026 — `confirmed` by self-assessment only, 40. OpenAI automated researcher by Mar 2028 — `not_yet_testable`, 70. Amodei SWE end-to-end 6–12 months from Jan 2026 — `on_track`/`emerging`, 55. Amodei "country of geniuses" 1–2 years from Jun 2026 — `emerging`, 45. Amodei trillions before 2030 — `emerging`, 40. Anthropic ~10×/yr — `on_track`, 70. AI 2027 horizon doubling ≤4mo — `ahead`, 80. N&K adoption at human speed — `on_track`/`confirmed`, 80. N&K safety speed limits bind — `confirmed`, 75. N&K RSI can't escape external bottlenecks — `on_track`, 70. N&K benchmarks don't predict products — `on_track`, 70. N&K AGI not a milestone — `not_yet_testable`. AI 2027 superhuman coder on schedule — `behind`/`emerging`, 55. Continual learning unsolved, no benchmark — `confirmed`, 80. Bain: $2T new revenue needed by 2030 — `emerging`. Cahn $600B→$840B question — `on_track` as a gap measure.

Thesis rules (nightly):
- Normal-technology FALSIFIED if (`horizon_ratio_80_50` ≤ 2 AND `metr_horizon_80` > 8h) AND (`cross_tracker_concordance` shows ≥3 trackers with a concurrent AI-attributable break beyond entry level) AND (`bbd_work_hours_assisted` > 20% OR `bls_tfp_private_nonfarm` sustained > trend + 1pp for ≥4 quarters).
- STRENGTHENED if `horizon_ratio_80_50` non-decreasing AND `continual_learning_level` ≤ L4 AND precise nulls persist through the next four monthly tracker releases.
- Invention-side WARNING if an independently verified RSI series shows agent-workdays/human-workday > 1 with `rsi_intervention_rate_4_8h` < 50% (tests bottleneck #86).
- Capture thesis "rents migrate up the stack" SUPPORTED if `margin_stack_share_by_layer` for labs+apps rises ≥5pp over four quarters while semis' share falls; CONTRADICTED if Nvidia's share holds and app-layer margins net of inference fall.
- Capture thesis "consumers keep most of the surplus" holds while `consumer_surplus_wta` > US GenAI revenue.

## Appendix C — Capture indicators (seed; from Thread C's outputs table)

Cross-layer: `margin_stack_share_by_layer` (derived, quarterly, from XBRL + Epoch lab estimates; **gap #1** in Thread C); `capex_to_revenue_stack` (Bain ~$500B capex vs ~$2T revenue needed by 2030; Cahn); `price_per_token_fixed_capability` (shared); `valuation_multiple_by_layer` (tier 5; expected-rent proxy); `hhi_by_layer` (derived; **gap #2**); `open_vs_closed_gap` (HAI: 8% → 1.7%; shared); `enterprise_multi_homing_share` (Menlo, Ramp, OpenRouter).

Semis: Nvidia GAAP gross margin 71.1% FY26 (Q4 75.0%), revenue $215.9B, Data Center $193.7B (8-K, 25 Feb 2026); Nvidia DC $75.2B vs AMD ~$5.8B (Apr-2026 quarter); `perf_per_dollar_growth` +49%/yr (Epoch); `custom_silicon_share` (leading indicator of Nvidia rent decay).

Cloud: `gpu_rental_price_per_hour` (SemiAnalysis; paywalled); `rpo_backlog` (Oracle ~$455B Q1 FY26; Microsoft >$600B AI RPO, ~45% OpenAI per IDC); `depreciation_useful_life_changes` (**gap #3**; from 10-Ks); `neocloud_debt_terms`.

Labs: `lab_run_rate` (shared; tier 5, `run_rate_vs_booked`); `lab_gross_margin` (reported 40–60%); `compute_share_of_spend` (Epoch: 57–70%); `lab_recoupment_ratio` (shared).

Apps: `app_gross_margin_net_of_inference` ("model tax"; **gap #4**; construct from Ramp token spend + reported ARR + SemiAnalysis unit costs); `enterprise_spend_by_layer` (Menlo $37B 2025, $19B apps); `startup_share_of_app_revenue` (63%).

Adopters: `ramp_business_adoption` (>50% in 2026); `revenue_per_employee_exposed_sectors`; `exec_reported_impact` (shared).

Labour/consumers: `consumer_surplus_wta` (shared; **gap #5** — no high-frequency series; recommend commissioning a quarterly WTA panel); wage/employment series (shared with bucket 4).

Circular financing: `circular_deal_ledger` (**gap #6**; rows typed as LOI / equity / binding take-or-pay, each linked to filing or PR: Nvidia–OpenAI $30B equity closed ~31 Mar 2026 + up-to-$105B Ohio guarantee, 17 Aug 2026 filing; AMD–OpenAI warrant, 6 Oct 2025; CoreWeave–Nvidia $6.3B backstop, 8-K Sept 2025; Oracle–OpenAI ~$300B reported only; OpenAI commitments ~$1.4T stated vs ~$600B reset); `nvidia_5y_cds_bps` (record ~82bps, 27 Jul 2026) as a stress barometer.

Venture flows (per sub-layer, quarterly): `venture_dollars`, `round_count`, `median_round_size`, `stage_mix`, `post_money_to_arr_multiple`, `venture_capital_intensity` ($ raised / sub-layer revenue), `top3_concentration`, `lab_procurement_signal`, `lab_vertical_integration_signal` (the August heuristic: enter on lab procurement, exit on lab vertical integration), `secondary_marks_between_rounds`, `founding_to_100m_arr_quarters`, `venture_lead_lag_vs_revenue_quarters`.

## Appendix D — Stack taxonomy (seed for `layers.yaml` / `sublayers.yaml`)

Layers: compute & physical; model; training input; serving & orchestration; deployment & application; adopters; labour & consumers.

Sub-layers (from Thread C; extend with the 11-layer map and the dependency tiers as attributes): 1 semis & AI chip startups; 2 neoclouds & GPU clouds; 3 data-centre developers & power; 4 memory/HBM, networking, photonics, cooling; 5 frontier labs; 6 neolabs; 7 open-weight & Chinese labs; 8 human/expert data & labelling; 9 RL environments, simulators, verifiers; 10 RLaaS / post-training / fine-tuning platforms (includes continual-learning infra: Trajectory, Baseten, Fireworks, Thinking Machines/Tinker, Applied Compute, Engram); 11 synthetic data & pipelines; 12 permissioned data markets & licensing; 13 evals, benchmarks, observability; 14 inference serving; 15 routing, gateways, inference FinOps; 16 agent infrastructure; 17 deployment / implementation / FDE services; 18 coding agents & dev tools; 19 vertical AI by domain (legal, healthcare, finance, support, sales, search, voice, robotics); 20 consumer AI; 21 AI-native rollups / buyout vehicles. Company lists and latest rounds come from Thread C's venture-sources research output; every entity gets a dated membership row and, where public, a CIK.

## Appendix E — Continual-learning ladder (shared indicator; bucket 5 ⇄ sub-layer 10)

| Rung | Description | Evidence today (Sept 2026) | Observables |
|---|---|---|---|
| L0 | Static snapshot; memory = files in context | Default for frontier models | — |
| L1 | Gradient-free memory: feedback distilled into retrievable rules | arXiv 2607.22157: pass^1 1.6× (verdict) to 2.6× (corrections) over static RAG on τ-bench banking; cross-model transfer of the store | pass^1 lift with memory; hold rate; transfer |
| L2 | Population-level online learning: one objective, all users | Cursor Tab (400M+ req/day); Baseten live draft-model training (+20% median accept) | refresh cadence; documented lift |
| L3 | Per-customer adapters on a cadence | Trajectory: hourly→weekly LoRA checkpoints, A/B routed, provenance, ~1h pipeline with Baseten; Decagon weekly | `cl_refresh_cadence_hours`; `cl_adapters_per_product`; per-customer lift over time |
| L4 | Organisation knowledge in weights | Harvey + Engram: firm knowledge internalised, +15% criteria pass, −58% tokens on LAB: Firm Knowledge; Tenet (Kimi K3, async RL with Fireworks) | `cl_forgetting_retention`; firm-knowledge lift; cost/query |
| L5 | Per-session weight updates that persist and pool without forgetting | Research only: rank-1 LoRA continuous merge; nested learning/Hope; Titans; TTT; EAFT; on-policy self-distillation; SDPO off-policy | lab release branded continual/online learning; forgetting benchmark; per-user weight divergence |
| L6 | Six-month-employee test passed on a public benchmark | None | benchmark exists and a frontier system passes |

Status rule: n = L0–L3; f = L5–L6; L4 = `emerging`. Sub-metrics: `cl_refresh_cadence_hours`, `cl_adapters_per_product`, `cl_forgetting_retention`, `cl_learning_curve_slope`, `cl_benchmark_exists`, `cl_lab_release_claims`. Capture cross-links: venture $ into sub-layer 10, lab procurement of RL environments and expert data, enterprise session-training policies (whether the deployment→training channel is open).

## Appendix F — "Who we read"

Diffusion: Arvind Narayanan, Sayash Kapoor; Dwarkesh Patel; Toby Ord; Ajeya Cotra; Ryan Greenblatt; Daniel Kokotajlo; Nathan Lambert; Andrej Karpathy; Sasha Rush; Beren Millidge; Ege Erdil, Tamay Besiroglu, Jaime Sevilla, Lennart Heim; Erik Brynjolfsson, Bharat Chandar, Ruyu Chen, Avinash Collis; Nela Richardson; Lisa Simon, Ben Zweig; Martha Gimbel, Molly Kinder; Neale Mahoney, Erika McEntarfer; Anders Humlum; Xiang Hui, Oren Reshef, Luofeng Zhou; David Deming, Alexander Bick, Adam Blandin; Daron Acemoglu; Jed Kolko; Nathan Goldschlag; Till von Wachter; Lucy Wark; Jack Clark; Dean Ball; Charles O'Neill; Ronak Malde, Arjun Karanam, Michael Elabd; Niko Grupen, Gabe Pereyra; Jakub Pachocki, Dario Amodei, Sam Altman (tier 7).

Capture: Dylan Patel (SemiAnalysis); Guido Appenzeller, Sarah Wang, Martin Casado (a16z); David Cahn (Sequoia); Jamin Ball (Clouded Judgment); Tomasz Tunguz; Tanay Jaipuria; Ben Thompson; Doug O'Laughlin; Ben Bajarin; Jim Covello, Michael Cembalest, Gil Luria, Paul Kedrosky; Ara Kharazian (Ramp); Menlo's enterprise AI team; Peter Walker (Carta); Nathan Benaich (Air Street); Kelvin Mu; The Information's AI Agenda team.

Organisations and series: METR; Epoch AI; Artificial Analysis; ARC Prize; Sierra (τ-bench); Princeton HAL; MIT FutureTech; MIT NANDA; Menlo; McKinsey; Stanford Digital Economy Lab + ADP Research; Revelio Labs; California Policy Lab + EDD; Yale Budget Lab; NY Fed; Federal Reserve Board; SIEPR; PIIE; Anthropic Economic Index; OpenAI research disclosures; Census BTOS; BLS; FDA; NCSL/MultiState/Transparency Coalition; EU AI Office; SEC EDGAR; OpenRouter; Ramp; SemiAnalysis; Bain; Goldman/JPM/Citi/Barclays; Bloomberg (circular-deals map); Sacra; Dealroom; PitchBook/Crunchbase/CB Insights/Tracxn; Carta; Bessemer/ICONIQ/Air Street; OECD.AI; Baseten Research; Trajectory; Harvey; Engram; Fireworks; Thinking Machines; Cursor; AI Futures Project; Metaculus; ai2027-tracker (methodology only).

Handle verification is a task, not an assumption.
