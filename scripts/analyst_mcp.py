"""The private analyst's tools, as a local MCP server for Claude Code (stdio). Nothing here is hosted.

    claude mcp add slow-variables-analyst -- uv run --directory <repo> --extra analyst python scripts/analyst_mcp.py

It serves the public Ask tools over a local Store (sql, metric, indicator, scenarios, claims, entity, rent_rubric and
the rest), plus `corpus_search` and `read_passage` over the index scripts/analyst_corpus.py builds outside the repo,
and `check_answer`, which runs the site's citation check on a draft, [corpus:<id>] passages included.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
os.chdir(REPO)  # the Store reads seed/ and semantic/ relative to the repo

from mcp.server.mcpserver import MCPServer  # noqa: E402

from ai_tracker import store as st  # noqa: E402
from ai_tracker.analysis.metrics import run_metrics  # noqa: E402
from ai_tracker.query import ask as ask_mod  # noqa: E402
from ai_tracker.query.citecheck import CITE, Record, check  # noqa: E402

DB = Path(os.environ.get("ANALYST_DB", "~/.ai-tracker/analyst.db")).expanduser()
SITE_TOOLS = [t for t in ask_mod.TOOLS if t["name"] != "rent_rubric"]  # its **kwargs get an explicit signature below

server = MCPServer(
    "slow-variables-analyst",
    instructions="The Slow Variables tracker's data and the owner's local reading. Cite site records as the public "
    "Ask does ([obs:id], [derived:id], [claim:id], [src:id] ...) and local passages as [corpus:<id>]; run "
    "check_answer on every draft. Paid and book passages are paraphrased and credited, never quoted at length.",
)


def _tools() -> ask_mod.Tools:
    s = st.Store()
    if not s.derived:
        s.derived = run_metrics(s.con)
        s.semantic_tables()
    s.prediction_table()
    return ask_mod.Tools(s)


TOOLS = _tools()
for t in SITE_TOOLS:
    server.tool(name=t["name"], description=t["description"])(getattr(TOOLS, t["name"]))


@server.tool(description=next(t["description"] for t in ask_mod.TOOLS if t["name"] == "rent_rubric"))
def rent_rubric(
    rent_kind: str | None = None,
    appropriability: str | None = None,
    complementary_assets: str | None = None,
    asset_owner: str | None = None,
    durability: str | None = None,
) -> Any:
    given = dict(rent_kind=rent_kind, appropriability=appropriability, complementary_assets=complementary_assets)
    given |= dict(asset_owner=asset_owner, durability=durability)
    return TOOLS.rent_rubric(**{k: v for k, v in given.items() if v})


def _db() -> sqlite3.Connection:
    if not DB.exists():
        raise RuntimeError(f"no index at {DB}: run scripts/analyst_corpus.py")
    return sqlite3.connect(f"file:{DB}?mode=ro", uri=True)


@server.tool()
def corpus_search(query: str, k: int = 8, collection: str | None = None, access: str | None = None) -> list[dict[str, Any]]:
    """Search the owner's local reading (knowledge base, singularity canon, The Diff, Sean Cai, Gary Marcus, Normal
    Technology, the sales canon, Inference Engineering, the tracker's private notes). Each hit has a `cite` to use as
    [corpus:<id>], its collection, title, author, year, access (public, paid, book, own) and a snippet. Paid and book
    passages are for paraphrase with credit. Optional filters: collection, access."""
    terms = re.findall(r"\w+", query)
    if not terms:
        return []
    where, params = ["chunks MATCH ?"], [" OR ".join(f'"{w}"' for w in terms)]
    for col, v in (("collection", collection), ("access", access)):
        if v:
            where.append(f"{col} = ?")
            params.append(v)
    rows = _db().execute(
        "SELECT rowid, collection, title, author, year, access, url, snippet(chunks, 0, '', '', ' … ', 48)"
        f" FROM chunks WHERE {' AND '.join(where)} ORDER BY rank LIMIT ?",
        [*params, max(1, min(int(k), 25))],
    ).fetchall()
    keys = ("collection", "title", "author", "year", "access", "url", "snippet")
    return [{"cite": f"corpus:{r[0]}", **dict(zip(keys, r[1:]))} for r in rows]


@server.tool()
def read_passage(cite: str, neighbours: int = 0) -> dict[str, Any]:
    """The full text of a corpus passage by its cite (corpus:<id>), with up to three neighbouring passages from the
    same work on either side when `neighbours` is set."""
    rowid = int(cite.split(":")[-1])
    con = _db()
    row = con.execute("SELECT path, part, title, author, year, access, url FROM chunks WHERE rowid = ?", [rowid]).fetchone()
    if not row:
        return {"error": f"no passage {cite}"}
    n = max(0, min(int(neighbours), 3))
    parts = con.execute(
        "SELECT rowid, part, text FROM chunks WHERE path = ? AND part BETWEEN ? AND ? ORDER BY part",
        [row[0], row[1] - n, row[1] + n],
    ).fetchall()
    meta = dict(zip(("title", "author", "year", "access", "url"), row[2:]))
    return {**meta, "passages": [{"cite": f"corpus:{r[0]}", "text": r[2]} for r in parts]}


@server.tool()
def check_answer(text: str) -> dict[str, Any]:
    """Run the site's citation check on a draft: every number must sit in a sentence citing a record that holds it,
    [corpus:<id>] passages included (whole-token match). Returns ok, the failures, and the draft with unverified
    numbers marked."""
    ids = CITE.findall(text)
    recs = TOOLS.records([(k, i) for k, i in ids if k != "corpus"])
    corpus = [i for k, i in ids if k == "corpus" and i.isdigit()]
    if corpus:
        con = _db()
        for i in corpus:
            r = con.execute("SELECT text FROM chunks WHERE rowid = ?", [int(i)]).fetchone()
            if r:
                recs[f"corpus:{i}"] = Record(i, "corpus", [], "", r[0])
    res = check(text, recs)
    missing = sorted({f"{k}:{i}" for k, i in ids} - set(recs))
    return {"ok": res.ok and not missing, "failures": res.failures, "unresolved_citations": missing, "annotated": res.annotated}


if __name__ == "__main__":
    server.run()
