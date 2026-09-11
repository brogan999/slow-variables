"""ai-tracker ingest | build | evaluate | export | check | approve"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import date, datetime, timezone

from . import store as st
from .analysis.bands import flow_status
from .analysis.direction import direction
from .analysis.metrics import run_metrics
from .ingest.connectors import CONNECTORS
from .schema import UNSCORED, FetchLog, Indicator, StatusEvent, Tier
from .thesis import render_md, run_all

log = logging.getLogger("ai-tracker")


def cmd_ingest(a: argparse.Namespace) -> int:
    names = list(CONNECTORS) if a.all else a.source
    rc = 0
    for name in names:
        try:  # a connector that crashes outside its own run() still logs a failure and never stops the others
            rows, fl = CONNECTORS[name]().run(a.day, a.refetch)
            fl.items_new = st.append_observations(name, rows) if rows else 0
        except Exception as e:  # noqa: BLE001
            now = datetime.now(timezone.utc)
            fl = FetchLog(source_id=name, started_at=now, finished_at=now, ok=False, error=repr(e)[:500])
        st.append_fetchlog(fl)
        optional = CONNECTORS[name].optional and not fl.ok
        print(
            f"{name}: ok={fl.ok} found={fl.items_found} new={fl.items_new}"
            + (f" error={fl.error}" if fl.error else "")
            + (
                " (optional source; run continues, series will read stale until it recovers)"
                if optional
                else ""
            )
        )
        rc |= int(not fl.ok and not CONNECTORS[name].optional)
    return rc


def cmd_build(a: argparse.Namespace) -> int:
    s = st.Store()
    n = s.con.execute("SELECT count(*) FROM observations").fetchone()[0]
    print(
        f"{len(s.seed.indicators)} indicators, {len(s.seed.sources)} sources, {n} approved observations, "
        f"{len(s.derived)} derived, {len(s.events)} status events"
    )
    return 0


PRIMARY = {Tier.BENCHMARK, Tier.MODEL_RELEASE, Tier.OFFICIAL_FILING}


def _single_non_primary(s: st.Store, ind: Indicator) -> bool:
    """A scored status needs two sources, or one primary (benchmark, model release, official filing)."""
    obs = s.evidence_obs(ind)
    return len({o["source_id"] for o in obs}) < 2 and not ({Tier(o["tier"]) for o in obs} & PRIMARY)


def _fmt(v: float, unit: str) -> str:
    if unit in ("USD", "usd") and abs(v) >= 1e6:
        d, suf = (v / 1e12, "T") if abs(v) >= 1e12 else (v / 1e9, "B") if abs(v) >= 1e9 else (v / 1e6, "M")
        return f"${d:.1f}{suf}"
    if unit == "share":
        return f"{v * 100:.1f}%"
    return f"{v:,.0f}" if abs(v) >= 1e4 else f"{v:.4g}"


def _auto_reason(
    s: st.Store, ind: Indicator, value: float | None, as_of, new: str, old: str | None, ids: list[str]
) -> str:
    """A machine-written reason only for a first scoring inside a band; band crossings wait for a human."""
    if old not in (None, *UNSCORED) or new in UNSCORED or value is None:
        return ""
    src = (
        s.con.execute("SELECT source_id FROM observation_all WHERE id = ?", [ids[0]]).fetchone()
        if ids
        else None
    )
    name = next((x.name for x in s.seed.sources if src and x.id == src[0]), src[0] if src else "?")
    if ind.direction_rule:
        r = ind.direction_rule
        return (
            f"Evaluator: {_fmt(value, ind.unit)} ({name}, {as_of}) reads {new.replace('_', ' ')} over {r.periods} periods with a "
            f"dead band of {r.dead_band:g}. Auto-reason; rule rationale: {r.rationale}"
        )
    band = ind.normal_band if new == "consistent_with_normal" else ind.fast_band
    edge = f"lo={_fmt(band.lo, ind.unit)}" if band and band.lo is not None else ""
    edge += (" " if edge else "") + (f"hi={_fmt(band.hi, ind.unit)}" if band and band.hi is not None else "")
    return (
        f"Evaluator: {_fmt(value, ind.unit)} ({name}, {as_of}) is inside the {new.replace('_', ' ').replace(' with normal', '')} "
        f"band ({edge}). Auto-reason; band rationale: {ind.band_rationale}"
    )


def _propose_predictions(s: st.Store, proposed: list[dict], seen: set, lines: list[str]) -> None:
    today = date.today()
    for pr in s.seed.predictions:
        if not pr.published:
            continue
        cur = s.current(pr.id)
        status = cur.new_status if cur else None
        new = None
        if pr.window_start and pr.window_start > today and status != "not_yet_testable":
            new = "not_yet_testable"
        elif pr.window_end and pr.window_end < today and status not in ("confirmed", "ahead", "behind"):
            new = "behind"
        if new and (pr.id, new) not in seen:
            ev = StatusEvent(
                target_type="prediction",
                target_id=pr.id,
                old_status=status,
                new_status=new,
                old_conf=cur.new_conf if cur else None,
                new_conf=cur.new_conf if cur else pr.confidence,
                reason="",
                evidence_ids=[],
                author="evaluate",
                created_at=datetime.now(timezone.utc),
            )
            proposed.append(st.dump(ev))
            lines.append(
                f"prediction {pr.id}: window says {new}; proposed StatusEvent {ev.id} needs a reason"
            )


def _drop_stale(proposed: list[dict], tonight: dict[str, str]) -> list[dict]:
    """A blank proposal the evaluator no longer holds is not a to-do, and a late reason must not commit it."""
    return [
        p
        for p in proposed
        if p.get("reason", "").strip() or tonight.get(p["target_id"], p["new_status"]) == p["new_status"]
    ]


def cmd_evaluate(a: argparse.Namespace) -> int:
    s = st.Store()
    derived = run_metrics(s.con)
    st.write_jsonl(st.DATA / "derived.jsonl", [st.dump(d) for d in derived])
    s.derived = derived
    s.semantic_tables()
    proposed = st.read_jsonl(st.DATA / "proposed_status_events.jsonl")
    seen = {(p["target_id"], p["new_status"]) for p in proposed}
    lines = [f"derived: {len(derived)} rows across {len({d.metric for d in derived})} metrics"]
    tonight: dict[str, str] = {}
    for ind in s.seed.indicators:
        if not ind.published:
            continue
        value, as_of, ids, tier = s.band_input(ind)
        if ind.direction_rule:
            pts = [
                (date.fromisoformat(p["as_of"]), p["value"])
                for p in s.headline(ind)
                if p["value"] is not None
            ]
            new = direction(pts, ind.direction_rule, tier).value
        else:
            new = flow_status(value, ind.normal_band, ind.fast_band, ind.falsifying_band, tier).value
        capped = new not in UNSCORED and _single_non_primary(s, ind)
        if capped:  # the two-source rule, applied at proposal time rather than only at the gate
            new = "emerging"
        tonight[ind.id] = new
        cur = s.current(ind.id)
        old = cur.new_status if cur else None
        lines.append(
            f"{ind.id}: input={value!r} as_of={as_of} tier={int(tier)} -> {new} (current: {old})"
            + (" [capped: single non-primary source]" if capped else "")
        )
        if ind.override_note:  # v2 §10: a status held by a published override note is never re-proposed
            proposed = [p for p in proposed if p["target_id"] != ind.id]
            lines.append(f"  held by its override note: {ind.override_note}")
            continue
        if not ids and ind.direction_rule:  # a direction reading rests on the window it compared
            ids = sorted(
                {i for p in s.headline(ind)[-(ind.direction_rule.periods + 1) :] for i in p["obs_ids"]}
            )
        if new != old and ids and (ind.id, new) not in seen and (value is not None or ind.direction_rule):
            ev = StatusEvent(
                target_id=ind.id,
                old_status=old,
                new_status=new,
                old_conf=cur.new_conf if cur else None,
                new_conf=cur.new_conf if cur else ind.confidence,
                reason=_auto_reason(s, ind, value, as_of, new, old, ids),
                evidence_ids=ids,
                author="evaluate",
                created_at=datetime.now(timezone.utc),
            )
            proposed.append(st.dump(ev))
            lines.append(
                f"  proposed StatusEvent {ev.id}: "
                + (
                    "auto-reason written"
                    if ev.reason
                    else "fill `reason` in data/proposed_status_events.jsonl or delete the row"
                )
            )
    proposed = _drop_stale(proposed, tonight)
    _propose_predictions(s, proposed, seen, lines)
    st.write_jsonl(st.DATA / "proposed_status_events.jsonl", proposed)
    verdicts = run_all(s)
    st.write_jsonl(
        st.DATA / "thesis.jsonl",
        [
            {
                "id": v.id,
                "name": v.name,
                "holds": v.holds,
                "logic": v.logic,
                "conds": [
                    {"text": c.text, "holds": c.holds, "obs_ids": c.obs_ids, "detail": c.detail}
                    for c in v.conds
                ],
            }
            for v in verdicts
        ],
    )
    (st.Path("docs") / "thesis.md").write_text(render_md(verdicts, date.today()))
    lines += [
        f"thesis {v.id}: {({True: 'HOLDS', False: 'no', None: 'untestable'})[v.holds]}" for v in verdicts
    ]
    summary = "\n".join(lines)
    print(summary)
    (st.DATA / "summary.md").write_text(
        f"# evaluate {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z\n\n```\n{summary}\n```\n"
        + _suggested_enrichment(s)
    )
    return 0


def _suggested_enrichment(s: st.Store) -> str:
    """Free lookups only (v2 M6): Form D issuers that match a seed alias without a CIK, and watchlist posts that link
    to a non-X artifact. Paid enrichment (Explorium, Swarm, Clay) stays in the operator's own session."""
    from .ingest.connectors.formd import FormD

    lines = []
    try:
        c = FormD()
        for r in c.candidates(c.fetch(date.today(), False)):
            lines.append(
                f'- entities.yaml `{r["entity"]}`: Form D issuer "{r["issuer"]}" CIK {r["cik"]} ({r["city"]}, {r["state"]}); add `cik` if it is the same company'
            )
    except Exception as e:  # noqa: BLE001 - no Form D cache today is not an error
        lines.append(f"- Form D candidates unavailable today ({type(e).__name__})")
    rows = s.con.execute(
        "SELECT series_key, value_text, url FROM observation_all WHERE series_key LIKE 'watch.x.%' AND value_text LIKE '% links: %' AND substr(retrieved_at, 1, 10) = ?",
        [date.today().isoformat()],
    ).fetchall()
    for k, text, url in rows:
        lines.append(
            f"- {k}: linked artifact(s) {text.split(' links: ', 1)[1]} ({url}); fetch and add a manual row if it is tier 1-6"
        )
    return "\n## Suggested enrichment\n\n" + "\n".join(lines or ["- nothing to suggest"]) + "\n"


