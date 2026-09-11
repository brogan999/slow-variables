"""Weekly memo (v2 §6.2): deterministic facts since the last memo, prose from a model when a key exists, checked
by citecheck, else the deterministic digest. Output is a markdown file with YAML front matter under docs/memos/;
`export` turns the folder into web/data/memos/*.json. Nothing here writes observations or statuses.
"""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import yaml

from . import store as st
from .query.ask import Tools
from .query.citecheck import CITE, check

log = logging.getLogger("ai-tracker.memo")
MEMOS = Path("docs/memos")
MODEL = os.environ.get("MEMO_MODEL", "claude-fable-5-1")
PROMPT_VERSION = "1"
SIGN = {"faster_than_normal": 1, "concentrating": 1, "slower_than_normal": -1, "dispersing": -1}


def load_memos() -> list[dict[str, Any]]:
    out = []
    for p in sorted(MEMOS.glob("*.md")):
        m = re.match(r"---\n(.*?)\n---\n(.*)", p.read_text(), re.S)
        if not m:
            continue
        fm = yaml.safe_load(m.group(1)) or {}
        out.append({**fm, "date": str(fm.get("date", p.stem)), "body": m.group(2).strip()})
    return out


RANK = {"leading": 0, "coincident": 1, "lagging": 2}


