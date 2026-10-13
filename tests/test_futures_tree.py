"""The technology tree at /futures/tree (plan Part 60): one node for a kind of technology in a decade, lit when the
gates it waits on are open. Every count is the export's; the links between nodes are a model's judgement."""

from __future__ import annotations

import copy
import itertools
import json
import re

from ai_tracker import futures as fu

WEB = fu.ROOT / "web" / "src"
SELLERS = ("incumbents", "anyone", "maker", "permit")


def _nodes(doc):
    return [n for lane in doc["lanes"] for n in lane["nodes"]]


def _big(category: str, key: str) -> list[dict]:
    """One kind and one decade: the unbuilt technologies the profit judgement calls a large or a vast prize."""
    judged = fu.verdicts()
    return [
        judged[x["id"]] | {"needs": x["needs"]}
        for x in fu.ideas()
        if x["category"] == category and x["technology"] == "yes" and x["arrival"]["state"] == "not_marked_built"
        and fu.expected_key(x) == key and (judged.get(x["id"]) or {}).get("prize") in ("large", "vast")
    ]


def test_each_node_counts_the_large_and_vast_prizes_of_its_kind_and_decade_by_who_keeps_the_rest():
    doc = fu.tree()
    assert _nodes(doc)
    for lane in doc["lanes"]:
        for n in lane["nodes"]:
            mine = _big(lane["id"], n["key"])
            assert n["n"] == len(mine) > 0, n["id"]
            assert [s["id"] for s in n["shares"]] == list(SELLERS)
            for s in n["shares"]:
                assert s["n"] == sum(1 for r in mine if r["seller"] == s["id"]), (n["id"], s["id"])
            assert abs(sum(s["width"] for s in n["shares"]) - 100) < 0.3, "the bar's widths are the export's and fill it"


def test_a_node_waits_on_what_most_of_its_prizes_wait_on_and_an_earlier_gate_wins_a_tie():
    doc, spec = fu.tree(), fu.tree_spec()
    order = [g["id"] for g in spec["gates"]]
    of = {need: g["id"] for g in spec["gates"] for need in g["needs"]}
    for lane in doc["lanes"]:
        for n in lane["nodes"]:
            votes = [of[r["needs"]] for r in _big(lane["id"], n["key"]) if r["needs"] in of]
            assert n["gate"]["id"] == max(order, key=lambda g: (votes.count(g), -order.index(g))), n["id"]


def test_the_export_is_the_same_twice_and_the_committed_file_is_the_export():
    a, b = json.dumps(fu.tree(), sort_keys=True), json.dumps(fu.tree(), sort_keys=True)
    assert a == b
    assert json.loads((fu.ROOT / "web" / "data" / "futures" / "tree.json").read_text()) == json.loads(a)


def test_every_set_of_open_gates_has_a_tally_that_is_the_sum_of_the_nodes_it_lights():
    doc = fu.tree()
    gates = [g["id"] for g in doc["gates"] if not g["open"]]
    assert len(doc["tallies"]) == 2 ** len(gates)
    lit_before: dict[frozenset, int] = {}
    for flags in itertools.product("01", repeat=len(gates)):
        on = {g for g, f in zip(gates, flags) if f == "1"}
        lit = [n for n in _nodes(doc) if set(n["needs"]) <= on]
        t = doc["tallies"]["".join(flags)]
        assert t["lit"] == len(lit) and t["n"] == sum(n["n"] for n in lit)
        for s in SELLERS:
            assert t[s] == sum(x["n"] for n in lit for x in n["shares"] if x["id"] == s)
        lit_before[frozenset(on)] = len(lit)
    for on, n in lit_before.items():  # opening a gate never darkens a node
        assert all(n >= lit_before[frozenset(sub)] for k in range(len(on)) for sub in itertools.combinations(on, k))
    assert lit_before[frozenset(gates)] == len(_nodes(doc)), "with every gate open the whole board is lit"
    assert 0 < lit_before[frozenset()] < len(_nodes(doc)), "something is lit before any gate is opened, and not everything"


def test_a_node_needs_its_own_gate_and_every_gate_on_the_way_to_it():
    doc = fu.tree()
    by = {n["id"]: n for n in _nodes(doc)}
    always = {g["id"] for g in doc["gates"] if g["open"]}
    for n in by.values():
        want = {n["gate"]["id"]} - always
        for a in n["after"]:
            assert a["id"] in by, f"{n['id']} comes after a node that is not on the board"
            want |= set(by[a["id"]]["needs"])
        assert set(n["needs"]) == want and n["needs"] == sorted(n["needs"]), n["id"]
    for lane in doc["lanes"]:  # within a kind of technology, each decade comes after the one before
        for prev, n in zip(lane["nodes"], lane["nodes"][1:]):
            assert prev["col"] < n["col"] and {"id": prev["id"], "cross": False} in [{"id": a["id"], "cross": a["cross"]} for a in n["after"]]