def cmd_export(a: argparse.Namespace) -> int:
    st.Store().export()
    print(f"exported to {st.WEB}")
    return 0


def check_errors(s: st.Store) -> list[str]:
    return _check(s)[0]


def attention(s: st.Store) -> list[str]:
    """What a human should look at but must not freeze the nightly: stale cards, late reasons, seed disagreements."""
    return _check(s)[1]


def _check(s: st.Store) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    notes: list[str] = []
    known = {r[0] for r in s.con.execute("SELECT id FROM observation_all").fetchall()}
    for e in s.events:
        if e.target_type == "indicator" and not e.evidence_ids:
            errors.append(f"{e.target_id}: status event {e.id} cites no evidence")
        missing = [i for i in e.evidence_ids if i not in known]
        if missing:
            errors.append(f"{e.target_id}: status event {e.id} cites unknown observations {missing}")
    for p in st.read_jsonl(st.DATA / "proposed_status_events.jsonl"):
        age = (datetime.now(timezone.utc) - datetime.fromisoformat(p["created_at"])).days
        if not p.get("reason", "").strip() and age > 14:
            notes.append(f"{p['target_id']}: proposal {p['id']} has waited {age} days for a reason")
    for ind in s.seed.indicators:
        if not ind.published:
            continue
        pts = s.headline(ind)
        if not pts:
            errors.append(f"{ind.id}: published without an approved observation")
        if not (
            (ind.normal_band and ind.band_rationale) or (ind.direction_rule and ind.direction_rule.rationale)
        ):
            errors.append(f"{ind.id}: published without bands/direction rule + rationale")
        tag = ind.leading_lagging.value if ind.leading_lagging else None
        if not tag or not (ind.timing_rationale or "").lower().startswith(tag + ":"):
            errors.append(f"{ind.id}: published without a timing_rationale that opens with its tag ({tag})")
        ev = s.current(ind.id)
        if not ev:
            errors.append(f"{ind.id}: published without a StatusEvent")
        elif ev.new_status not in ("emerging", "not_yet_measurable"):
            if _single_non_primary(s, ind):
                errors.append(f"{ind.id}: scored status from a single non-primary source")
        if ev and ind.proposed_status and ind.proposed_status != ev.new_status:
            notes.append(f"{ind.id}: seed proposed {ind.proposed_status}, evaluator says {ev.new_status}")
        stale = s._card(ind)["stale_as_of"]
        if stale and not ind.stale_ok:
            notes.append(
                f"{ind.id}: stale since {stale} (cadence {ind.cadence_expected}); set stale_ok with a reason or refresh"
            )
    return errors, notes


