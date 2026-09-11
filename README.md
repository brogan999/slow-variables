# Slow Variables

*The slow variables decide how AI lands: adoption in hours worked, margins in filings, productivity in the statistics.*

One tracker, two lenses: how fast AI value moves through the diffusion stages (Narayanan & Kapoor) and who keeps it at each layer of the stack. Every number traces to a dated, graded observation; the site never computes a number.

- Spec: `docs/briefs/`. Build plan and decisions: `docs/plan.md`. Seed corpus: `docs/research/`, `docs/interpretation/`. Rules for agents: `CLAUDE.md`.

## Run

```bash
cp .env.example .env            # SEC EDGAR needs a User-Agent with a contact address
uv sync
uv run ai-tracker ingest --all  # every connector (26 today; `ingest --help` lists them) -> data/observations/*.jsonl
uv run ai-tracker build         # seed YAML + JSONL -> DuckDB (in memory), prints counts
uv run ai-tracker evaluate      # derived metrics; proposes StatusEvents into data/proposed_status_events.jsonl
#   ...write a `reason` on each proposal (or delete the row), then:
uv run ai-tracker approve       # pending observations -> approved; reasoned proposals -> data/status_events.jsonl
uv run ai-tracker check         # publish rules; exit 1 on any violation
uv run ai-tracker export        # web/data/*.json (committed) + web/public/data/*.csv
uv run ai-tracker memo          # docs/memos/<date>.md: model prose with a citation check, else the deterministic digest
uv run ai-tracker ask "..."     # one question through the query service's tool loop (needs ANTHROPIC_API_KEY)
uv run ai-tracker golden        # the twelve golden questions plus one refusal case
uv run ai-tracker serve         # the query service (what Fly runs); the site proxies /api/query/* to it
cd web && pnpm install && pnpm dev
```

Services: the query service runs on Fly (`fly.toml`, `Dockerfile`, deployed by `deploy-query.yml` on pushes that touch data, seed, semantic or src); the site needs `QUERY_URL` and `QUERY_TOKEN`; the service needs `QUERY_TOKEN`, `ANTHROPIC_API_KEY` and optionally `QUERY_DAILY_USD_CAP` (default 5). The nightly (`nightly.yml`, 06:17 UTC) opens a pull request and merges it itself when `check`, `pytest` and the web build pass, then redeploys the query service; the memo job (`memo.yml`, Mondays 09:17 UTC) opens a pull request for a human to merge, with operator notes in its body. X posts are quoted from pages that already carry their text; the tracker makes no request to X.

`uv run pytest`, `uv run ruff check src tests`. CI runs the same; the nightly workflow ingests, evaluates, checks, tests, builds, exports, opens a PR with `data/summary.md` as the body and merges it through that gate (Vercel builds `web/` on the merge).

## Where things live

| What | Where |
|---|---|
| Schema, tier guards, grade derivation | `src/ai_tracker/schema.py` |
| Connectors (one per source) | `src/ai_tracker/ingest/connectors/` |
| Figures quoted from documents | `seed/manual_observations.yaml` (snippet must appear verbatim on the fetched page) |
| Derived metrics (DuckDB SQL) | `semantic/metrics.yaml` |
| Bands, direction rules, counterevidence | `seed/indicators/*.yaml` |
| Status (the only place) | `data/status_events.jsonl` |
| Observations (append-only, superseded never deleted) | `data/observations/*.jsonl` |
| Query service, citation post-check, golden questions | `src/ai_tracker/query/`, `seed/golden.yaml`, `seed/analyses.yaml` |
| Weekly memo | `src/ai_tracker/memo.py`, `docs/memos/` |
