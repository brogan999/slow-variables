# ai-tracker

One tracker, two lenses: how fast AI value moves through the diffusion stages (Narayanan & Kapoor) and who keeps it at each layer of the stack. Every number traces to a dated, graded observation; the site never computes a number.

- Spec: `docs/briefs/`. Build plan and decisions: `docs/plan.md`. Seed corpus: `docs/research/`, `docs/interpretation/`. Rules for agents: `CLAUDE.md`.

## Run

```bash
cp .env.example .env            # SEC EDGAR needs a User-Agent with a contact address
uv sync
uv run ai-tracker ingest --all  # metr, sec_xbrl, manual, bls, epoch -> data/observations/*.jsonl
uv run ai-tracker build         # seed YAML + JSONL -> DuckDB (in memory), prints counts
uv run ai-tracker evaluate      # derived metrics; proposes StatusEvents into data/proposed_status_events.jsonl
#   ...write a `reason` on each proposal (or delete the row), then:
uv run ai-tracker approve       # pending observations -> approved; reasoned proposals -> data/status_events.jsonl
uv run ai-tracker check         # publish rules; exit 1 on any violation
uv run ai-tracker export        # web/data/*.json (committed) + web/public/data/*.csv
cd web && pnpm install && pnpm dev
```

`uv run pytest`, `uv run ruff check src tests`. CI runs the same; the nightly workflow ingests, evaluates, checks, exports and opens a PR with `data/summary.md` as the body. Merge = publish (Vercel builds `web/`).

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