def cmd_check(a: argparse.Namespace) -> int:
    s = st.Store()
    errors, notes = _check(s)
    pending = sum(
        1 for p in st.OBS.glob("*.jsonl") for r in st.read_jsonl(p) if r["review_status"] == "pending"
    )
    proposed = st.read_jsonl(st.DATA / "proposed_status_events.jsonl")
    print(f"{pending} pending observations, {len(proposed)} proposed status events awaiting a reason")
    for n in notes:
        print("attention", n)
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


def cmd_candidates(a: argparse.Namespace) -> int:
    """Form D issuers that look like a seed company but have no CIK on file; add the CIK to seed/entities.yaml."""
    from .ingest.connectors.formd import FormD

    c = FormD()
    rows = c.candidates(c.fetch(a.day, False))
    for r in rows:
        print(
            f"{r['entity']:24s} {r['issuer'][:40]:40s} CIK {r['cik']}  {r['city']}, {r['state']}  [{r['industry']}]"
        )
    print(f"{len(rows)} candidates")
    return 0


def cmd_approve(a: argparse.Namespace) -> int:
    n = st.approve_pending(a.reviewer)
    moved = 0
    proposed = st.read_jsonl(st.DATA / "proposed_status_events.jsonl")
    keep = []
    for p in proposed:
        if p.get("reason", "").strip():
            with (st.DATA / "status_events.jsonl").open("a") as f:
                f.write(json.dumps(p, sort_keys=True) + "\n")
            moved += 1
        else:
            keep.append(p)
    st.write_jsonl(st.DATA / "proposed_status_events.jsonl", keep)
    print(f"approved {n} observations; {moved} status events committed, {len(keep)} still need a reason")
    return 0