def facts(store: st.Store, since: date, today: date) -> dict[str, Any]:
    names = {i.id: i.name for i in store.seed.indicators} | {
        p.id: p.claim_text[:80] for p in store.seed.predictions
    }
    # P1 §8: leading indicators first, then coincident, then lagging; predictions after indicators
    lead = {
        i.id: RANK.get(i.leading_lagging.value if i.leading_lagging else "", 3) for i in store.seed.indicators
    }
    events = [
        {**st.dump(e), "name": names.get(e.target_id, e.target_id)}
        for e in sorted(store.events, key=lambda e: (lead.get(e.target_id, 4), e.created_at))
        if since <= e.created_at.date() <= today
    ]
    cur = store.con.execute(
        "SELECT id, series_key, source_id, value_text, url, as_of_date FROM observations "
        "WHERE substr(retrieved_at, 1, 10) >= ? ORDER BY retrieved_at",
        [since.isoformat()],
    )
    new = [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
    new_ids = {r["id"] for r in new}
    by_indicator = []
    for ind in store.seed.indicators:
        if not ind.published:
            continue
        ids = [o["id"] for o in store.evidence_obs(ind) if o["id"] in new_ids]
        if not ids:
            continue
        pts = store.headline(ind)
        drows = store.derived_for(ind.metric, ind.metric_dims) if ind.metric else []
        by_indicator.append(
            {
                "id": ind.id,
                "name": ind.name,
                "leading_lagging": ind.leading_lagging.value if ind.leading_lagging else None,
                "unit": ind.unit,
                "new": len(ids),
                "latest": pts[-1] if pts else None,
                "derived_id": drows[-1].id if drows else None,
            }
        )
    by_indicator.sort(key=lambda r: (lead.get(r["id"], 3), r["name"]))
    by_source: dict[str, int] = {}
    for r in new:
        by_source[r["source_id"]] = by_source.get(r["source_id"], 0) + 1
    watch = [
        {
            "as_of": r["as_of_date"].isoformat(),
            "source": r["source_id"],
            "text": (r["value_text"] or "")[:200],
            "url": r["url"],
            "id": r["id"],
        }
        for r in new
        if r["series_key"].startswith("watch.")
    ]
    stale = [
        {"id": c["id"], "name": c["name"], "stale_as_of": c["stale_as_of"]}
        for c in (store._card(i) for i in store.seed.indicators if i.published)
        if c["stale_as_of"]
    ]
    tpath = st.DATA / "thesis.jsonl"
    thesis = {v["name"]: v["holds"] for v in st.read_jsonl(tpath)} if tpath.exists() else {}
    prev = load_memos()
    prev_thesis = (prev[-1].get("thesis") or {}) if prev else {}
    thesis_changes = {
        k: (prev_thesis.get(k), v) for k, v in thesis.items() if k in prev_thesis and prev_thesis.get(k) != v
    }
    opposing = []
    for row in store.seed.crosswalk:
        b = [
            e
            for e in events
            if any(i.id == e["target_id"] and i.bucket_id == row.bucket_id for i in store.seed.indicators)
        ]
        ly = [
            e
            for e in events
            if any(i.id == e["target_id"] and i.layer_id == row.layer_id for i in store.seed.indicators)
        ]
        sb = {SIGN.get(e["new_status"], 0) for e in b} - {0}
        sl = {SIGN.get(e["new_status"], 0) for e in ly} - {0}
        if sb and sl and sb != sl:
            opposing.append(
                {
                    "bucket_id": row.bucket_id,
                    "layer_id": row.layer_id,
                    "bucket_events": [e["target_id"] for e in b],
                    "layer_events": [e["target_id"] for e in ly],
                }
            )
    lens = {}
    for name in ("diffusion", "capture"):
        p = st.WEB / "lens" / f"{name}.json"
        lens[name] = json.loads(p.read_text()).get("verdict", "") if p.exists() else ""
    return {
        "since": since.isoformat(),
        "date": today.isoformat(),
        "events": events,
        "new_observations": len(new),
        "by_source": dict(sorted(by_source.items(), key=lambda kv: -kv[1])),
        "by_indicator": by_indicator,
        "watchlist": watch,
        "stale": stale,
        "thesis": thesis,
        "thesis_changes": thesis_changes,
        "opposing_crosswalk": opposing,
        "lens": lens,
    }


def _val(p: dict[str, Any] | None, unit: str, derived_id: str | None = None) -> str:
    """A value the way the site renders it, followed by the token of the record that carries it."""
    if not p or p.get("value") is None:
        return "unmeasured"
    v = p["value"]
    if unit == "share":
        s = f"{v * 100:.1f}%"
    elif unit in ("USD", "usd") and abs(v) >= 1e6:
        d, suf = (v / 1e12, "T") if abs(v) >= 1e12 else (v / 1e9, "B") if abs(v) >= 1e9 else (v / 1e6, "M")
        s = f"${d:.1f}{suf}"
    elif unit == "ratio":
        s = f"{v:.3g}×"
    elif unit == "minutes" and v >= 60:
        s = f"{v / 60:.1f} h"
    elif unit == "year":
        s = f"{v:.0f}"
    else:
        s = f"{v:,.0f}" if abs(v) >= 1e3 else f"{v:.3g}"
    ids = f"[derived:{derived_id}]" if derived_id else " ".join(f"[obs:{i}]" for i in p.get("obs_ids", []))
    return f"{s} as of {p['as_of']} {ids}".strip()


def digest(f: dict[str, Any]) -> str:
    """Deterministic memo: ids rather than names (names carry numbers), every number followed by its record's token."""
    w = {True: "holds", False: "does not hold", None: "untestable"}
    opener = (
        " ".join(x for x in (f["lens"].get("diffusion"), f["lens"].get("capture")) if x)
        or "What moved this week, from the store."
    )
    out = [opener]
    out.append("\n## What changed\n")
    if f["events"]:
        for e in f["events"]:
            out.append(
                f"- **{e['target_id']}**: {(e['old_status'] or 'unmeasured').replace('_', ' ')} → "
                f"{e['new_status'].replace('_', ' ')}, confidence {e['new_conf']} [ind:{e['target_id']}], by {e['author']} "
                f"on {e['created_at'][:10]}; the reason is in the changelog [event:{e['id']}]."
            )
    else:
        out.append("No status changed this week.")
    out.append("\n## New evidence\n")
    if f["by_indicator"]:
        for i in f["by_indicator"]:
            out.append(
                f"- {i['id']}: new observations; latest {_val(i['latest'], i['unit'], i['derived_id'])} [ind:{i['id']}]"
            )
    else:
        out.append("No published indicator received new observations.")
    out.append("\n## Watchlist\n")
    if f["watchlist"]:
        out.extend(
            f"- {x['as_of']} {x['source']}: {x['text']} ({x['url']}) [obs:{x['id']}]" for x in f["watchlist"]
        )
    else:
        out.append("No new watchlist posts.")
    out.append("\n## Thesis monitor\n")
    out.extend(
        f"- {k.replace('_', ' ')}: {w[v]}"
        + (f" (was {w[f['thesis_changes'][k][0]]})" if k in f["thesis_changes"] else "")
        for k, v in f["thesis"].items()
    )
    out.append("\n## Crosswalk\n")
    if f["opposing_crosswalk"]:
        out.extend(
            f"- {o['bucket_id']} ⇄ {o['layer_id']} moved in opposite directions: {', '.join(o['bucket_events'])} versus {', '.join(o['layer_events'])}"
            for o in f["opposing_crosswalk"]
        )
    else:
        out.append("No crosswalk pair moved in opposite directions.")
    if f["stale"]:
        out.append("\n## Stale\n")
        out.extend(f"- {s['name']} ({s['id']}): last point {s['stale_as_of']}" for s in f["stale"])
    out.append("\n## Lens sentences\n")
    out.append(f"Diffusion: {f['lens'].get('diffusion', '')}\n\nCapture: {f['lens'].get('capture', '')}")
    return "\n".join(out)


PROMPT = """You write the weekly memo for an AI diffusion and value-capture tracker. Given the observations and evidence added since {since}, which indicators changed status or would under the band and direction rules? Which crosswalk pairs moved in opposite directions? Draft the memo, the L0 sentences for both lenses, and note the changelog entries.

Rules: use only the facts below; never introduce a number that is not in them. Every number must be followed by the citation token given with it ([obs:...], [derived:...], [ind:...] or [event:...]); a status is cited with [ind:<id>]. Under 450 words. Markdown with these sections: an opening paragraph, "## What changed", "## New evidence", "## Watchlist", "## Thesis monitor", "## Crosswalk", and last "## Lens sentences" containing exactly two lines "Diffusion: ..." and "Capture: ...". Fast is not good and concentrating is not good; say what moved and what it means for the normal-technology reading, nothing more. Facts are ordered leading indicators first; lead with what moved among them, since they move before the coincident and lagging ones.

Facts (JSON):
{facts}
"""


def prose(f: dict[str, Any], tools: Tools) -> tuple[str | None, str | None]:
    """Model-written memo, or (None, why) when there is no key or the citation check fails twice."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None, "no ANTHROPIC_API_KEY"
    import anthropic

    client = anthropic.Anthropic()
    msgs: list[dict[str, Any]] = [
        {"role": "user", "content": PROMPT.format(since=f["since"], facts=json.dumps(f, default=str)[:60000])}
    ]
    for attempt in range(2):
        try:
            r = client.messages.create(model=MODEL, max_tokens=1800, messages=msgs)
        except anthropic.APIError as e:  # an outage or a spent limit still yields a memo PR (the digest)
            return None, f"model error ({type(e).__name__})"
        text = "".join(b.text for b in r.content if b.type == "text")
        res = check(text, tools.records(CITE.findall(text)))
        if res.ok:
            return text, None
        msgs += [
            {"role": "assistant", "content": text},
            {
                "role": "user",
                "content": "Citation check failed:\n"
                + "\n".join(f"- {x}" for x in res.failures)
                + "\nRevise so every number is followed by the token of a record that contains it, or drop the number. Reply with the memo only.",
            },
        ]
        log.warning("memo attempt %d failed citecheck: %s", attempt + 1, res.failures[:5])
    return None, "citation check failed twice"


def write(store: st.Store, today: date | None = None, since: date | None = None) -> Path:
    today = today or date.today()
    prev = load_memos()
    if prev and prev[-1]["date"] == today.isoformat():
        log.info("memo for %s already exists; not rewriting it", today)
        return MEMOS / f"{today.isoformat()}.md"
    since = since or (
        date.fromisoformat(prev[-1]["date"]) + timedelta(days=1) if prev else today - timedelta(days=7)
    )
    f = facts(store, since, today)
    body, why = prose(f, Tools(store))
    mode = "prose" if body else "digest"
    if not body:
        log.info("memo falls back to the digest: %s", why)
        body = digest(f)
    lens = dict(f["lens"])
    for line in body.splitlines():
        m = re.match(r"\s*(Diffusion|Capture):\s*(.+)", line)
        if m:
            lens[m.group(1).lower()] = m.group(2).strip()
    fm = {
        "date": today.isoformat(),
        "since": since.isoformat(),
        "title": f"Week to {today.strftime('%-d %B %Y')}",
        "mode": mode,
        "model": MODEL if mode == "prose" else None,
        "prompt_version": PROMPT_VERSION,
        "fallback_reason": why,
        "thesis": f["thesis"],
        "lens": lens,
        "events": len(f["events"]),
        "new_observations": f["new_observations"],
        "by_source": f["by_source"],
    }
    MEMOS.mkdir(parents=True, exist_ok=True)
    p = MEMOS / f"{today.isoformat()}.md"
    p.write_text(
        "---\n" + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True) + "---\n\n" + body.strip() + "\n"
    )
    return p


REFRESH_NOTES = {
    "revelio": "Revelio's terms forbid automated access: take the figure from a Wayback snapshot"
}


def due_for_refresh(store: st.Store, today: date) -> list[str]:
    """Hand-entered series behind a published indicator whose newest row is older than twice its source's cadence."""
    from fnmatch import fnmatch

    import yaml

    metrics = (yaml.safe_load(Path("semantic/metrics.yaml").read_text()) or {})["metrics"]
    globs = {
        g
        for i in store.seed.indicators
        if i.published
        for g in [*i.series_keys, *((metrics.get(i.metric) or {}).get("inputs", []) if i.metric else [])]
    }
    cadence = {x.id: (x.name, x.cadence) for x in store.seed.sources}
    rows = store.con.execute(
        "SELECT series_key, arg_max(source_id, as_of_date), max(as_of_date), arg_max(url, as_of_date), "
        "arg_max(extraction_method, as_of_date) FROM observations GROUP BY series_key ORDER BY series_key"
    ).fetchall()
    out = []
    for key, src, as_of, url, method in rows:
        name, cad = cadence.get(src, (src, None))
        days = st.CADENCE_DAYS.get(cad or "")
        if (
            method != "manual" or not days or cad == "per_release" or not any(fnmatch(key, g) for g in globs)
        ):  # a one-off study is not due
            continue
        if (today - as_of).days > 2 * days:
            note = f" ({REFRESH_NOTES[src]})" if src in REFRESH_NOTES else ""
            out.append(f"- `{key}` ({name}, {cad}): newest {as_of}; {url}{note}")
    return out


def ops_notes(store: st.Store, today: date | None = None) -> str:
    """Operator notes for the memo PR body: what needs the maintainer this week. Everything here is already
    public in the repo or on /sources; nothing is written to docs/memos."""
    from .cli import attention
    from .ingest.connectors import (
        CONNECTORS,
    )  # a retired connector's source stays on /sources, not in the weekly notes

    today = today or date.today()
    week = [fl for fl in store.fetchlog if (today - fl.finished_at.date()).days < 7]
    memo = (load_memos() or [{}])[-1]
    lead = (
        [
            f"- The memo fell back to the digest: {memo['fallback_reason']}. If that is a model error, Ask is down too."
        ]
        if memo.get("date") == today.isoformat() and memo.get("fallback_reason")
        else []
    )
    last = max((fl.finished_at for fl in store.fetchlog), default=None)
    lead.append(f"- Newest fetch on main: {last.date() if last else 'never'}.")
    blank = [
        p for p in st.read_jsonl(st.DATA / "proposed_status_events.jsonl") if not p.get("reason", "").strip()
    ]
    layout = sorted({fl.source_id for fl in week if not fl.ok and "LayoutChanged" in (fl.error or "")})
    nights: dict[str, set[date]] = {}
    for fl in week:
        if (
            not fl.ok and fl.source_id not in layout and "not set" not in (fl.error or "")
        ):  # a missing key is a choice
            nights.setdefault(fl.source_id, set()).add(fl.finished_at.date())
    health = [store._source_health(s) for s in store.seed.sources]
    sections = {
        "Band crossings waiting for a reason (tell Claude, or write it on main)": [
            f"- `{p['target_id']}`: {(p.get('old_status') or 'unscored').replace('_', ' ')} → "
            f"{p['new_status'].replace('_', ' ')}, waiting {(today - date.fromisoformat(p['created_at'][:10])).days} days"
            for p in blank
        ],
        "Attention from check": [f"- {n}" for n in attention(store) if "waited" not in n],
        "Layout changes this week (an issue is open for each)": [f"- `{s}`" for s in layout],
        "Connectors failing 3+ of the last 7 nights": [
            f"- `{k}`: {len(v)} nights" for k, v in sorted(nights.items()) if len(v) >= 3
        ],
        "Hand-entered series due for a refresh (fetch the page, add a row to seed/manual_observations.yaml)": due_for_refresh(
            store, today
        ),
        "Sources stale or never fetched": [
            f"- `{h['id']}`: {h['health']}, last success {str(h['last_success_at'] or 'never')[:10]}"
            for h in health
            if h["health"] != "ok"
            and "not set" not in (h["last_error"] or "")
            and h["connector"] in CONNECTORS
        ],
    }
    return (
        "## Operator notes\n\n"
        + "\n".join(lead)
        + "\n"
        + "".join(f"\n**{k}**\n\n" + "\n".join(v or ["- none"]) + "\n" for k, v in sections.items())
    )
