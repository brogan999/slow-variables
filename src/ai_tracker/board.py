"""Every prediction on the site in one list: other people's dated claims (the ledger), the outlook's tested claims,
the migration page's predictions and the home page's exits, each with one plain status word. Pure over built dicts,
so the export and the query service share it and tests need no store."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SPEC = Path("seed/board.yaml")

# The status word each family's own vocabulary maps to; the page prints this table from the export.
WORDS = {
    "ledger": {
        "confirmed": "happening",
        "ahead": "happening",
        "on_track": "happening",
        "behind": "slower",
        "emerging": "too_early",
        "not_yet_testable": "too_early",
        None: "too_early",
    },
    "outlook": {"holding": "happening", "failing": "not_happening", "both": "both", "untestable": "too_early"},
    "migration": {"holding": "happening", "failing": "not_happening", "untestable": "too_early"},
    "exit": {
        "supported": "happening",
        "unsupported": "not_happening",
        "contradicted": "not_happening",
        "untestable": "too_early",
    },
}
ORDER = ["happening", "not_happening", "slower", "both", "too_early"]
OPS = ("gt", "gte", "lt", "lte")


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text())


def _who(c: dict[str, Any], sources: dict[str, dict[str, Any]]) -> str:
    names = [sources[h].get("short") or sources[h]["who"] for h in c.get("holders") or [] if h in sources]
    if c.get("attribution") == "site" or not names:
        return "This site"
    lead = " and ".join(names)
    return f"This site, extending {lead}" if c.get("attribution") == "extension" else lead


def _test(t: dict[str, Any] | None) -> dict[str, Any] | None:
    if not t:
        return None
    op = next(k for k in OPS if k in t)
    return {"fact": t["fact"], "op": op, "against": t[op]}


def rows(
    spec: dict[str, Any],
    ledger: list[dict[str, Any]],
    outlook: dict[str, Any],
    argument: dict[str, Any],
    verdicts: list[dict[str, Any]],
    exits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lines = spec["ledger"]
    for p in ledger:
        if p["id"] not in lines or not p.get("published", True):
            continue
        out.append(
            {
                "id": p["id"],
                "kind": "ledger",
                "folio": lines[p["id"]]["folio"],
                "who": p["claimant"],
                "attribution": "author",
                "line": lines[p["id"]]["line"],
                "state": p.get("status"),
                "settles": p.get("window_end"),
                "test": None,
                "reading": None,
                "sources": [p["claim_url"]] if p.get("claim_url") else [],
                "href": f"/predictions#{p['id']}",
            }
        )
    srcs = {s["id"]: s for s in outlook.get("sources") or []}
    facts = outlook.get("facts") or {}
    for c in outlook.get("claims") or []:
        t = _test(c.get("test"))
        out.append(
            {
                "id": c["id"],
                "kind": "outlook",
                "folio": c["folio"],
                "stage": c.get("stage"),
                "row": c.get("row"),
                "who": _who(c, srcs),
                "attribution": c["attribution"],
                "line": c["text"],
                "state": c["state"],
                "settles": c.get("due") or c.get("falsifier"),
                "test": t,
                "reading": facts.get(t["fact"]) if t else None,
                "sources": [srcs[h]["url"] for h in c.get("holders") or [] if h in srcs],
                "href": f"/outlook#claim-{c['id']}",
            }
        )
    mig = argument.get("migration") or {}
    for p in mig.get("predictions") or []:
        m = spec["migration"].get(p["id"])
        if not m:
            continue
        out.append(
            {
                "id": p["id"],
                "kind": "migration",
                "folio": m["folio"],
                "who": "This site",
                "attribution": "site",
                "line": p["claim"],
                "state": p["state"],
                "settles": None,
                "test": None,
                "reading": (mig.get("facts") or {}).get(p.get("fact")) if p.get("fact") else None,
                "sources": [],
                "href": "/argument/migration",
            }
        )
    state = {v["id"]: v["state"] for v in verdicts}
    for e in exits:
        x = spec["exits"].get(e["monitor"])
        if not x:
            continue
        out.append(
            {
                "id": e["monitor"],
                "kind": "exit",
                "folio": x["folio"],
                "who": "This site",
                "attribution": "site",
                "line": e["label"],
                "state": state.get(e["monitor"], "untestable"),
                "settles": e["text"],
                "test": None,
                "reading": None,
                "sources": [],
                "href": "/#exits",
            }
        )
    for r in out:
        r["word"] = WORDS[r["kind"]][r["state"]]
    return out


def build(
    spec: dict[str, Any],
    ledger: list[dict[str, Any]],
    outlook: dict[str, Any],
    argument: dict[str, Any],
    verdicts: list[dict[str, Any]],
    exits: list[dict[str, Any]],
    cards: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rs = rows(spec, ledger, outlook, argument, verdicts, exits)
    rank = {w: i for i, w in enumerate(ORDER)}
    return {
        "as_of": outlook.get("as_of"),
        "words": [{"id": w, **spec["words"][w]} for w in ORDER],
        "mapping": [
            {"kind": k, "state": s or "none", "word": w} for k, m in WORDS.items() for s, w in m.items()
        ],
        "tally": {w: sum(1 for r in rs if r["word"] == w) for w in ORDER},
        "folios": [
            {
                **f,
                "rows": sorted(
                    (r for r in rs if r["folio"] == f["id"]), key=lambda r: (rank[r["word"]], r["kind"], r["id"])
                ),
                "too_early": sum(1 for r in rs if r["folio"] == f["id"] and r["word"] == "too_early"),
            }
            for f in spec["folios"]
        ],
        "questions": [
            {
                **q,
                "status": (cards.get(q["indicator"]) or {}).get("status") if q.get("indicator") else None,
                "href": f"/indicators/{q['indicator']}" if q.get("indicator") else None,
            }
            for q in spec["questions"]
        ],
    }


def problems(
    spec: dict[str, Any], ledger_ids: set[str], migration_ids: set[str], monitors: set[str], published: set[str]
) -> list[str]:
    errors = []
    folios = {f["id"] for f in spec["folios"]}
    for group, known in (("ledger", ledger_ids), ("migration", migration_ids), ("exits", monitors)):
        for k, v in spec[group].items():
            if k not in known:
                errors.append(f"board: {group} entry {k} names nothing on the site")
            if v.get("folio") not in folios:
                errors.append(f"board: {group} entry {k} has an unknown folio")
    for k in published - set(spec["ledger"]):
        errors.append(f"board: ledger prediction {k} has no line on the board")
    if set(spec["words"]) != set(ORDER):
        errors.append("board: every status word needs a label and a meaning")
    return errors
