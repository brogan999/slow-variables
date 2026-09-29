from datetime import date

from ai_tracker import market_map as mm
from ai_tracker.schema import Entity
from ai_tracker.store import Seed


def _real():
    seed = Seed.load()
    return seed, mm.load()


def test_the_seed_resolves():
    seed, spec = _real()
    assert mm.problems(spec, seed.entities, {s.id for s in seed.sublayers}, {i.id for i in seed.indicators}) == []


def test_every_sub_layer_has_exactly_one_default_and_every_category_is_real():
    seed, spec = _real()
    cats = {c["id"] for c in spec["categories"]}
    assert set(spec["sublayers"]) == {s.id for s in seed.sublayers}
    assert set(spec["sublayers"].values()) <= cats


def test_a_broken_seed_names_each_problem():
    spec = {
        "layers": [{"id": "l1"}],
        "categories": [
            {"id": "a", "layer": "l1", "leaves": ["x"]},
            {"id": "b", "layer": "nope", "leaves": []},
            {"id": "gone", "layer": "l1", "leaves": [], "out_of_scope": "for now"},
        ],
        "sublayers": {"s1": "a", "ghost": "zzz"},
        "excluded": {"e2": "off the map", "nobody": "off"},
        "indicators": {"i1": "a", "missing": "zzz"},
    }
    ents = [
        Entity(id="e1", name="E1", places=[{"cat": "a", "leaf": "y", "source": "src", "label": "l"},
                                            {"cat": "zzz", "source": "src", "label": "l"},
                                            {"cat": "gone", "source": "src", "label": " "}]),
        Entity(id="e2", name="E2", places=[{"cat": "a", "source": "src", "label": "l"}]),
    ]
    got = "\n".join(mm.problems(spec, ents, {"s1", "s2"}, {"i1"}))
    for needle in ["category b names unknown layer", "s2 has no default category", "ghost is not a sub-layer",
                   "defaults to unknown category zzz", "excluded entity nobody does not exist", "e2 is excluded but has places",
                   "unknown category zzz", "unknown leaf 'y'", "which is out of scope", "has a place with no label",
                   "indicator missing does not exist", "indicator missing placed in unknown category"]:
        assert needle in got, needle


def test_the_export_places_by_default_or_own_places_and_counts_add_up():
    spec = {
        "layers": [{"id": "l1", "number": 1, "name": "L1"}],
        "categories": [{"id": "a", "number": "1.1", "name": "A", "layer": "l1", "leaves": ["x"]},
                       {"id": "b", "number": "1.2", "name": "B", "layer": "l1", "leaves": []}],
        "sublayers": {"s1": "a"},
        "excluded": {"e3": "off"},
    }
    ents = [
        Entity(id="e1", name="E1", verified=True, memberships=[{"layer_id": "l", "sublayer_id": "s1"}]),
        Entity(id="e2", name="E2", memberships=[{"layer_id": "l", "sublayer_id": "s1"}],
               places=[{"cat": "a", "leaf": "x", "source": "src", "label": "Section", "read": "2026-09-28"}]),
        Entity(id="e3", name="E3", memberships=[{"layer_id": "l", "sublayer_id": "s1"}]),
        Entity(id="e4", name="E4", ownership="acquired", ownership_note="Acme, Oct 2025",
               memberships=[{"layer_id": "l", "sublayer_id": "s1", "to_date": "2025-10-09"}]),
    ]
    doc = mm.build(spec, ents, [{"id": "i1", "name": "I1", "sublayer_id": "s1"}], {"s1"}, date(2026, 9, 28))
    a, b = doc["layers"][0]["categories"]
    assert [x["id"] for x in a["entities"]] == ["e1", "e2", "e4"] and a["n_verified"] == 1
    e4 = a["entities"][2]
    assert (e4["ownership"], e4["ownership_note"], e4["ended"]) == ("acquired", "Acme, Oct 2025", "2025-10-09")
    assert a["entities"][0]["default"] and a["entities"][1]["label"] == "Section" and a["entities"][1]["read"] == "28 Sep 2026"
    assert a["leaves"] == [{"name": "x", "n": 1}] and a["default_of"] == ["s1"] and a["venture_sublayers"] == ["s1"]
    assert a["indicators"] == [{"id": "i1", "name": "I1"}]
    assert (a["chips"], a["n_more"], a["n_leaves"], a["n_indicators"]) == (["e1", "e2", "e4"], 0, 1, 1)
    assert doc["layers"][0]["n_categories"] == 2 and doc["layers"][0]["n_unmapped"] == 1
    assert doc["counts"]["entities"] == 3 and doc["counts"]["unmapped_categories"] == 1 and b["entities"] == []


def test_display_names_are_the_short_names_readers_know():
    filer = {"cik": "0000000001"}
    assert mm.display(Entity(id="nvda", name="NVIDIA Corp", aliases=["NVIDIA", "Nvidia"], **filer)) == "NVIDIA"
    assert mm.display(Entity(id="amd", name="Advanced Micro Devices", aliases=["AMD"], **filer)) == "AMD"
    assert mm.display(Entity(id="klac", name="KLA Corp", aliases=["KLA Corporation"], **filer)) == "KLA"
    assert mm.display(Entity(id="nbis", name="Nebius Group N.V.", **filer)) == "Nebius"
    assert mm.display(Entity(id="stead", name="Stead", aliases=["Reya"])) == "Stead"  # an old name is never shown
    assert mm.display(Entity(id="vercel", name="Vercel", aliases=["v0"])) == "Vercel"
