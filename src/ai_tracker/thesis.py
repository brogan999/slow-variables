"""Nightly thesis monitor: the brief's Appendix B rules as plain functions over the store. None means untestable."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .store import Store, is_stale


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
    counter: list[Cond] = field(default_factory=list)  # what would contradict it, where that is measurable

    @property
    def state(self) -> str:
        """supported, contradicted, untestable or unsupported. Not holding and being contradicted differ."""
        if self.holds:
            return "supported"
        if self.counter and _all(self.counter) is True:
            return "contradicted"
        return "untestable" if self.holds is None else "unsupported"


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
        self.cadence = {src.id: src.cadence for src in store.seed.sources}

    def _fresh(self, o: dict) -> bool:
        """Same rule as the indicator cards: older than 2x the source cadence (plus a publication lag) is stale."""
        return not is_stale(o["as_of_date"], self.cadence.get(o["source_id"], ""))

    def metric(self, name: str, dims: dict[str, str] | None = None) -> tuple[float, date, list[str]] | None:
        rows = self.s.derived_for(name, dims)
        return (rows[-1].value, rows[-1].as_of_date, rows[-1].input_observation_ids) if rows else None

    def metric_n(
        self, name: str, n: int, dims: dict[str, str] | None = None
    ) -> list[tuple[date, float, list[str]]]:
        return [(r.as_of_date, r.value, r.input_observation_ids) for r in self.s.derived_for(name, dims)[-n:]]

    def series(self, glob: str, max_tier: int = 7, best: bool = False) -> tuple[float, date, list[str]] | None:
        rows = [
            o
            for o in self.s.observations(glob)
            if o["value_numeric"] is not None and o["tier"] <= max_tier and self._fresh(o)
        ]
        if not rows:
            return None
        o = max(rows, key=lambda r: r["value_numeric"]) if best else rows[-1]
        return (o["value_numeric"], o["as_of_date"], [o["id"]])


def _cond(text: str, got: tuple[float, date, list[str]] | None, test, fmt: str = "{:.3g}") -> Cond:
    if got is None:
        return Cond(text, None, [], "untestable: no observation within two source cadences")
    v, d, ids = got
    return Cond(text, bool(test(v)), ids, f"{fmt.format(v)} as of {d}")


def normal_tech_falsified(d: Data) -> Verdict:
    ratio = d.metric("horizon_ratio_80_50")
    h50 = d.series("metr.*.horizon_50.pt", best=True)
    h80 = d.series("metr.*.horizon_80.pt", best=True)
    conc = d.metric("cross_tracker_concordance")
    hours = d.series("fred.us_workers.hours_assisted_share.q")
    tfp4 = d.metric_n("bls_tfp_yoy", 4)
    conds = [
        _cond("50%/80% horizon ratio ≤ 2", ratio, lambda v: v <= 2, "{:.2f}×"),
        _cond(  # a ratio that shrinks because the 50% horizon stalls at the ceiling is censoring, not reliability
            "50% horizon below the suite's 16 h ceiling, so a falling ratio is not censoring",
            h50,
            lambda v: v < 960,
            "{:.0f} min",
        ),
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
    holds = _all([Cond("", _all(conds[:3])), conds[3], Cond("", _any(conds[4:]))])
    return Verdict(
        "normal_tech_falsified",
        "Normal-technology thesis, falsification test",
        holds,
        conds,
        "(ratio ≤ 2 AND 50% horizon below the ceiling AND 80% horizon > 8 h) AND (≥ 3 trackers break) "
        "AND (hours > 20% OR TFP > trend + 1pp for 4 years)",
    )


def normal_tech_strengthened(d: Data) -> Verdict:
    r4 = d.metric_n("horizon_ratio_80_50", 4)
    cl = d.metric("continual_learning_level")
    conc4 = d.metric_n("cross_tracker_concordance", 4)
    conds = [
        Cond(
            "50%/80% ratio non-decreasing over the last four models",
            (all(b >= 0.9 * a for (_, a, _), (_, b, _) in zip(r4, r4[1:])) if len(r4) == 4 else None),
            [i for _, _, ids in r4 for i in ids],
            ", ".join(f"{v:.1f}×" for _, v, _ in r4) or "untestable",
        ),
        _cond("continual-learning ladder ≤ L4", cl, lambda v: v <= 4, "L{:.0f}"),
        Cond(
            "at most one tracker breaking through four monthly releases",
            (all(v <= 1 for _, v, _ in conc4) if len(conc4) >= 4 else None),
            [i for _, _, ids in conc4 for i in ids],
            f"{len(conc4)} readings, max break count {max((v for _, v, _ in conc4), default=0):.0f}"
            if conc4
            else "untestable",
        ),
    ]
    return Verdict(
        "normal_tech_strengthened",
        "Normal-technology thesis, strengthening test",
        _all(conds),
        conds,
        "ratio non-decreasing (within 10%) AND ladder ≤ L4 AND four releases with at most one break each",
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
    labs = d.metric_n("gross_profit_share_by_layer", 5, {"layer_id": "model"})
    semis = d.metric_n("gross_profit_share_by_layer", 5, {"layer_id": "compute_semis"})
    up = (labs[-1][1] - labs[0][1] >= 0.05) if len(labs) == 5 else None
    fall = (semis[-1][1] - semis[0][1] <= -0.05) if len(semis) == 5 else None
    conds = [
        Cond(
            "labs' share of stack gross profit up ≥ 5pp over four quarters (apps unmeasured)",
            up,
            [i for _, _, ids in labs for i in ids],
            (
                f"{labs[0][1]:.1%} → {labs[-1][1]:.1%}; the lab layer is a grade C estimate (run-rate × revenue-minus-inference margin)"
                if len(labs) == 5
                else f"untestable, {len(labs)} of 5 quarters"
            ),
        ),
        Cond(
            "chips' share of stack gross profit down ≥ 5pp over four quarters",
            fall,
            [i for _, _, ids in semis for i in ids],
            (
                f"{semis[0][1]:.1%} → {semis[-1][1]:.1%}"
                if len(semis) == 5
                else f"untestable, {len(semis)} of 5 quarters"
            ),
        ),
    ]
    hold_or_rise = (semis[-1][1] - semis[0][1] >= 0) if len(semis) == 5 else None
    counter = [
        Cond(
            "chips' share of stack gross profit flat or rising over four quarters",
            hold_or_rise,
            [i for _, _, ids in semis for i in ids],
            (
                f"{semis[0][1]:.1%} → {semis[-1][1]:.1%}"
                if len(semis) == 5
                else f"untestable, {len(semis)} of 5 quarters"
            ),
        )
    ]
    return Verdict(
        "rents_migrate_up",
        "Capture thesis 'rents migrate up the stack'",
        _all(conds),
        conds,
        "supported when labs are up ≥ 5pp and chips down, on gross profit; contradicted when chips' share is "
        "flat or rising (the brief's app-margin branch needs margins net of inference, which are not public)",
        counter,
    )


def _bracket(v: float, floor: float, ceiling: float) -> bool | None:
    """True above the ceiling, False below the floor, None (untestable) in between."""
    return True if v > ceiling else False if v < floor else None


# Stated-preference work finds willingness to accept runs a multiple of willingness to pay; the surplus estimate
# is WTA-based and the revenue ceiling omits consumer subscriptions, so the bar sits at the low end of that wedge.
WTA_WEDGE = 2.0


def consumers_keep_surplus(d: Data) -> Verdict:
    cs = d.series("stanford_del.us.genai_consumer_surplus_usd.pt")
    floor = d.series("menlo.us_enterprise.genai_spend_usd.fy")
    ceiling = d.metric("genai_revenue_upper_bound")
    holds = _bracket(cs[0], floor[0], ceiling[0] * WTA_WEDGE) if cs and floor and ceiling else None
    conds = [
        Cond(
            "consumer surplus (WTA) > twice the approximate revenue ceiling, bracketed",
            holds,
            (cs[2] if cs else []) + (floor[2] if floor else []) + (ceiling[2] if ceiling else []),
            (
                f"${cs[0] / 1e9:.0f}B surplus against a floor of ${floor[0] / 1e9:.0f}B (US enterprise spend) and a bar of "
                f"${ceiling[0] * WTA_WEDGE / 1e9:.0f}B, twice the ${ceiling[0] / 1e9:.0f}B ceiling (lab run-rates plus enterprise "
                "spend; consumer subscriptions sit outside it, and a WTA estimate runs at least twice WTP)"
                if cs and floor and ceiling
                else "untestable"
            ),
        ),
    ]
    return Verdict(
        "consumers_keep_surplus",
        "Capture thesis 'consumers keep most of the surplus'",
        holds,
        conds,
        "surplus above twice the approximate revenue ceiling holds, below the enterprise-spend floor fails, in "
        "between is untestable; the doubling covers the willingness-to-accept wedge and the consumer subscriptions "
        "the ceiling omits",
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
    word = {"supported": "HOLDS", "contradicted": "CONTRADICTED", "unsupported": "does not hold", "untestable": "untestable"}
    out = [f"# Thesis monitor ({as_of})\n", "Generated nightly from `thesis.py`; do not edit.\n"]
    for v in verdicts:
        out.append(f"\n## {v.name}: **{word[v.state]}**\n\nRule: {v.logic}\n")
        for c in v.conds + ([Cond("Contradicted when:", None, [], "")] + v.counter if v.counter else []):
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
