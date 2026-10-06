"""Part 45g: the figures on /value-chain. Every count, share and position is made in Python from records the export
already holds; the page only places them. Nothing here changes a unit's judgement, an entity or an ownership state."""

import copy
import json
import re
from datetime import date
from pathlib import Path

from ai_tracker import futures
from ai_tracker import market_map as mm
from ai_tracker import value_chain as vc
from ai_tracker.outlook import load as load_outlook
from ai_tracker.store import Seed

ROOT = Path(__file__).resolve().parents[1]
TSX = ROOT / "web" / "src" / "components" / "ValueChainFigures.tsx"
PARTS = ROOT / "web" / "src" / "components" / "diagrams" / "valuechain.tsx"
PAGE = ROOT / "web" / "src" / "app" / "value-chain" / "page.tsx"
MAP = ROOT / "web" / "src" / "components" / "MarketMap.tsx"
YEAR = re.compile(r"\b(19|20)\d\d\b")
TODAY = date(2026, 10, 6)


def _map():
    seed = Seed.load()
    return mm.build(mm.load(), seed.entities, [], set(), TODAY)


def _chain():
    seed = Seed.load()
    doc = vc.build(vc.load(), load_outlook(), futures.rubric(), {})
    names = {e.id: e.name for e in seed.entities}
    for c in doc["companies"]:
        c["name"] = names[c["entity"]]
    before = copy.deepcopy(doc)
    short = {e.id: mm.display(e) for e in seed.entities}
    fig = vc.figures(doc, seed.layers, seed.sublayers, mm.primaries(mm.load(), seed.entities, TODAY), futures.rubric(), short)
    assert doc == before  # drawing the figures changes no judgement
    return doc, fig, seed


def _in_scope(layer):
    return [c for c in layer["categories"] if not c["out_of_scope"]]


def test_the_map_export_keeps_every_field_it_had():
    doc = _map()
    assert set(doc) == {"credit", "layers", "counts", "figures"}
    assert set(doc["figures"]) == {"categories", "verified", "coverage"}
    json.dumps(doc)


def test_category_bars_count_each_company_once_by_its_ownership_state():
    doc = _map()
    fig = doc["figures"]["categories"]
    layers = {L["id"]: L for L in doc["layers"]}
    assert [L["id"] for L in fig["layers"]] == [L["id"] for L in doc["layers"] if not L.get("indicator_only")]
    ends = []
    for L in fig["layers"]:
        cats = {c["id"]: c for c in layers[L["id"]]["categories"]}
        assert [r["id"] for r in L["rows"]] == list(cats)
        for r in L["rows"]:
            c = cats[r["id"]]
            assert r["n"] == c["n_entities"] == sum(s["n"] for s in r["segs"])
            assert r["leaves"] == [{"name": p["name"], "n": p["n"]} for p in c["leaves"]]  # the dots sit on the category's row
            states = {e["id"]: e["ownership"] for e in c["entities"]}
            assert {s["state"]: s["n"] for s in r["segs"]} == {
                "independent": sum(1 for v in states.values() if v is None),
                "bought": sum(1 for v in states.values() if v in ("acquired", "being_acquired")),
                "closed": sum(1 for v in states.values() if v == "defunct"),
            }
            x = 0.0
            for s in r["segs"]:
                assert abs(s["x"] - x) < 0.06 and 0 <= s["w"] <= 100
                x = s["x"] + s["w"]
            assert abs(x - r["w"]) < 0.06 and x <= 100.05
            ends.append(x)
    assert abs(max(ends) - 100) < 0.06  # the fullest category fills the scale
    assert fig["totals"] == {k: sum(s["n"] for L in fig["layers"] for r in L["rows"] for s in r["segs"] if s["state"] == k)
                             for k in ("independent", "bought", "closed")}


