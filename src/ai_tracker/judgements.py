"""A model's judgement in words where the site has no reading (plan Part 39, Alex's decisions of 5 Oct 2026).

One seed file, seed/judgements.yaml, holds a word and a reason for each empty slot, by surface: an input the tightness
scorecard cannot score, a barrier with no reading, an Atlas expectation nobody scores, an indicator held back or
unpublished. A judgement is never a reading and never a status: nothing here is read by the evaluator, a metric, the
query service or a tally. The export copies it to one file the pages look up, and each page shows it only beside the
slot that is still empty. The forecasts board keeps its own file (seed/board_judgements.yaml), made the same way.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Any

import yaml

from .board import FIGURE, YEAR

ROOT = Path(__file__).resolve().parents[2]
SPEC = ROOT / "seed" / "judgements.yaml"
SURFACES = ("tightness", "barriers", "atlas", "indicators")


def load() -> dict[str, Any]:
    return (yaml.safe_load(SPEC.read_text()) or {}) if SPEC.exists() else {}


def known() -> dict[str, set[str]]:
    """The ids a judgement may name on each surface, from the seed files that define the slots."""
    seed = ROOT / "seed"
    return {
        "tightness": {i["id"] for i in yaml.safe_load((seed / "tightness.yaml").read_text())["inputs"]},
        "barriers": {str(b["id"]) for b in yaml.safe_load((seed / "bottlenecks.yaml").read_text())["bottlenecks"]},
        "atlas": {e["id"] for e in yaml.safe_load((seed / "atlas.yaml").read_text())["expectations"]},
        "indicators": {i["id"] for f in glob.glob(str(seed / "indicators" / "*.yaml")) for i in yaml.safe_load(Path(f).read_text()).get("indicators", [])},
    }


def problems(doc: dict[str, Any], known_ids: dict[str, set[str]]) -> list[str]:
    errors = []
    made = doc.get("made_by") or {}
    for k in ("model", "date", "method", "reviewed_by"):
        if not made.get(k):
            errors.append(f"judgements: made_by has no {k}")
    for surface, s in (doc.get("surfaces") or {}).items():
        if surface not in SURFACES or surface not in known_ids:
            errors.append(f"judgements: {surface} is not a surface of the site")
            continue
        words, seen = s.get("words") or {}, set()
        for j in s.get("judgements") or []:
            where = f"judgement {surface}/{j.get('id')}"
            if str(j.get("id")) not in known_ids[surface]:
                errors.append(f"{where} names no slot on the site")
            if j.get("id") in seen:
                errors.append(f"{where} is given twice")
            seen.add(j.get("id"))
            if j.get("word") not in words:
                errors.append(f"{where} has a word outside its surface's vocabulary: {j.get('word')}")
            reason = (j.get("reason") or "").strip()
            if not reason:
                errors.append(f"{where} gives no reason")
            elif FIGURE.search(YEAR.sub("", reason)):
                errors.append(f"{where}: its reason types a figure, a size word or an address")
    return errors


def build(doc: dict[str, Any]) -> dict[str, Any]:
    """web/data/judgements.json: surface -> slot id -> the word, its label and the reason; and who judged."""
    made = doc.get("made_by")
    return {
        "made_by": {**made, "date": str(made["date"])} if made else None,
        "surfaces": {
            surface: {str(j["id"]): {"word": j["word"], "label": s["words"][j["word"]], "reason": j["reason"]} for j in s.get("judgements") or []}
            for surface, s in (doc.get("surfaces") or {}).items()
        },
    }
