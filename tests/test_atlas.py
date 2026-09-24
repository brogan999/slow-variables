import copy
import re

import yaml

from ai_tracker import atlas, board
from ai_tracker.outlook import load as load_outlook

W = ["managed_explosion", "long_diffusion", "loss_of_control", "brake"]
YEAR = re.compile(r"\(?(1[6-9]\d\d|2[01]\d\d)(s|'s|’s)?[\"”]?[,.;:)]?")
NUMBER_WORD = re.compile(
    r"\b(half|halves|twice|double[sd]?|triple[sd]?|percent|per cent|fifths?|tenths?|hundreds?|thousands?|millions?"
    r"|billions?|trillions?|dozens?|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty|thirty|forty|fifty"
    r"|sixty|seventy|eighty|ninety)\b|-fold\b",
    re.I,
)
NAMES = {"v0"}  # a product name, not a figure: the tool the plates were made in


def _e(i, domain="work", era="now", worlds=("brake",), source="a"):
    return {"id": i, "domain": domain, "era": era, "worlds": list(worlds), "source": source, "line": "x"}


def test_cells_count_distinct_works_and_an_any_work_counts_in_every_world():
    got = atlas.cells(
        [
            _e("a1", source="s1", worlds=["brake"]),
            _e("a2", source="s1", worlds=["long_diffusion"]),  # same work twice: counts once overall
            _e("a3", source="s2", worlds=["any"]),
            _e("a4", source="s3", era="long_run"),
        ],
        W,
    )
    assert got[("work", "now")] == {
        "all": 2,
        "managed_explosion": 1,
        "long_diffusion": 2,
        "loss_of_control": 1,
        "brake": 2,
        "any": 1,
    }
    assert got[("work", "long_run")]["all"] == 1 and ("economy", "now") not in got


def test_levels_step_at_fixed_counts():
    assert [atlas.level(n) for n in (0, 1, 2, 3, 4, 6, 7, 30)] == [0, 1, 2, 2, 3, 3, 4, 4]


def _published() -> set[str]:
    return {
        i["id"]
        for f in ("diffusion", "capture")
        for i in yaml.safe_load((atlas.ROOT / "seed" / "indicators" / f"{f}.yaml").read_text())["indicators"]
        if i.get("published")
    }


def _problems(spec):
    ol = load_outlook()
    return atlas.problems(
        spec, ol, set(ol.get("facts") or {}), _published(), {f["id"] for f in board.load()["folios"]}
    )


def test_the_seed_resolves():
    assert _problems(atlas.load()) == []


def test_each_rule_fires():
    spec = copy.deepcopy(atlas.load())
    e = spec["expectations"][0]
    e["worlds"] = ["utopia"]
    e["reads"] = ["nowhere"]
    e["source"] = "nobody"
    spec["expectations"].append(dict(spec["expectations"][1]))  # a repeated id
    d = spec["domains"][0]
    d["thesis_from"] = [x["id"] for x in spec["expectations"] if x["domain"] != d["id"]][:2]
    spec["plates"][d["id"]] = {"file": "missing", "alt": "", "allegory": ""}
    got = "\n".join(_problems(spec))
    for bit in (
        "worlds outside the four",
        "reads nowhere",
        "unknown source nobody",
        "share an id",
        "thesis_from names an expectation outside",
        "needs alt text",
        "missing-480.webp is missing",
    ):
        assert bit in got, bit


def test_a_disagreement_never_puts_one_writer_on_both_sides():
    spec = copy.deepcopy(atlas.load())
    d = next(x for x in spec["domains"] if x.get("disagreement"))
    a = d["disagreement"]["side_a"]["entries"][0]
    d["disagreement"]["side_b"]["entries"].append(a)
    assert any("both sides" in p for p in _problems(spec))


def test_the_site_types_no_figure_and_credited_lines_type_only_years():
    spec = atlas.load()
    for t in [*atlas.strings(spec), *atlas.credited(spec)]:
        stray = [w for w in t.split() if re.search(r"\d", w) and w.strip(",.;") not in NAMES]
        assert all(YEAR.fullmatch(w) for w in stray), (t, stray)
    for t in atlas.strings(spec):
        assert not NUMBER_WORD.search(t), t


def test_the_world_filter_ships_only_when_a_third_of_entries_name_worlds():
    spec = atlas.load()
    specific = sum(1 for e in spec["expectations"] if e["worlds"] != ["any"])
    assert specific >= atlas.FILTER_SHARE * len(spec["expectations"])