def test_verified_bars_end_at_one_hundred_and_sum_to_the_layer():
    doc = _map()
    fig = doc["figures"]["verified"]
    layers = {L["id"]: L for L in doc["layers"]}
    for r in fig["rows"]:
        assert r["n_verified"] + r["n_unverified"] == r["n"]
        assert abs(r["segs"][0]["w"] + r["segs"][1]["w"] - 100) < 0.06 and r["segs"][0]["x"] == 0
        assert abs(r["share_verified"] - r["n_verified"] / r["n"]) < 1e-9
        if r["id"] != "all":
            L = layers[r["id"]]
            assert r["n"] == L["n_entities"]
            assert r["n_verified"] == len({e["id"] for c in L["categories"] for e in c["entities"] if e["verified"]})
    assert fig["rows"][-1]["id"] == "all" and fig["rows"][-1]["n"] == doc["counts"]["entities"]


def test_coverage_counts_the_parts_in_scope_with_and_without_a_company():
    doc = _map()
    fig = doc["figures"]["coverage"]
    layers = {L["id"]: L for L in doc["layers"]}
    for r in fig["rows"]:
        cats = _in_scope(layers[r["id"]])
        assert r["n_parts"] == sum(c["n_leaves"] for c in cats) == r["n_covered"] + r["n_empty"]
        assert r["n_covered"] == sum(c["leaves_covered"] for c in cats)
        assert r["n_unassigned"] == len({e["id"] for c in cats for e in c["entities"] if e["leaf"] is None})
    assert fig["n_parts"] == sum(r["n_parts"] for r in fig["rows"]) and fig["n_empty"] == sum(r["n_empty"] for r in fig["rows"])
    thin = {t["id"] for t in fig["thin"]}
    assert thin == {c["id"] for L in doc["layers"] if not L.get("indicator_only") for c in _in_scope(L) if c["n_entities"] <= fig["thin_at"]}


def test_the_chain_counts_every_company_on_the_map_once_and_draws_each_unit_where_it_was_judged():
    doc, fig, seed = _chain()
    chain = fig["chain"]
    assert [L["id"] for L in chain["layers"]] == [x.id for x in sorted(seed.layers, key=lambda x: x.order)]
    assert sum(L["n"] for L in chain["layers"]) + chain["n_unfiled"] == chain["n_companies"] == _map()["counts"]["entities"]
    units = {u["id"]: u for u in doc["units"]}
    drawn = {}
    for L in chain["layers"]:
        assert L["n"] == sum(p["n"] for p in L["parts"]) and 0 <= L["h"] <= 100
        for d in vc.DIRECTIONS:
            for m in L["marks"][d]:
                drawn[m["unit"]] = (L["id"], d)
        judged = {u["sublayer"] for u in units.values() if u["layer"] == L["id"]}
        assert {p["id"] for p in L["unjudged"]} == {s.id for s in seed.sublayers if s.layer_id == L["id"]} - judged
        assert L["tally"] == {d: len(L["marks"][d]) for d in vc.DIRECTIONS}
    assert drawn == {u["id"]: (u["layer"], u["direction"]) for u in units.values()}
    assert max(L["h"] for L in chain["layers"]) == 100
    assert chain["n_unjudged_companies"] == sum(p["n"] for L in chain["layers"] for p in L["unjudged"])
    assert chain["tally"] == {d: sum(1 for u in units.values() if u["direction"] == d) for d in vc.DIRECTIONS}


def test_the_chain_names_the_companies_it_files_under_no_part_and_calls_a_layer_judged_whole_the_whole_layer():
    doc, fig, seed = _chain()
    chain = fig["chain"]
    names = {e.id: mm.display(e) for e in seed.entities}
    unfiled = [names[i] for i, sub in mm.primaries(mm.load(), seed.entities, TODAY).items() if sub is None]
    assert chain["unfiled"] == unfiled and len(unfiled) == chain["n_unfiled"]
    subs = {s.id: s.name for s in seed.sublayers}
    marks = {m["unit"]: m["name"] for L in chain["layers"] for d in vc.DIRECTIONS for m in L["marks"][d]}
    for u in doc["units"]:  # a layer judged as a whole does not repeat its own name beneath its heading
        assert marks[u["id"]] == (subs[u["sublayer"]] if u["sublayer"] else "the whole layer")


