"""/story: the argument as a run of figures reused from the other pages (plan Part 46). The seed holds words only, and
so does the export: which figure, where its full version lives, the two sentences above it and the caveats beneath.
Every number a panel shows is drawn by the reused figure from its own page's export. This module decides, from those
exports, which panels have data and which sentences about tonight's result still hold; the web decides neither."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from . import illustrations

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / "seed" / "story.yaml"
DATA = ROOT / "web" / "data"
KINDS = ("chart", "model", "illustration", "mixed")
# the components the page may draw, by name; web/src/app/story/page.tsx keeps the matching map
FIGURES = (
    "FourClocks", "LagModel", "StageGauges", "ReadingsFigure", "WholeFigure", "ScreenFigure",
    "PerezCurve", "StackPlate", "LabsPlate", "TiesPlate", "ChainFigure", "ScalePlate", "Anatomy",
    "DisputeReach", "TallyBars", "LeanBars", "TimelinePlate", "SaidAgainstGiven", "WorldsGrid", "FictionLag",
)  # fmt: skip
Read = Callable[[str], Any]


def read(name: str) -> Any:
    return json.loads((DATA / name).read_text())


def _settle(d: Read) -> dict[str, Any]:
    return d("outlook.json")["figures"]["settle"]


def _states(d: Read) -> dict[str, int]:
    return d("singularity.json")["figures"]["worlds"]["states"]


# Each is a yes or a no read off another page's export. The first five are what the reused component itself draws
# nothing on, or draws with its own sentence flagged or its marker missing; the rest gate a sentence that states
# tonight's result.
CONDITIONS: dict[str, Callable[[Read], bool]] = {
    "clocks_chart": lambda d: bool((c := d("argument.json")["clocks"]).get("chart")) and c.get("holds") is not False,
    "phase_placed": lambda d: d("argument.json")["phase"]["state"] != "untestable",
    "profit_stack": lambda d: bool((s := d("lens/capture.json")["gross_profit_stack"]).get("axis") and s.get("quarters")),
    "ties": lambda d: bool(d("lens/capture.json")["figures"].get("ties")),
    "leans": lambda d: bool((b := d("board.json"))["figures"].get("leans") and b.get("leans") and b.get("judged")),
    "clocks_stamps_mixed": lambda d: {"measured", "reported"} <= {x.get("stamp") for x in d("argument.json")["clocks"]["drawn"]},
    "most_too_early": lambda d: (b := d("board.json"))["tally"]["too_early"] > b["n"] - b["tally"]["too_early"],
    "ages_near": lambda d: bool(d("argument.json")["migration"]["figures"]["ages"].get("near")),
    "most_disputes_untested": lambda d: _settle(d)["counts"]["no_test"] > _settle(d)["n"] - _settle(d)["counts"]["no_test"],
    "no_world_signpost_read": lambda d: not _states(d).get("holding") and not _states(d).get("failing"),
}


def load() -> dict[str, Any]:
    return yaml.safe_load(SEED.read_text())


def panels(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Every panel, of the seed or of a built document: the acts' in order, then the coda's."""
    return [*(p for a in spec["acts"] for p in a["panels"]), *spec["coda"]]


def placed(spec: dict[str, Any]) -> list[str]:
    """The act pictures, as the seed names them, for illustrations.placement_problems."""
    return [a["illustration"] for a in spec["acts"]]


def strings(spec: dict[str, Any]) -> list[str]:
    """Every word the page adds, for the tests that keep figures and findings out of them."""
    out = [spec["eyebrow"], spec["title"], spec["lede"], *spec["disclosure"], *spec["closing"].values()]
    out += [x for a in spec["acts"] for x in (a["sentence"], a.get("picture_note")) if x]
    for p in panels(spec):
        out += [*p["words"], *(c if isinstance(c, str) else c["text"] for c in p["carry"])]
    return out


def problems(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for p in panels(spec):
        where = f"story: panel {p['id']}"
        if p["kind"] not in KINDS:
            errors.append(f"{where} has kind {p['kind']}, not one of {', '.join(KINDS)}")
        if p["figure"] not in FIGURES:
            errors.append(f"{where} names {p['figure']}, which the page does not draw")
        if len(p["words"]) != 2:
            errors.append(f"{where} needs exactly two sentences")
        for name in [p.get("needs"), *(c["when"] for c in p["carry"] if not isinstance(c, str))]:
            if name and name not in CONDITIONS:
                errors.append(f"{where} waits on {name}, which is not a condition")
    return errors


def build(spec: dict[str, Any], data: Read = read, holds: Callable[[str], bool] | None = None) -> dict[str, Any]:
    """The page's document: strings only. A panel whose figure has no data is left out with its sentences."""
    ok = holds or (lambda name: CONDITIONS[name](data))

    def shown(ps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "id": p["id"], "figure": p["figure"], "kind": p["kind"], "route": p["route"], "href": f"{p['route']}#{p['anchor']}",
                "words": p["words"], "carry": [c if isinstance(c, str) else c["text"] for c in p["carry"] if isinstance(c, str) or ok(c["when"])],
            }
            for p in ps if not p.get("needs") or ok(p["needs"])
        ]  # fmt: skip

    return {
        **{k: spec[k] for k in ("eyebrow", "title", "lede", "disclosure", "closing", "plates")},
        "acts": [
            {
                "id": a["id"], "anchor": a["anchor"], "sentence": a["sentence"], "illustration": illustrations.card(a["illustration"]),
                "picture_note": a.get("picture_note"), "panels": shown(a["panels"]),
            }
            for a in spec["acts"]
        ],
        "coda": shown(spec["coda"]),
    }  # fmt: skip
