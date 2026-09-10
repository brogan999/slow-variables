"""Citation post-check: every number in a model-written answer must be traceable to a cited record.

`check(text, records)` extracts numeric tokens from prose, normalises units the way the site renders them
(format.ts: shares as percentages, USD with k/M/B/T suffixes, ratios with x, minutes as hours), and matches each
against the values (and CI bounds, band edges or verbatim snippets) of the records the answer cites. A sentence
that carries a number but no [obs:..] / [derived:..] / [ind:..] token fails; so does a number that matches nothing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

CITE = re.compile(r"\[(obs|derived|ind|event):([A-Za-z0-9_.\-]+)\]")
NUM = re.compile(
    r"(?<![\w.\-#])(?P<sign>[-−–])?(?P<cur>\$|€|£)?(?P<num>\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?P<suffix>\s?(?:%|×|x\b|[kKmMbBtT](?!\w)|h\b|hours?\b|min\b|minutes?\b|days?\b|pp\b|points?\b|bn\b|trillion|billion|million))?",
)
MULT = {"k": 1e3, "m": 1e6, "b": 1e9, "bn": 1e9, "t": 1e12, "million": 1e6, "billion": 1e9, "trillion": 1e12}
WORD_NUMBERS = {"one", "two", "three", "four"}


@dataclass
class Record:
    """One cited thing: an observation, a derived row or an indicator (whose band edges count as numbers)."""

    id: str
    kind: str  # obs | derived | ind | event
    values: list[float] = field(default_factory=list)  # value, low, high, band edges
    unit: str = ""
    snippet: str = ""


@dataclass
class Result:
    ok: bool
    numbers: list[str]
    failures: list[str]
    annotated: str


def _candidates(v: float, unit: str) -> list[float]:
    """Every rendering the site could give a value, in base units the extractor also produces."""
    out = {v}
    if unit == "share":
        out.add(v * 100)  # 0.063 renders as 6.3%
    if unit in ("minutes",):
        out.add(v / 60)  # 186 min renders as 3.1 h
    if unit in ("days",):
        out.add(v / 30.44)  # "about 3.5 months"
    return sorted(out)


def _close(a: float, b: float, rel: float = 0.005, absolute: float = 0.05) -> bool:
    return abs(a - b) <= max(absolute, rel * max(abs(a), abs(b)))


def _rendered_matches(token: float, rec: Record) -> bool:
    for v in rec.values:
        for c in _candidates(v, rec.unit):
            # the site rounds: 172.0B, 6.3%, 6.34x, 3.1 h -> accept within the rounding of the shorter form
            if (
                _close(token, c)
                or _close(round(token, 1), round(c, 1), rel=0.02)
                or _close(token, c, rel=0.02, absolute=0.5)
            ):
                return True
    return False


def _parse(m: re.Match) -> float | None:
    raw = m.group("num").replace(",", "")
    try:
        v = float(raw)
    except ValueError:
        return None
    suf = (m.group("suffix") or "").strip().lower()
    if suf in MULT:
        v *= MULT[suf]
    if m.group("sign"):
        v = -v
    return v


def check(text: str, records: dict[str, Record]) -> Result:
    numbers, failures, annotated = [], [], text
    units = []
    for line in text.splitlines():
        units += (
            [line] if line.lstrip().startswith("- ") else re.split(r"(?<=[.!?])\s+", line)
        )  # a bullet is one claim
    for sentence in units:
        cited = [records.get(i) for _, i in CITE.findall(sentence)]
        cited = [r for r in cited if r]
        for m in NUM.finditer(CITE.sub(" ", sentence)):  # ids inside citation tokens are not numbers
            token_text = m.group(0).strip()
            suf = (m.group("suffix") or "").strip().lower()
            num = m.group("num")
            if suf in ("", "days", "day", "points", "point", "pp") and re.fullmatch(r"(19|20)\d\d", num):
                continue  # a bare year
            if not m.group("cur") and not suf and re.fullmatch(r"\d", num):
                continue  # "one of 4" style small counts and list numbering
            if re.match(r"\s*(time[- ])?horizon|\s*reliab|\s*confidence", sentence[m.end() :]):
                continue  # "the 80% horizon" names a series, it is not a claim
            v = _parse(m)
            if v is None:
                continue
            numbers.append(token_text)
            if not cited:
                failures.append(f"uncited number: {token_text}")
                annotated = annotated.replace(token_text, f"⟦unverified: {token_text}⟧", 1)
                continue
            snippet_hit = any(num in r.snippet for r in cited if r.snippet)
            if not snippet_hit and not any(_rendered_matches(v, r) for r in cited):
                failures.append(f"{token_text} not found in cited records {[r.id for r in cited]}")
                annotated = annotated.replace(token_text, f"⟦unverified: {token_text}⟧", 1)
    return Result(not failures, numbers, failures, annotated)
