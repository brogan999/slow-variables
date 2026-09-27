"""Operator notes: what needs the maintainer this week, read on request with `ai-tracker ops-notes`."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from . import store as st

REFRESH_NOTES = {
    "revelio": "Revelio's terms forbid automated access: take the figure from a Wayback snapshot"
}
# Hand-entered series whose source no longer states the figure, or whose figure a connector now reads: listing them
# would ask for a refresh that cannot, or need not, happen. Each reason was checked on the date it gives.
# ponytail: a source that states the figure again needs its entry removed by hand.
NOT_DUE = {
    "menlo.enterprise.multi_model_share.pt": "only the 2023 wave states a share; the 2024 wave gives a typical model "
    "count and the 2025 reports neither (22 Sep 2026)",
    "anthropic_ei.global.augmentation_share_reported.pt": "later reports state neither share in text, and the "
    "dataset connector reads both monthly (22 Sep 2026)",
    "anthropic_ei.global.automation_share_reported.pt": "later reports state neither share in text, and the "
    "dataset connector reads both monthly (22 Sep 2026)",
    "yale_budget_lab.recent_vs_older_grads.occupation_dissimilarity_range.pt": "the graduates index now comes from the "
    "tracker's chart data, which the yale_budget_lab_data connector reads (22 Sep 2026)",
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
            method != "manual"
            or key in NOT_DUE
            or not days
            or cad == "per_release"
            or not any(fnmatch(key, g) for g in globs)
        ):  # a one-off study is not due
            continue
        if st.is_stale(as_of, cad, today):
            note = f" ({REFRESH_NOTES[src]})" if src in REFRESH_NOTES else ""
            out.append(f"- `{key}` ({name}, {cad}): newest {as_of}; {url}{note}")
    return out


def ops_notes(store: st.Store, today: date | None = None) -> str:
    """Operator notes: what needs the maintainer this week (`ai-tracker ops-notes`). Everything here is already
    public in the repo or on /sources."""
    from .cli import attention
    from .ingest.connectors import (
        CONNECTORS,
    )  # a retired connector's source stays on /sources, not in the weekly notes

    today = today or date.today()
    week = [fl for fl in store.fetchlog if (today - fl.finished_at.date()).days < 7]
    lead = []
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