def cmd_ask(a: argparse.Namespace) -> int:
    from .query.ask import ask

    s = st.Store()
    if not s.derived:
        s.derived = run_metrics(s.con)
        s.semantic_tables()
    res = ask(s, a.question)
    print(res["answer"])
    print(f"\n[{res['status']}] {len(res['citations'])} citations, ${res['usage']['usd']:.4f}")
    for f in res["checks"]["failures"]:
        print("  !", f)
    return 0 if res["status"] != "blocked" else 1


def cmd_golden(a: argparse.Namespace) -> int:
    from .query.ask import golden

    s = st.Store()
    if not s.derived:
        s.derived = run_metrics(s.con)
        s.semantic_tables()
    res = golden(s)
    for r in res:
        tag = " (informational)" if r["informational"] else ""
        print(f"{'PASS' if r['ok'] else 'FAIL'} {r['id']}{tag} [{r['status']}] {r['answer'][:160]!r}")
    req = [r for r in res if not r["informational"]]
    n = sum(r["ok"] for r in req)
    print(f"{n}/{len(req)} required passed, ${sum(r['usd'] for r in res):.3f}")
    return 0 if n == len(req) else 1


def cmd_audit_pull(a: argparse.Namespace) -> int:
    """Append the query service's answer records newer than the last one on file. Never fails the nightly."""
    import httpx

    from .query.ask import AUDIT_KEYS

    path = st.DATA / "query_log.jsonl"
    url = os.environ.get("QUERY_URL", "https://ai-tracker-query.fly.dev").rstrip("/") + "/audit"
    try:
        r = httpx.get(url, headers={"Authorization": f"Bearer {os.environ['QUERY_TOKEN']}"}, timeout=90)
        r.raise_for_status()
        rows = r.json()["rows"]
    except Exception as e:  # noqa: BLE001 - a cold or unreachable service loses nothing: rows stay seven days
        print(f"audit: not read ({type(e).__name__})")
        return 0
    lines = path.read_text().splitlines() if path.exists() else []
    last = max((json.loads(x)["time"] for x in lines if x.strip()), default="")
    new = sorted((x for x in rows if x["time"] > last), key=lambda x: x["time"])
    with path.open("a") as f:
        for x in new:
            f.write(json.dumps({k: x.get(k) for k in AUDIT_KEYS}, sort_keys=True) + "\n")
    print(f"audit: {len(new)} new answer records")
    return 0


