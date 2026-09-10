# Prior art

`~/ai-value-chain` (Aug 2026) was a first attempt at the capture side: Next 16 + Prisma/Postgres, 23-layer YAML taxonomy, honesty rules enforced as DB constraints. Not forked (Postgres is not the brief; the TS parquet story is weak). Ported from it:

- Epoch ZIP connector column maps (`config/sources.yaml`) → `ingest/connectors/epoch.py`
- SEC XBRL quarterly-duration filter and restatement dedupe (`src/lib/ingest/connectors/sec-xbrl.ts`) → `ingest/connectors/sec_xbrl.py`
- CC-BY attribution string stored on the source row and rendered on every Epoch chart
- "No data means no number, never 50" → `published: false` until an approved observation exists

`~/normaltech-predictions` (8 Sep 2026) produced the 89-bottleneck list and the 747-row N&K prediction extraction copied into `docs/research/`.
