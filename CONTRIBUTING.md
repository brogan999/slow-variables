# Contributing

Corrections and additions are pull requests. The rules that make a change mergeable are in `CLAUDE.md` and on the
site's methodology page; the short version:

- **A number needs a record.** Figures enter through a connector or `seed/manual_observations.yaml`, where the
  manual connector fetches the URL and checks that `raw_snippet` appears verbatim on the page. Nothing is typed
  into an indicator.
- **Status lives in `data/status_events.jsonl` only**, each event with a reason, evidence ids and an author.
  `ai-tracker evaluate` proposes; a human writes the reason (or deletes the row); `ai-tracker approve` commits.
- **Bands, direction rules and formulas change only by pull request** with the `rationale` updated.
- **Observations are superseded, never deleted.** To correct a value, add the corrected row; the ledger links it
  to the row it replaces.
- **Test first.** Every change to behaviour starts with a failing test that names it; run it red, then make it
  green. A bug fix starts with a test that reproduces the bug. List the new tests under "Tests first" in the PR.
- **Run the loop before opening a PR:** `uv run pytest`, `uv run ruff check src tests`,
  `uv run ai-tracker evaluate && uv run ai-tracker check` (`check` alone reads stale derived rows),
  `cd web && pnpm exec tsc --noEmit -p . && pnpm lint && pnpm build`. `python` and `web` are required checks on
  `main`.

Source suggestions, disputed figures and counterevidence are welcome as issues; say what the record is and where
it can be fetched.