def test_the_board_says_how_many_prizes_it_leaves_off():
    doc = fu.tree()
    judged = fu.verdicts()
    every = sum(
        1 for x in fu.ideas()
        if x["technology"] == "yes" and x["arrival"]["state"] == "not_marked_built" and (judged.get(x["id"]) or {}).get("prize") in ("large", "vast")
    )
    on = sum(n["n"] for n in _nodes(doc))
    assert doc["on_board"] == on and doc["left_off"]["n"] == every - on > 0
    assert doc["left_off"]["kinds"], "the kinds of technology with no row are named"


def test_the_seed_is_sound_and_a_broken_one_is_caught():
    assert fu.tree_problems() == []
    spec = fu.tree_spec()
    looped = copy.deepcopy(spec)
    first, last = looped["lanes"][0]["nodes"][0], looped["lanes"][0]["nodes"][-1]
    first.setdefault("after", []).append(f"{looped['lanes'][0]['id']}-{last['decade']}")
    assert any("circle" in e for e in fu.tree_problems(looped))
    typed = copy.deepcopy(spec)
    typed["lanes"][0]["nodes"][0]["name"] = "Seven kinds of thinking machine"
    assert any("figure" in e for e in fu.tree_problems(typed))
    empty = copy.deepcopy(spec)
    empty["lanes"][0]["nodes"].append({"decade": "2090s", "name": "Nothing imagined here", "built": "idea"})
    assert any("no large or vast prize" in e for e in fu.tree_problems(empty))
    for k in ("model", "date", "method", "reviewed_by"):
        assert spec["made_by"].get(k), f"the tree's judgements say who made them: {k}"
    assert "owner" in spec["tally"].lower(), "the seed records whose decision the running tally is"


def test_the_check_and_the_export_are_wired_without_handing_the_judgement_file_around():
    src = fu.ROOT / "src" / "ai_tracker"
    assert "futures.tree_problems()" in (src / "cli.py").read_text()
    assert "fut.tree()" in (src / "store.py").read_text() and '"tree.json"' in (src / "store.py").read_text()


def test_the_tree_is_listed_where_a_reader_or_a_crawler_would_look():
    contents = (WEB / "lib" / "contents.ts").read_text()
    assert re.search(r'^\s*"/futures/tree": \{ name: "[^"]+", question: "[^"]+\?"', contents, re.M)
    assert re.search(r'"/singularity": \[[^\]]*"/futures", "/futures/tree"', contents), "the contents page lists it beside Futures"
    assert '"/futures/tree"' in (WEB / "app" / "sitemap.ts").read_text()
    assert '"/futures/tree"' in (WEB / "app" / "search.json" / "route.ts").read_text()
    assert 'href="/futures/tree"' in (WEB / "app" / "futures" / "page.tsx").read_text()
    assert "/futures/tree" in (WEB / "app" / "methodology" / "page.tsx").read_text(), "the method page says how the tree is made"


def test_the_board_lights_without_script_and_only_the_tally_line_is_an_island():
    board = (WEB / "components" / "FuturesTree.tsx").read_text()
    tally = (WEB / "components" / "FuturesTreeTally.tsx").read_text()
    page = (WEB / "app" / "futures" / "tree" / "page.tsx").read_text()
    assert '"use client"' not in board and '"use client"' not in page and '"use client"' in tally
    assert ":has(#ft-g-" in board and 'type="checkbox"' in board, "the gates are checkboxes and the rules are CSS"
    assert "<noscript>" in board and "aria-live" in tally
    assert "tallies[" in tally and "+=" not in tally and "+=" not in board, "the page looks a tally up; it adds nothing"
    assert "localStorage" not in board + tally + page
    assert "min-w-[" not in board, "the board folds at phone width; it does not scroll sideways"


def test_every_count_on_the_page_is_labelled_a_models_judgement_and_so_are_the_links():
    board = (WEB / "components" / "FuturesTree.tsx").read_text()
    tally = (WEB / "components" / "FuturesTreeTally.tsx").read_text()
    page = (WEB / "app" / "futures" / "tree" / "page.tsx").read_text()
    assert "as a model judges it" in tally and "as a model judges it" in board
    assert "A model&apos;s judgement, not a reading" in board and "made_by" in board
    assert "bg-fast" not in board and "bg-slow" not in board, "who keeps the rest is drawn in ink, never a hue"
    assert "left_off" in page, "the page says what the board leaves off"
