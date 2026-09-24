"""Score Futures rows with the rent rubric (plan Part 20).

    uv run python scripts/futures_score.py <rows.jsonl> <out.jsonl> --models claude-opus-5-5,claude-sonnet-5 [--limit 50] [--cap-usd 5]

Each model answers only the rubric's inputs, a category and an arrival judgement, as a forced tool call with fixed
enums (seed/futures/rubric.yaml), with thinking off and a capped reply. The first model also rewords the row in the
site's words. Rows already in <out> are skipped, so a run resumes. Token usage is logged per call, and the run stops
before it can pass --cap-usd. Keys come from the environment (ANTHROPIC_API_KEY, OPENAI_API_KEY); nothing is printed.
Everything written here is private working data: the public seed is written from it after review."""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import anthropic
import httpx

from ai_tracker.futures import rubric

# USD per million tokens (input, output), for the spend guard only; the logged token counts are the record.
PRICE = {"claude-opus-5-5": (5.0, 25.0), "claude-sonnet-5": (2.0, 10.0), "gpt-6": (5.0, 20.0)}

SYSTEM = """You judge technologies imagined in science fiction or forecast in non-fiction, for a public research site.
For the technology described, answer every field of the `score` tool, choosing only from the allowed values.

- category: the one best fit.
- line: (only when asked) one plain sentence of at most 25 words saying what the technology does, in your own words.
  Do not reuse the description's wording, do not quote it, name no characters, and write no digits except years.
- rent_kind: if this technology existed and sold, the main source of lasting profit for whoever collects it:
  scarcity (a limited input or capability others cannot easily add), scale_network (it gets better or cheaper
  the more people use it), switching_cost (users are locked in once they adopt it), regulatory (a licence,
  permit or legal monopoly), none (anyone could supply it, so competition removes profit).
- appropriability: tight if its maker could stop others copying it (patents, secrecy, rare know-how); else weak.
- complementary_assets: specialised if reaching customers needs assets few hold (factories, networks,
  approvals, distribution, data); generic if not.
- asset_owner: who holds those assets today: innovator, incumbents, platforms, or regulators_licensees.
- durability: how long that profit would last before competitors or a new bottleneck erode it: short (under
  five years), medium (five to twenty), long (decades).
- arrival_decade: if it does not exist yet, the decade a working, commercially available version is most
  likely; after_2100 if later; not_physically_possible if it needs physics we have no evidence for;
  cannot_judge if you genuinely cannot tell. If it already exists, answer 2020s.
- needs: the main thing that must happen first.
Judge the technology as described, not the story. Be calibrated: say cannot_judge rather than guess."""


def tool(spec: dict, reword: bool) -> dict:
    enum = lambda k: {"type": "string", "enum": spec["inputs"][k]}  # noqa: E731
    props = {
        "category": {"type": "string", "enum": spec["categories"]},
        "rent_kind": enum("rent_kind"),
        "appropriability": enum("appropriability"),
        "complementary_assets": enum("complementary_assets"),
        "asset_owner": enum("asset_owner"),
        "durability": enum("durability"),
        "arrival_decade": {"type": "string", "enum": spec["arrival"]["decades"]},
        "needs": {"type": "string", "enum": spec["arrival"]["needs"]},
    }
    if reword:
        props["line"] = {"type": "string", "maxLength": 220}
    return {
        "name": "score",
        "description": "Record the judgement.",
        "input_schema": {
            "type": "object",
            "properties": props,
            "required": list(props),
            "additionalProperties": False,
        },
    }


def prompt(row: dict) -> str:
    return (
        f"Technology: {row['name']}\nFrom: {row['work']} by {row['author']}, {row['imagined']}\n"
        f"Description: {row['description']}\nPhysical or digital: {row.get('bits_atoms') or 'unknown'}"
    )


def call_anthropic(
    client: anthropic.Anthropic, model: str, spec: dict, row: dict, reword: bool
) -> tuple[dict, dict]:
    t = tool(spec, reword)
    r = client.messages.create(
        model=model,
        max_tokens=400,
        system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": prompt(row) + ("\nAlso write `line`." if reword else "")}],
        tools=[t],
        tool_choice={"type": "tool", "name": "score"},
        thinking={"type": "disabled"},
    )
    out = next(b.input for b in r.content if b.type == "tool_use")
    return out, {"in": r.usage.input_tokens, "out": r.usage.output_tokens}


def call_openai(model: str, spec: dict, row: dict, reword: bool) -> tuple[dict, dict]:
    t = tool(spec, reword)
    r = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
        json={
            "model": model,
            "max_completion_tokens": 400,
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt(row)}],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "score", "strict": True, "schema": t["input_schema"]},
            },
        },
        timeout=120,
    )
    r.raise_for_status()
    d = r.json()
    return json.loads(d["choices"][0]["message"]["content"]), {
        "in": d["usage"]["prompt_tokens"],
        "out": d["usage"]["completion_tokens"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("rows")
    ap.add_argument("out")
    ap.add_argument("--models", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shortlist-first", action="store_true")
    ap.add_argument("--cap-usd", type=float, required=True)
    a = ap.parse_args()
    spec = rubric()
    models = a.models.split(",")
    rows = [json.loads(line) for line in open(a.rows)]
    if a.shortlist_first:
        rows.sort(key=lambda r: not r["shortlist"])
    rows = rows[: a.limit] if a.limit else rows
    done = {(d["id"], d["model"]) for d in map(json.loads, open(a.out))} if Path(a.out).exists() else set()
    spent = (
        sum(
            (d["usage"]["in"] * PRICE[d["model"]][0] + d["usage"]["out"] * PRICE[d["model"]][1]) / 1e6
            for d in map(json.loads, open(a.out))
        )
        if Path(a.out).exists()
        else 0.0
    )
    client = anthropic.Anthropic() if any(m.startswith("claude") for m in models) else None

    def one(job: tuple[dict, str]) -> dict:
        row, model = job
        reword = model == models[0]
        try:
            ans, usage = (
                call_anthropic(client, model, spec, row, reword)
                if model.startswith("claude")
                else call_openai(model, spec, row, reword)
            )
            return {"id": row["id"], "model": model, "answer": ans, "usage": usage}
        except Exception as e:  # noqa: BLE001 - one failed call must not stop the run; it is retried on resume
            return {"id": row["id"], "model": model, "error": type(e).__name__, "usage": {"in": 0, "out": 0}}

    jobs = [(r, m) for r in rows for m in models if (r["id"], m) not in done]
    with open(a.out, "a") as f, ThreadPoolExecutor(8) as pool:
        for res in pool.map(one, jobs):
            if "error" in res:
                print(f"{res['id']} {res['model']}: {res['error']}", file=sys.stderr)
                continue
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
            spent += (
                res["usage"]["in"] * PRICE[res["model"]][0] + res["usage"]["out"] * PRICE[res["model"]][1]
            ) / 1e6
            if spent >= a.cap_usd:
                print(f"stopping at the cap: ${spent:.2f}", file=sys.stderr)
                pool.shutdown(cancel_futures=True)
                break
    print(f"{len(jobs)} calls queued; about ${spent:.2f} spent so far")


if __name__ == "__main__":
    main()
