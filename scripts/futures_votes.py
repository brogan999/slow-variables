"""Merge three scorers' votes on Futures rows into one judged record per row (plan Part 20).

    uv run python scripts/futures_votes.py <votes dir> <tag> <out.jsonl>

Reads <votes dir>/{opus,sonnet,haiku}-<tag>.jsonl (written by scoring agents in the session, one JSON object per
row). A vote outside the rubric's words (or cannot_judge, which every field allows) is spoiled, except the spelling
"specialized", which is read as "specialised". Each field takes the value at least two valid votes gave, else
"no_majority". Where the rent pools and its tier
are then derived by futures.judged from the majority answers, never voted on. Prints agreement per field."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from ai_tracker.futures import FIELDS, judged, rubric

SCORERS = ["opus", "sonnet", "haiku"]


def load(path: Path) -> dict[str, dict]:
    return (
        {d["id"]: d for d in map(json.loads, path.read_text().splitlines()) if d.get("id")}
        if path.exists()
        else {}
    )


def allowed(spec: dict) -> dict[str, set[str]]:
    words = {**spec["inputs"], "category": spec["categories"], "arrival_decade": spec["arrival"]["decades"]}
    words["needs"] = spec["arrival"]["needs"]
    return {k: {*v, "cannot_judge"} for k, v in words.items()}


def clean(value: object, words: set[str]) -> str | None:
    value = "specialised" if value == "specialized" else value
    return value if value in words else None


def majority(values: list[str | None]) -> str:
    counts = Counter(v for v in values if v is not None)
    v, n = counts.most_common(1)[0] if counts else (None, 0)
    return v if n >= 2 else "no_majority"


def main(votes: str, tag: str, out: str) -> None:
    spec = rubric()
    words = allowed(spec)
    by = {s: load(Path(votes) / f"{s}-{tag}.jsonl") for s in SCORERS}
    ids = sorted(set().union(*by.values()))
    agree = Counter()
    with open(out, "w") as f:
        for i in ids:
            got = [by[s][i] for s in SCORERS if i in by[s]]
            if len(got) < 3:
                print(f"{i}: only {len(got)} scorers", file=sys.stderr)
                continue
            rec = {"id": i, "line": by["opus"][i].get("line")}
            for k in FIELDS:
                vals = [clean(g.get(k), words[k]) for g in got]
                rec[k] = majority(vals)
                rec[f"{k}_votes"] = vals
                agree[k] += len(set(vals)) == 1
            rec["pools"], rec["tier"] = judged(rec, spec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n = len(ids)
    print(f"{n} rows; all three agree: " + ", ".join(f"{k} {agree[k]}/{n}" for k in FIELDS))


if __name__ == "__main__":
    main(*sys.argv[1:4])
