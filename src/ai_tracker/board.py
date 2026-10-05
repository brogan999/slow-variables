"""Every prediction on the site in one list: other people's dated claims (the ledger), the outlook's tested claims,
the migration page's predictions and the home page's exits, each with one plain status word. Pure over built dicts,
so the export and the query service share it and tests need no store."""

from __future__ import annotations

import re
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
    "outlook": {
        "holding": "happening",
        "failing": "not_happening",
        "both": "both",
        "untestable": "too_early",
    },
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
JUDGEMENTS = Path("seed/board_judgements.yaml")
# A reason names the reading it rests on and the page links to it, so it types no figure, no size word and no address.
FIGURE = re.compile(
    r"\d|https?://|www\.|\b(half|halves|twice|thrice|doubl\w*|tripl\w*|quadrupl\w*|halv\w*|percent|per cent|fifths?|tenths?"
    r"|hundreds?|thousands?|millions?|billions?|trillions?|dozens?|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen"
    r"|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)\b|-fold\b",
    re.I,
)
YEAR = re.compile(r"\b(19|20|21)\d\d\b")


def judgements() -> dict[str, Any]:
    """A model's lean on forecasts no reading can yet test: its own file, read by no status logic (plan Part 39)."""
    return (yaml.safe_load(JUDGEMENTS.read_text()) or {}) if JUDGEMENTS.exists() else {}


def judgement_problems(doc: dict[str, Any], known: set[tuple[str, str]], indicator_ids: set[str], leans: set[str]) -> list[str]:
    errors, seen = [], set()
    made = doc.get("made_by") or {}
    for k in ("model", "date", "method", "reviewed_by"):
        if not made.get(k):
            errors.append(f"board judgements: made_by has no {k}")
    for j in doc.get("judgements") or []:
        key = (j.get("kind"), j.get("id"))
        where = f"board judgement {key[0]}/{key[1]}"
        if key not in known:
            errors.append(f"{where} names no forecast on the board")
        if key in seen:
            errors.append(f"{where} is given twice")
        seen.add(key)
        if j.get("lean") not in leans:
            errors.append(f"{where} has an unknown lean {j.get('lean')}")
        reason = (j.get("reason") or "").strip()
        if not reason:
            errors.append(f"{where} gives no reason")
        elif FIGURE.search(YEAR.sub("", reason)):
            errors.append(f"{where}: its reason types a figure, a size word or an address")
        for i in j.get("rests_on") or []:
            if i not in indicator_ids:
                errors.append(f"{where} rests on unknown indicator {i}")
    return errors


def load() -> dict[str, Any]:
    return yaml.safe_load(SPEC.read_text())


def _who(c: dict[str, Any], sources: dict[str, dict[str, Any]]) -> str:
    names = list(
        dict.fromkeys(
            sources[h].get("short") or sources[h]["who"] for h in c.get("holders") or [] if h in sources
        )
    )
    if c.get("attribution") == "site" or not names:
        return "This site"
    lead = " and ".join(names)
    return f"This site, extending {lead}" if c.get("attribution") == "extension" else lead


