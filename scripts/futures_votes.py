"""Merge three scorers' votes on Futures rows into one judged record per row (plan Part 20).

    uv run python scripts/futures_votes.py <votes dir> <tag> <out.jsonl>

Reads <votes dir>/{opus,sonnet,haiku}-<tag>.jsonl (written by scoring agents in the session, one JSON object per
row). Each field takes the value at least two scorers gave, else "no_majority". Where the rent pools and its tier
are then derived by futures.pools and futures.tier from the majority answers, never voted on; a row with any rubric
field in no_majority gets neither. Prints agreement per field."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

from ai_tracker.futures import pools, rubric, tier

SCORERS = ["opus", "sonnet", "haiku"]
FIELDS = [
    "category",
    "rent_kind",
    "appropriability",
    "complementary_assets",
    "asset_owner",
    "durability",
    "arrival_decade",
    "needs",
]


def load(path: Path) -> dict[str, dict]:
    return (
        {d["id"]: d for d in map(json.loads, path.read_text().splitlines()) if d.get("id")}
        if path.exists()
        else {}
    )


def derive(rec: dict, spec: dict) -> tuple[str | None, str | None]:
    """Where the rent pools and its tier, from majority answers. A split vote blocks a result only where the rule
    needs that answer: who owns the assets matters only when copying is easy and the assets are specialised."""
    if rec["category"] == "exotic_physics":
        return None, None
    need = ["appropriability"]
    if rec["appropriability"] == "weak":
        need.append("complementary_assets")
        if rec["complementary_assets"] == "specialised":
            need.append("asset_owner")
    if any(rec[k] == "no_majority" for k in need):
        return None, None
    where = pools(rec, spec)
    if where == "users":
        return where, "none"
    if rec["rent_kind"] == "no_majority" or rec["durability"] == "no_majority":
        return where, None
    return where, tier(rec, spec)


def majority(values: list[str]) -> str:
    v, n = Counter(values).most_common(1)[0]
    return v if n >= 2 else "no_majority"


def main(votes: str, tag: str, out: str) -> None:
    spec = rubric()
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
                vals = [g.get(k) for g in got]
                rec[k] = majority(vals)
                rec[f"{k}_votes"] = vals
                agree[k] += len(set(vals)) == 1
            rec["pools"], rec["tier"] = derive(rec, spec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    n = len(ids)
    print(f"{n} rows; all three agree: " + ", ".join(f"{k} {agree[k]}/{n}" for k in FIELDS))


if __name__ == "__main__":
    main(*sys.argv[1:4])
