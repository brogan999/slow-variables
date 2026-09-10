"""Nightly thesis monitor: the brief's Appendix B rules as plain functions over the store. None means untestable."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .store import Store


@dataclass
class Cond:
    text: str
    holds: bool | None
    obs_ids: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass
class Verdict:
    id: str
    name: str
    holds: bool | None
    conds: list[Cond]
    logic: str  # human-readable combination rule


def _all(conds: list[Cond]) -> bool | None:
    if any(c.holds is False for c in conds):
        return False
    if any(c.holds is None for c in conds):
        return None
    return True


def _any(conds: list[Cond]) -> bool | None:
    if any(c.holds is True for c in conds):
        return True
    if any(c.holds is None for c in conds):
        return None
    return False


class Data:
    def __init__(self, store: Store) -> None:
        self.s = store

    def metric(self, name: str, dims: dict[str, str] | None = None) -> tuple[float, date, list[str]] | None:
        rows = self.s.derived_for(name, dims)
        return (rows[-1].value, rows[-1].as_of_date, rows[-1].input_observation_ids) if rows else None

    def metric_n(
        self, name: str, n: int, dims: dict[str, str] | None = None
    ) -> list[tuple[date, float, list[str]]]:
        return [(r.as_of_date, r.value, r.input_observation_ids) for r in self.s.derived_for(name, dims)[-n:]]

    def series(self, glob: str, max_tier: int = 7) -> tuple[float, date, list[str]] | None:
        rows = [
            o for o in self.s.observations(glob) if o["value_numeric"] is not None and o["tier"] <= max_tier
        ]
        return (rows[-1]["value_numeric"], rows[-1]["as_of_date"], [rows[-1]["id"]]) if rows else None


def _cond(text: str, got: tuple[float, date, list[str]] | None, test, fmt: str = "{:.3g}") -> Cond:
    if got is None:
        return Cond(text, None, [], "untestable: no observations yet")
    v, d, ids = got
    return Cond(text, bool(test(v)), ids, f"{fmt.format(v)} as of {d}")


def normal_tech_falsified(d: Data) -> Verdict:
    ratio = d.metric("horizon_ratio_80_50")
    h80 = d.series("metr.*.horizon_80.pt")
    conc = d.metric("cross_tracker_concordance")
    hours = d.series("fred.us_workers.hours_assisted_share.q")
    tfp4 = d.metric_n("bls_tfp_yoy", 4)
    conds = [
        _cond("50%/80% horizon ratio ≤ 2", ratio, lambda v: v <= 2, "{:.2f}×"),
        _cond("80% horizon > 8 h", h80, lambda v: v > 480, "{:.0f} min"),
        _cond(
            "≥ 3 labour trackers show a concurrent AI-attributable break",
            conc,
            lambda v: v >= 3,
            "{:.0f} of 4",
        ),
        _cond("work hours assisted by AI > 20%", hours, lambda v: v > 0.20, "{:.1%}"),
        Cond(
            "TFP > trend + 1pp for ≥ 4 consecutive years",
            (all(v > 0.02 for _, v, _ in tfp4) if len(tfp4) == 4 else None),
            [i for _, _, ids in tfp4 for i in ids],
            ", ".join(f"{dt.year} {v:+.1%}" for dt, v, _ in tfp4) or "untestable",
        ),
    ]
    holds = _all([Cond("", _all(conds[:2])), conds[2], Cond("", _any(conds[3:]))])
    return Verdict(
        "normal_tech_falsified",
        "Normal-technology thesis FALSIFIED",
        holds,
        conds,
        "(ratio ≤ 2 AND 80% horizon > 8 h) AND (≥ 3 trackers break) AND (hours > 20% OR TFP > trend + 1pp for 4 years)",
    )


def normal_tech_strengthened(d: Data) -> Verdict:
    r4 = d.metric_n("horizon_ratio_80_50", 4)
    cl = d.series("*.continual_learning_level.pt")
    conc4 = d.metric_n("cross_tracker_concordance", 4)
    conds = [
        Cond(
            "50%/80% ratio non-decreasing over the last four models",
            (all(b >= a - 0.5 for (_, a, _), (_, b, _) in zip(r4, r4[1:])) if len(r4) == 4 else None),
            [i for _, _, ids in r4 for i in ids],
            ", ".join(f"{v:.1f}×" for _, v, _ in r4) or "untestable",
        ),
        _cond("continual-learning ladder ≤ L4", cl, lambda v: v <= 4, "L{:.0f}"),
        Cond(
            "precise nulls persist through four monthly tracker releases",
            (all(v == 0 for _, v, _ in conc4) if len(conc4) >= 4 else None),
            [i for _, _, ids in conc4 for i in ids],
            f"{len(conc4)} readings, max break count {max((v for _, v, _ in conc4), default=0):.0f}"
            if conc4
            else "untestable",
        ),
    ]
    return Verdict(
        "normal_tech_strengthened",
        "Normal-technology thesis STRENGTHENED",
        _all(conds),
        conds,
        "ratio non-decreasing AND ladder ≤ L4 AND four clean tracker releases (the ladder has no series yet, so this cannot resolve)",
    )


def _independent(d: Data, glob: str, text: str, test, fmt: str) -> Cond:
    """Tier-7 (lab self-report) rows are shown but never satisfy the condition."""
    got = d.series(glob, max_tier=5)
    if got is None and (own := d.series(glob)):
        v, day, ids = own
        return Cond(text, None, ids, f"untestable: only self-reported (tier 7) {fmt.format(v)} as of {day}")
    return _cond(text, got, test, fmt)


def invention_side_warning(d: Data) -> Verdict:
    conds = [
        _independent(
            d,
            "*.rsi_agent_workdays_per_human.pt",
            "independently verified agent-workdays per human-workday > 1",
            lambda v: v > 1,
            "{:.1f}",
        ),
        _independent(
            d,
            "*.rsi_intervention_rate_4_8h.pt",
            "intervention rate on 4–8 h agent tasks < 50%",
            lambda v: v < 0.5,
            "{:.0%}",
        ),
    ]
    return Verdict(
        "invention_side_warning",
        "Invention-side WARNING (bottleneck #86 under test)",
        _all(conds),
        conds,
        "both conditions, on independently verified series (OpenAI's self-reported 3.1 and >50% do not qualify)",
    )


def rents_migrate_up(d: Data) -> Verdict:
    semis = d.metric_n("margin_stack_share_by_layer", 5, {"layer_id": "compute_semis"})
    fall = (semis[-1][1] - semis[0][1] <= -0.05) if len(semis) == 5 else None
    conds = [
        Cond(
            "labs + apps share of stack margin up ≥ 5pp over four quarters",
            None,
            [],
            "untestable: no filed or estimated lab/app margin series yet",
        ),
        Cond(
            "semis' share of stack margin falling over four quarters",
            fall,
            [i for _, _, ids in semis for i in ids],
            (f"{semis[0][1]:.1%} → {semis[-1][1]:.1%}" if len(semis) == 5 else "untestable"),
        ),
    ]
    return Verdict(
        "rents_migrate_up",
        "Capture thesis 'rents migrate up the stack' SUPPORTED",
        _all(conds),
        conds,
        "labs + apps up ≥ 5pp AND semis down (contradicted if semis hold and app margins net of inference fall)",
    )


def consumers_keep_surplus(d: Data) -> Verdict:
    cs = d.series("stanford_del.us.genai_consumer_surplus_usd.pt")
    rev = d.series("menlo.us_enterprise.genai_spend_usd.fy")
    holds = (cs[0] > rev[0]) if cs and rev else None
    conds = [
        Cond(
            "consumer surplus (WTA) > US GenAI revenue",
            holds,
            (cs[2] if cs else []) + (rev[2] if rev else []),
            (
                f"${cs[0] / 1e9:.0f}B surplus vs ${rev[0] / 1e9:.0f}B enterprise spend (consumer spend not yet ingested)"
                if cs and rev
                else "untestable"
            ),
        ),
    ]
    return Verdict(
        "consumers_keep_surplus",
        "Capture thesis 'consumers keep most of the surplus' HOLDS",
        holds,
        conds,
        "surplus > revenue (revenue side is enterprise spend only until consumer spend is sourced)",
    )


RULES = [
    normal_tech_falsified,
    normal_tech_strengthened,
    invention_side_warning,
    rents_migrate_up,
    consumers_keep_surplus,
]


def run_all(store: Store) -> list[Verdict]:
    d = Data(store)
    return [rule(d) for rule in RULES]


def render_md(verdicts: list[Verdict], as_of: date) -> str:
    word = {True: "HOLDS", False: "does not hold", None: "untestable"}
    out = [f"# Thesis monitor ({as_of})\n", "Generated nightly from `thesis.py`; do not edit.\n"]
    for v in verdicts:
        out.append(f"\n## {v.name}: **{word[v.holds]}**\n\nRule: {v.logic}\n")
        for c in v.conds:
            mark = {True: "✓", False: "✗", None: "?"}[c.holds]
            out.append(
                f"- {mark} {c.text} — {c.detail}"
                + (
                    f" (obs: {', '.join(i[:8] for i in c.obs_ids[:3])}{'…' if len(c.obs_ids) > 3 else ''})"
                    if c.obs_ids
                    else ""
                )
            )
    return "\n".join(out) + "\n"