def test_the_powers_grid_marks_only_what_a_unit_or_a_profile_names():
    doc, fig, seed = _chain()
    grid = fig["powers"]
    short = {e.id: mm.display(e) for e in seed.entities}
    assert grid["cols"] == list(vc.POWERS.values())
    assert [r["unit"] for r in grid["rows"]] == [u["id"] for u in doc["units"]]
    for r, u in zip(grid["rows"], doc["units"]):
        assert [c["power"] for c in r["cells"]] == grid["cols"]
        for c in r["cells"]:
            assert c["named"] == (c["power"] in u["powers"])
            held = [short[p["entity"]] for p in doc["companies"] if p["units"] == [u["id"]] and c["power"] in [x["power"] for x in p["powers"]]]
            assert c["companies"] == held and c["n"] == len(held)
        assert r["n_single"] == sum(1 for p in doc["companies"] if p["units"] == [u["id"]])
    assert grid["n_units_naming"] == sum(1 for u in doc["units"] if u["powers"]) and grid["n_units"] == len(doc["units"])
    assert grid["gloss"] == [vc.POWER_GLOSS[p] for p in grid["cols"]]  # each column head carries its plain meaning


def test_no_company_profiled_in_more_than_one_part_is_counted_in_a_powers_cell():
    doc, fig, seed = _chain()
    grid = fig["powers"]
    short = {e.id: mm.display(e) for e in seed.entities}
    several = [c for c in doc["companies"] if len(c["units"]) > 1]
    assert several  # the case exists, so the rule is exercised
    counted = {n for r in grid["rows"] for c in r["cells"] for n in c["companies"]}
    assert not counted & {short[c["entity"]] for c in several}
    names = {u["id"]: r["name"] for u, r in zip(doc["units"], grid["rows"])}
    assert grid["multi"] == [{"entity": c["entity"], "name": short[c["entity"]], "parts": [names[u] for u in c["units"]],
                              "powers": [x["power"] for x in c["powers"]]} for c in several]


def test_the_rent_rule_is_drawn_step_for_step_and_sends_each_profile_where_the_rule_does():
    doc, fig, _ = _chain()
    rent = fig["rent"]
    rules = futures.rubric()["pools"]["rules"]
    assert len(rent["steps"]) == len(rules)
    placed = [c["entity"] for s in rent["steps"] for c in s["companies"]]
    assert sorted(placed) == sorted(c["entity"] for c in doc["companies"])
    by = {c["entity"]: c for c in doc["companies"]}
    for i, s in enumerate(rent["steps"]):
        assert s["n"] == len(s["companies"]) and s["question"] and s["keeps"]
        for c in s["companies"]:
            a = by[c["entity"]]["rent"]
            assert all(a.get(k) == v for k, v in rules[i]["when"].items())
            assert not any(all(a.get(k) == v for k, v in r["when"].items()) for r in rules[:i])  # the first rule that fits
            assert c["tier"] == futures.TIER_WORDS[a["tier"]]
    assert {c["entity"] for c in rent["steps"][-1]["companies"]} == {e for e, c in by.items() if c["rent"]["pools"] == "users"}


def test_the_rent_rule_never_says_a_company_s_profit_is_kept_by_somebody_else_when_it_may_be_an_owner_itself():
    doc, fig, _ = _chain()
    by = {c["entity"]: c["rent"] for c in doc["companies"]}
    assert futures.POOLS_WORDS["incumbents"] == "incumbent firms"  # the shared words are not this figure's to change
    for s in fig["rent"]["steps"]:
        for c in s["companies"]:
            a = by[c["entity"]]
            assert c["goes_to"] == vc.RENT_GOES_TO.get(a["pools"])
            assert "kept by incumbent" not in c["reads"] and "kept_by" not in c
            if c["goes_to"] and a["tier"] != "none":
                assert c["reads"] == f"a {c['tier']} profit, judged to go to {c['goes_to']}"
            else:
                assert c["reads"] == a["reads"]
    assert "the company named can be one of them" in vc.RENT_GOES_TO["incumbents"]
    assert "can be the company itself" in fig["rent"]["steps"][2]["keeps"]