def cmd_memo(a: argparse.Namespace) -> int:
    from .memo import write

    s = st.Store()
    if not s.derived:
        s.derived = run_metrics(s.con)
        s.semantic_tables()
    p = write(s, a.date, a.since)
    print(f"wrote {p}")
    return 0


def cmd_ops_notes(a: argparse.Namespace) -> int:
    from .memo import ops_notes

    print(ops_notes(st.Store()))
    return 0


def cmd_serve(a: argparse.Namespace) -> int:
    from .query.server import serve

    serve(a.port)
    return 0


def load_env(path: str = ".env") -> None:
    """KEY=VALUE lines, optional quotes; never overrides a variable already set."""
    try:
        lines = open(path).read().splitlines()
    except FileNotFoundError:
        return
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip("\"'"))


def main(argv: list[str] | None = None) -> None:
    load_env()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="ai-tracker")
    sub = p.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("ingest")
    i.add_argument("source", nargs="*", choices=list(CONNECTORS))
    i.add_argument("--all", action="store_true")
    i.add_argument("--day", type=date.fromisoformat, default=date.today())
    i.add_argument("--refetch", action="store_true")
    i.set_defaults(fn=cmd_ingest)
    for name, fn in (
        ("build", cmd_build),
        ("evaluate", cmd_evaluate),
        ("export", cmd_export),
        ("check", cmd_check),
        ("ops-notes", cmd_ops_notes),
    ):
        sub.add_parser(name).set_defaults(fn=fn)
    cd = sub.add_parser("candidates")
    cd.add_argument("--day", type=date.fromisoformat, default=date.today())
    cd.set_defaults(fn=cmd_candidates)
    q = sub.add_parser("ask")
    q.add_argument("question")
    q.set_defaults(fn=cmd_ask)
    sub.add_parser("golden").set_defaults(fn=cmd_golden)
    sub.add_parser("audit-pull").set_defaults(fn=cmd_audit_pull)
    mm = sub.add_parser("memo")
    mm.add_argument("--date", type=date.fromisoformat, default=None)
    mm.add_argument("--since", type=date.fromisoformat, default=None)
    mm.set_defaults(fn=cmd_memo)
    sv = sub.add_parser("serve")
    sv.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8080")))
    sv.set_defaults(fn=cmd_serve)
    ap = sub.add_parser("approve")
    ap.add_argument("--reviewer", default="merge")
    ap.set_defaults(fn=cmd_approve)
    a = p.parse_args(argv)
    if a.cmd == "ingest" and not a.all and not a.source:
        p.error("ingest needs a source name or --all")
    sys.exit(a.fn(a))
