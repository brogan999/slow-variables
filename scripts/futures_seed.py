"""Write the public Futures seed from the private working files (plan Part 20, 2/4).

    uv run python scripts/futures_seed.py <private futures dir> seed/futures/ideas.jsonl

Joins rows.jsonl (futures_import), merged-all.jsonl (futures_votes: category, arrival decade and needs by three
scorers, majority rule; a three-way split takes Opus's vote), votes/rent-*.jsonl (the rent inputs and the technology flag, re-scored by one scorer with
the instruction to judge each market as if the thing already existed), lines-manual.json (lines written by hand for
rows a scorer saw without their text, or corrected on review), votes/market-*.jsonl (whether a thing would be sold,
asked only where the rules would give a rent) and overrides.json (a reviewed answer that replaces a
voted one, with its reason, kept on the row). Technovelgy's descriptions and the sheet's product column stay private;
the seed keeps facts (name, work, author, years), the site's reworded line, and the votes with their majorities."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from ai_tracker.futures import RENT, VOTED, judged, rubric


def main(private: str, out: str) -> None:
    d = Path(private)
    rows = {r["id"]: r for r in map(json.loads, (d / "rows.jsonl").read_text().splitlines())}
    manual = json.loads((d / "lines-manual.json").read_text())
    overrides = json.loads((d / "overrides.json").read_text())
    merged = [json.loads(line) for line in (d / "merged-all.jsonl").read_text().splitlines()]
    market = {
        r["id"]: r["market"]
        for f in sorted((d / "votes").glob("market-*.jsonl"))
        for r in map(json.loads, f.read_text().splitlines())
    }
    rent = {
        r["id"]: r
        for f in sorted((d / "votes").glob("rent-*.jsonl"))
        for r in map(json.loads, f.read_text().splitlines())
    }
    assert {m["id"] for m in merged} == set(rows) == set(rent), (
        "every imported row needs one merged and one rent record"
    )
    spec = rubric()
    with open(out, "w") as f:
        for m in sorted(merged, key=lambda m: (rows[m["id"]]["imagined"], m["id"])):
            r = rows[m["id"]]
            idea = {k: r[k] for k in ("id", "name", "work", "author", "imagined", "arrival", "shortlist")}
            idea["line"] = manual.get(m["id"]) or m["line"]
            idea["technology"] = rent[m["id"]]["technology"]
            idea |= {k: m[k] for k in VOTED} | {k: rent[m["id"]][k] for k in RENT}
            split = [k for k in VOTED if m[k] == "no_majority" and m[f"{k}_votes"][0] is not None]
            idea |= {k: m[f"{k}_votes"][0] for k in split}  # Opus's vote breaks a three-way split
            if split:
                idea["tiebreak"] = split
            if m["id"] in market:
                idea["market"] = market[m["id"]]
            fixed = overrides.get(m["id"], {})
            idea |= {k: v for k, (v, _why) in fixed.items()}
            if fixed:
                idea["overrides"] = {k: why for k, (_v, why) in fixed.items()}
            idea["pools"], idea["tier"] = judged(idea, spec)
            idea["votes"] = {k: m[f"{k}_votes"] for k in VOTED}
            f.write(json.dumps(idea, ensure_ascii=False) + "\n")
    print(f"{len(merged)} ideas written")


if __name__ == "__main__":
    main(*sys.argv[1:3])