def _indicator(f: dict[str, Any] | None) -> list[str]:
    """The indicator a reading belongs to: a fact links to its published indicator's page when it has one."""
    href = (f or {}).get("href") or ""
    return [href.split("/indicators/", 1)[1]] if href.startswith("/indicators/") else []


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
                "line": lines[p["id"]].get("line") or p["claim_text"],  # the singularity ledger is already in the site's words
                "state": p.get("status"),
                "settles": p.get("window_end"),
                "test": None,
                "reading": None,
                "sources": [p["claim_url"]] if p.get("claim_url") else [],
                "indicators": list(p.get("related_indicators") or []),
                "href": f"/predictions#{p['id']}",
            }
        )
    srcs = {s["id"]: s for s in outlook.get("sources") or []}
    facts = outlook.get("facts") or {}
    for c in outlook.get("claims") or []:
        t = _test(c.get("test"))
        f = facts.get(t["fact"]) if t else None
        out.append(
            {
                "id": c["id"],
                "kind": "outlook",
                "folio": (spec.get("folio_overrides") or {}).get(c["id"], c["folio"]),
                "stage": c.get("stage"),
                "row": c.get("row"),
                "who": _who(c, srcs),
                "attribution": c["attribution"],
                "line": c["text"],
                "state": c["state"],
                "settles": c.get("due") or c.get("falsifier"),
                "test": t,
                "reading": f,
                "sources": [srcs[h]["url"] for h in c.get("holders") or [] if h in srcs],
                "indicators": _indicator(f) + list((spec.get("claim_indicators") or {}).get(c["id"]) or []),
                "href": f"/outlook#claim-{c['id']}",
            }
        )
    mig = argument.get("migration") or {}
    for p in mig.get("predictions") or []:
        m = spec["migration"].get(p["id"])
        if not m:
            continue
        f = (mig.get("facts") or {}).get(p.get("fact")) if p.get("fact") else None
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
                "reading": f,
                "sources": [],
                "indicators": _indicator(f),
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
                "indicators": list(x.get("indicators") or []),
                "href": "/argument#exits",
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
    judged: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rs = rows(spec, ledger, outlook, argument, verdicts, exits)
    rank = {w: i for i, w in enumerate(ORDER)}
    # A lean attaches only while the row is still too early: once a reading settles it, the lean is dropped, not kept.
    leans = {(j["kind"], j["id"]): j for j in (judged or {}).get("judgements") or []}
    for r in rs:
        j = leans.get((r["kind"], r["id"]))
        if j and r["word"] == "too_early":
            r["judgement"] = {
                "lean": j["lean"], "reason": j["reason"],
                "rests_on": [{"id": i, "name": (cards.get(i) or {}).get("name") or i, "href": f"/indicators/{i}"} for i in j.get("rests_on") or []],
            }  # fmt: skip
    order = list(spec.get("leans") or {})
    count = lambda rows_: {w: n for w in order if (n := sum(1 for r in rows_ if (r.get("judgement") or {}).get("lean") == w))}  # noqa: E731
    extra = {}
    if judged:
        extra = {
            "leans": [{"id": w, **spec["leans"][w]} for w in order],
            "judged": {**judged["made_by"], "date": str(judged["made_by"]["date"]), "tally": {w: count(rs).get(w, 0) for w in order}},
        }
    return {
        **extra,
        "as_of": outlook.get("as_of"),
        "words": [{"id": w, **spec["words"][w]} for w in ORDER],
        "mapping": [
            {"kind": k, "state": s or "none", "word": w} for k, m in WORDS.items() for s, w in m.items()
        ],
        "n": len(rs),
        "tally": {w: sum(1 for r in rs if r["word"] == w) for w in ORDER},
        "folios": [
            {
                **f,
                "rows": sorted(
                    (r for r in rs if r["folio"] == f["id"]),
                    key=lambda r: (rank[r["word"]], r["kind"], r["id"]),
                ),
                "too_early": sum(1 for r in rs if r["folio"] == f["id"] and r["word"] == "too_early"),
                **({"leans": count([r for r in rs if r["folio"] == f["id"]])} if judged else {}),
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
    spec: dict[str, Any],
    ledger_ids: set[str],
    migration_ids: set[str],
    monitors: set[str],
    published: set[str],
    claim_ids: set[str] | None = None,
    indicator_ids: set[str] | None = None,
) -> list[str]:
    errors = []
    folios = {f["id"] for f in spec["folios"]}
    for group, known in (("ledger", ledger_ids), ("migration", migration_ids), ("exits", monitors)):
        for k, v in spec[group].items():
            if k not in known:
                errors.append(f"board: {group} entry {k} names nothing on the site")
            if v.get("folio") not in folios:
                errors.append(f"board: {group} entry {k} has an unknown folio")
    for k, v in (spec.get("folio_overrides") or {}).items():
        if claim_ids is not None and k not in claim_ids:
            errors.append(f"board: folio override {k} names no outlook claim")
        if v not in folios:
            errors.append(f"board: folio override {k} names an unknown folio")
    for k, v in (spec.get("claim_indicators") or {}).items():
        if claim_ids is not None and k not in claim_ids:
            errors.append(f"board: claim_indicators names no outlook claim {k}")
        for i in v:
            if indicator_ids is not None and i not in indicator_ids:
                errors.append(f"board: claim {k} names an unknown indicator {i}")
    for k, v in spec["exits"].items():
        for i in v.get("indicators") or []:
            if indicator_ids is not None and i not in indicator_ids:
                errors.append(f"board: exit {k} names an unknown indicator {i}")
    for k in published - set(spec["ledger"]):
        errors.append(f"board: ledger prediction {k} has no line on the board")
    if set(spec["words"]) != set(ORDER):
        errors.append("board: every status word needs a label and a meaning")
    return errors