def test_figure_words_in_the_export_type_no_figure():
    from .test_outlook import NUMBER_WORD

    _, fig, _ = _chain()
    words = [s[k] for s in fig["rent"]["steps"] for k in ("question", "keeps", "why")] + list(vc.DIRECTION_MEANS.values())
    words += list(vc.RENT_GOES_TO.values()) + ["the whole layer"]
    for t in words:
        assert not re.search(r"\d", YEAR.sub("", t)) and not NUMBER_WORD.search(t), t


def test_the_page_has_at_least_five_figures_and_each_states_its_kind_key_and_foot():
    src = TSX.read_text()
    blocks = re.split(r"(?=<Figure\b)", src)[1:]
    assert len(blocks) >= 5, len(blocks)
    for b in blocks:
        head = b[: b.index("\n    >")] if "\n    >" in b else b
        assert re.search(r'id="fig-[a-z-]+"', head), head[:80]
        assert re.search(r"note=\{?(\"[^\"]+\"|KIND_LABEL\.[a-z]+|[A-Z_]+)", head), head[:80]
        assert "keys=" in head and "foot=" in head, head[:80]
        if "KIND_LABEL.chart" in head or "MIXED" in head:
            assert "table=" in head, head[:80]  # a chart's numbers are folded beneath it, never hover-only
    page = PAGE.read_text()
    assert len(blocks) == 5, len(blocks)  # the coverage dots sit on the category rows, not in a figure of their own
    assert "CoverageDots" not in src and "PartDot" in _body(src, "CategoryBars")
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name
    assert page.index("<VerifiedBars ") < page.index("<CategoryBars ")  # how firm the map is comes before the map's counts
    assert "<MarketMap " in page and "<PowersGlossary " in page  # what the page already had stays


def test_the_figures_type_no_digit_but_a_year_and_no_number_word():
    from .test_outlook import NUMBER_WORD

    for f in (TSX, PARTS):
        for line in f.read_text().splitlines():
            if line.lstrip().startswith(("import ", "//")):
                continue
            text = " ".join(re.findall(r'(?:title|aria-label|label|tableLabel)="([^"]*)"', line) + re.findall(r">([^<>{}]+)<", line))
            assert not re.search(r"\d", YEAR.sub("", text)), line.strip()[:140]
            assert not NUMBER_WORD.search(text), line.strip()[:140]


def _body(src: str, fn: str) -> str:
    body = src[src.index(f"export function {fn}") :]
    return body[: body.index("\nexport function ", 1)] if "\nexport function " in body[1:] else body


def _code(f: Path) -> str:
    return "\n".join(line for line in f.read_text().splitlines() if not line.lstrip().startswith("//"))


def test_hatching_is_kept_for_a_judged_length_or_area_and_a_judged_mark_is_solid_and_says_judgement():
    # one convention across pages: this page draws judged yes-or-no marks and placings only, so nothing on it is
    # hatched, and the map's "not yet mapped" (a gap in coverage, not a judgement) is a dashed outline
    for f in (TSX, PARTS, MAP):
        assert "hatch" not in _code(f), f.name
    src = TSX.read_text()
    for const in ("MIXED", "JUDGED", "PLACED"):
        assert "judgement" in re.search(rf'const {const} = "([^"]+)"', src).group(1), const
    for fn, const in (("ChainFigure", "MIXED"), ("PowerGrid", "JUDGED"), ("RentRule", "PLACED")):
        body = _body(src, fn)
        assert f"note={{{const}}}" in body and "judgement" in body[body.index("keys=") : body.index("foot=")], fn
    assert "border-dashed" in MAP.read_text()


