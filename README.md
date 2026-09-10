# ai-tracker

One tracker, two lenses: how fast AI value moves through the diffusion stages (Narayanan & Kapoor) and who keeps it at each layer of the stack. Every number traces to a dated, graded observation.

- Spec: `docs/briefs/`. Build plan: `docs/plan.md`. Seed corpus: `docs/research/`, `docs/interpretation/`.
- Python spine (`src/ai_tracker`): `uv run ai-tracker ingest --all && uv run ai-tracker build && uv run ai-tracker evaluate && uv run ai-tracker export`
- Site (`web/`): `pnpm dev`
