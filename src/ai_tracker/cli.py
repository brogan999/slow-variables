"""ai-tracker ingest | build | evaluate | export | check | approve"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timezone

from . import store as st
from .analysis.bands import flow_status
from .analysis.direction import direction
from .analysis.metrics import run_metrics
from .ingest.connectors import CONNECTORS
from .schema import StatusEvent, Tier

log = logging.getLogger("ai-tracker")


def cmd_ingest(a: argparse.Namespace) -> int:
    names = list(CONNECTORS) if a.all else a.source
    rc = 0
    for name in names:
        rows, fl = CONNECTORS[name]().run(a.day, a.refetch)
        fl.items_new = st.append_observations(name, rows) if rows else 0
        st.append_fetchlog(fl)
        print(
            f"{name}: ok={fl.ok} found={fl.items_found} new={fl.items_new}"
            + (f" error={fl.error}" if fl.error else "")
        )
        rc |= int(not fl.ok)
    return rc


def cmd_build(a: argparse.Namespace) -> int:
    s = st.Store()
    n = s.con.execute("SELECT count(*) FROM observations").fetchone()[0]
    print(
        f"{len(s.seed.indicators)} indicators, {len(s.seed.sources)} sources, {n} approved observations, "
        f"{len(s.derived)} derived, {len(s.events)} status events"
    )
    return 0


def cmd_evaluate(a: argparse.Namespace) -> int:
    s = st.Store()
    derived = run_metrics(s.con)
    st.write_jsonl(st.DATA / "derived.jsonl", [st.dump(d) for d in derived])
    s.derived = derived
    proposed = st.read_jsonl(st.DATA / "proposed_status_events.jsonl")
    seen = {(p["target_id"], p["new_status"]) for p in proposed}
    lines = [f"derived: {len(derived)} rows across {len({d.metric for d in derived})} metrics"]
    for ind in s.seed.indicators:
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
        cur = s.current(ind.id)
        old = cur.new_status if cur else None
        lines.append(f"{ind.id}: input={value!r} as_of={as_of} tier={int(tier)} -> {new} (current: {old})")
        if new != old and (ind.id, new) not in seen and (value is not None or ind.direction_rule):
            ev = StatusEvent(
                target_id=ind.id,
                old_status=old,
                new_status=new,
                old_conf=cur.new_conf if cur else None,
                new_conf=cur.new_conf if cur else ind.confidence,
                reason="",
                evidence_ids=ids,
                author="evaluate",
                created_at=datetime.now(timezone.utc),
            )
            proposed.append(st.dump(ev))
            lines.append(
                f"  proposed StatusEvent {ev.id}: fill `reason` in data/proposed_status_events.jsonl or delete the row"
            )
    st.write_jsonl(st.DATA / "proposed_status_events.jsonl", proposed)
    summary = "\n".join(lines)
    print(summary)
    (st.DATA / "summary.md").write_text(
        f"# evaluate {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z\n\n```\n{summary}\n```\n"
    )
    return 0


def cmd_export(a: argparse.Namespace) -> int:
    st.Store().export()
    print(f"exported to {st.WEB}")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    s = st.Store()
    errors: list[str] = []
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
        ev = s.current(ind.id)
        if not ev:
            errors.append(f"{ind.id}: published without a StatusEvent")
        elif ev.new_status not in ("emerging", "not_yet_measurable"):
            ev_obs = s.evidence_obs(ind)
            srcs = {o["source_id"] for o in ev_obs}
            tiers = {Tier(o["tier"]) for o in ev_obs}
            if len(srcs) < 2 and not tiers & {Tier.BENCHMARK, Tier.MODEL_RELEASE, Tier.OFFICIAL_FILING}:
                errors.append(f"{ind.id}: scored status from a single non-primary source")
        if ev and ind.proposed_status and ind.proposed_status != ev.new_status:
            print(f"note {ind.id}: seed proposed {ind.proposed_status}, evaluator says {ev.new_status}")
    pending = sum(
        1 for p in st.OBS.glob("*.jsonl") for r in st.read_jsonl(p) if r["review_status"] == "pending"
    )
    proposed = st.read_jsonl(st.DATA / "proposed_status_events.jsonl")
    print(f"{pending} pending observations, {len(proposed)} proposed status events awaiting a reason")
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


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


def main(argv: list[str] | None = None) -> None:
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
    ):
        sub.add_parser(name).set_defaults(fn=fn)
    ap = sub.add_parser("approve")
    ap.add_argument("--reviewer", default="merge")
    ap.set_defaults(fn=cmd_approve)
    a = p.parse_args(argv)
    if a.cmd == "ingest" and not a.all and not a.source:
        p.error("ingest needs a source name or --all")
    sys.exit(a.fn(a))
