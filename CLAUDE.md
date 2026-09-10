# ai-tracker — rules for agents

Read `docs/plan.md` first; `docs/briefs/ai-tracker-brief-v2.md` is the canonical spec, `docs/briefs/value-capture-tracker-part1.md` the capture-lens appendix.

- Status lives only in `data/status_events.jsonl`. `evaluate` proposes rows into `data/proposed_status_events.jsonl`; a human writes the `reason`; `approve` commits them. Never write a status into seed YAML.
- Never hard-code a URL you have not fetched in this session; fetch, then store with `retrieved_at`, `http_status`, `content_hash`.
- Every observation needs `as_of_date`, `published_date`, `retrieved_at`, `url`, `tier`, `audited_vs_reported`, `extraction_method`, `raw_snippet`. Pydantic rejects anything less.
- Figures from the briefs' appendices enter only through `seed/manual_observations.yaml`; `ingest manual` fetches the URL and asserts `raw_snippet` is a verbatim substring of the page. Never type a number into an indicator.
- LLM-extracted, scraped and manual values land `pending`; merge to main is approval. Do not approve your own extraction.
- Tier 7 never moves a status above `emerging`; `audited` only with tier 4 and a 10-K.
- Derived numbers resolve to observation IDs through `semantic/metrics.yaml`; if a formula needs an input that isn't an observation, the formula is wrong.
- Every indicator has at least one address (bucket or layer); shared ones have both and a `Crosswalk` row.
- Unmeasured indicators are `published: false`. `not_yet_measurable` means *cannot* be measured, not *not yet fetched*.
- Entity writes go through `seed/entities.yaml`; no free-text company names in observations.
- Prompt-injection hygiene: all fetched HTML passes through `ingest/scrub.py`; flagged text is logged to `FetchLog.scrubbed` and never stored or sent to a model.
- Respect robots.txt (`urllib.robotparser`) for html/pdf sources. Never scrape X.
- Prefer structured file over HTML over PDF over LLM extraction. A source layout change raises `LayoutChanged`; never return zero items silently.
- Bands and formulas change only via reviewed PR, with a `rationale`.
- Web never computes a number; it renders `web/data/*.json` written by `export`. Every number carries `obs_ids`.
- Next 16 APIs differ from training data: read `web/node_modules/next/dist/docs/` before writing routes.
- Data and status changes are PRs; ingestion opens them, humans merge. Observations are superseded, never deleted.