def test_the_judgement_figures_say_the_model_that_drafted_them_is_anthropic_s():
    src = TSX.read_text()
    for fn in ("ChainFigure", "PowerGrid", "RentRule"):
        body = _body(src, fn)
        foot = body[body.index("foot=") : body.index("tableLabel=")]
        assert "Claude, a model made by Anthropic" in foot, fn
    # the profit rule's foot says one named person reviewed every profile; hold it to the records
    assert "Alex Brogan reviewed every profile" in _body(src, "RentRule")
    assert {c.get("reviewed_by") for c in vc.load()["companies"]} == {"Alex Brogan"}
    assert all(c.get("judged_by", "").startswith("claude") for c in vc.load()["companies"])


def test_the_profit_rule_prints_no_size_word_beside_a_company_and_says_its_placings_are_judgement():
    body = _body(TSX.read_text(), "RentRule")
    assert "word=" not in body and "c.tier" not in body  # the size stays in the folded table's reading
    assert "Judged to go to" in body and "Judged kept by" not in body
    assert "ranks a company" not in body and "advice to buy or sell" in body
    assert "where each company lands is this site&apos;s judgement" in TSX.read_text() or "where each company lands is this site's judgement" in TSX.read_text()


def test_the_feet_say_what_the_counts_and_marks_do_not_show():
    src = TSX.read_text()
    assert "do not line up with these bars" in _body(src, "ChainFigure")  # the chain's counts against the map's
    assert "not ones it judged unimportant" in _body(src, "ChainFigure")
    assert "do not always agree" in _body(src, "PowerGrid")  # the part's judgement against its companies'
    bars = _body(src, "CategoryBars")
    assert "are a floor" in bars and "drawn as independent" not in bars
    assert "slightly fewer than the placements" in bars and "which holds the remaining parts" in bars
    assert 'independent: "no sale or closure recorded"' in PARTS.read_text()
    assert "nothing here says its entry is wrong" in _body(src, "VerifiedBars")
    assert "RL is reinforcement learning" in re.search(r'const SHORT_NAMES = "([^"]+)"', src).group(1)  # the jargon, glossed
    assert "{SHORT_NAMES}" in _body(src, "ChainFigure") and "{SHORT_NAMES}" in _body(src, "PowerGrid")


def test_the_export_s_figures_are_the_builder_s_and_the_committed_file_has_their_shape():
    from ai_tracker import store as st
    from ai_tracker.analysis.metrics import run_metrics

    s = st.Store()
    s.derived = run_metrics(s.con)  # derived rows are not committed; a fresh checkout computes them
    doc = s._value_chain()
    today = date.today()
    short = {e.id: mm.display(e) for e in s.seed.entities}
    want = vc.figures({k: v for k, v in doc.items() if k != "figures"} | {"sources": []}, s.seed.layers, s.seed.sublayers,
                      mm.primaries(mm.load(), s.seed.entities, today), futures.rubric(), short)
    assert doc["figures"] == want
    names = {c["entity"]: c["name"] for c in doc["companies"]}  # the figures use the short name, the profiles the legal one
    assert any(names[c["entity"]] != c["name"] for st_ in want["rent"]["steps"] for c in st_["companies"])

    def shape(x):
        if isinstance(x, dict):
            return {k: shape(v) for k, v in x.items()}
        return [shape(x[0])] if isinstance(x, list) and x else type(x).__name__

    committed = json.loads((ROOT / "web" / "data" / "value_chain.json").read_text())["figures"]
    live = json.loads(json.dumps(want))
    assert {k: set(v) for k, v in committed.items()} == {k: set(v) for k, v in live.items()}
    assert shape(committed["powers"]["rows"]) == shape(live["powers"]["rows"])
    assert shape(committed["rent"]["steps"][2]) == shape(live["rent"]["steps"][2])
