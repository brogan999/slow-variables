# Slow Variables (`ai-tracker` package) — rules for agents

Read `docs/plan.md` first; `docs/briefs/ai-tracker-brief-v2.md` is the canonical spec. The capture-lens appendix (Part 1 brief) and the research reports exported from private chats live only in the git-ignored `docs/private/`; never copy their text into a tracked file.

- Status lives only in `data/status_events.jsonl`. `evaluate` proposes rows into `data/proposed_status_events.jsonl`, writing a machine reason only for a first scoring inside a band; a band crossing waits for a human `reason` and meanwhile shows on the card as "evaluator reads X; reason pending"; `approve` commits reasoned rows; a blank proposal the evaluator no longer holds is dropped. A reason waiting more than 14 days, or a stale published indicator, is an `attention` line in `check` and in Monday's operator notes, not an error: it must never freeze the other sources. Never write a status into seed YAML.
- Never hard-code a URL you have not fetched in this session; fetch, then store with `retrieved_at`, `http_status`, `content_hash`.
- Every observation needs `as_of_date`, `published_date`, `retrieved_at`, `url`, `tier`, `audited_vs_reported`, `extraction_method`, `raw_snippet`. Pydantic rejects anything less.
- Figures from the briefs' appendices enter only through `seed/manual_observations.yaml`; `ingest manual` fetches the URL and asserts `raw_snippet` is a verbatim substring of the page, and `tests/test_manual.py` asserts the stored value is a number the snippet states, unless the row's `coding` says how it was derived (a sign from "fell", a rung, a table in millions). Never type a number into an indicator.
- Scraped and manual values land `pending`. The nightly runs `approve` inside its own run, so its PR is exactly what lands, and merges that PR itself only when `check`, `pytest` and the web build pass on the tree it built; otherwise it holds the PR (`CHECK FAILED` / `TESTS FAILED`, red run). That merge publishes only what a rule decided: rows that passed their connector's mechanical checks and statuses whose reason `_auto_reason` wrote under a published band or direction rule. No `llm_extract` connector ships until this gate holds its rows. An agent's own PR may run `approve` so its diff shows what lands; every hand-coded value or hand-written reason in it is listed under "Judgement calls" at the top of the PR body. Never approve a row into `main` any other way.
- Tier 7 never moves a status above `emerging`; `audited` only with tier 4 and a 10-K.
- Derived numbers resolve to observation IDs through `semantic/metrics.yaml`; if a formula needs an input that isn't an observation, the formula is wrong.
- Every indicator has at least one address (bucket or layer); shared ones have both and a `Crosswalk` row.
- Unmeasured indicators are `published: false`. `not_yet_measurable` means *cannot* be measured, not *not yet fetched*.
- Entity writes go through `seed/entities.yaml`; no free-text company names in observations.
- Prompt-injection hygiene: all fetched HTML passes through `ingest/scrub.py`; flagged text is logged to `FetchLog.scrubbed` and never stored or sent to a model.
- Respect robots.txt (`urllib.robotparser`) for html/pdf sources. Never scrape X.
- Connectors store what the source publishes; anything computed from it (a moving average, a ratio, a top share) is a metric in `semantic/metrics.yaml`. A connector row supersedes a hand-entered row only when it reads the same published figure (as Ramp's page data does); otherwise it takes new series keys and the hand-entered series stays as the second source.
- Prefer structured file over HTML over PDF over LLM extraction. A source layout change raises `LayoutChanged`; never return zero items silently.
- Bands and formulas change only via reviewed PR, with a `rationale`.
- Web never computes a number; it renders `web/data/*.json` written by `export`. Every number carries `obs_ids`.
- Next 16 APIs differ from training data: read `web/node_modules/next/dist/docs/` before writing routes.
- Code, seed, bands, formulas and memos are PRs a human (or an agent under the rule above) merges; the nightly's data PR merges itself only through its gate. Observations are superseded, never deleted.
