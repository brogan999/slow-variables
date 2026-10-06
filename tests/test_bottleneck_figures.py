"""The figures on /bottlenecks (Part 45h) draw only what the map, the barriers list and the judgements already hold:
every count and position is laid out by `bottleneck_map.figures`, which is pure, and the page only places it."""

import copy
import json
import re
from collections import Counter
from pathlib import Path

from ai_tracker import bottleneck_map

from .test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "web" / "data"
TSX = ROOT / "web" / "src" / "components" / "BottleneckFigures.tsx"
PARTS = ROOT / "web" / "src" / "components" / "diagrams" / "bottlenecks.tsx"
PAGE = ROOT / "web" / "src" / "app" / "bottlenecks" / "page.tsx"
CLASSES = ["tight", "moderate", "easing", "unscored", "friction", "friction_unread"]


def _docs():
    return [json.loads((DATA / f).read_text()) for f in ("map.json", "bottlenecks.json", "judgements.json")]


def _rows(doc):
    return [r for g in doc["groups"] for s in g["sections"] for r in s["rows"]]


def _figs():
    doc, barriers, judged = _docs()
    return bottleneck_map.figures(doc, barriers, judged), doc, barriers, judged


def test_the_figures_are_pure_and_change_nothing_the_map_already_exports():
    doc, barriers, judged = _docs()
    shipped = doc.pop("figures")
    before = copy.deepcopy((doc, barriers, judged))
    assert bottleneck_map.figures(doc, barriers, judged) == shipped  # the file on disk is what the builder writes
    assert (doc, barriers, judged) == before
    assert set(doc) == {"stages", "groups", "bets"}


def test_every_row_is_counted_once_by_kind_and_once_at_each_stage_it_acts_on():
    f, doc, _, _ = _figs()
    rows = _rows(doc)
    ids = [u["id"] for s in f["sections"] for u in s["units"]]
    assert sorted(ids) == sorted(r["id"] for r in rows) and f["rows"] == len(rows) == sum(f["tally"].values())
    assert [s["total"] for s in f["sections"]] == [len(s["rows"]) for g in doc["groups"] for s in g["sections"] if s["rows"]]
    cls = {u["id"]: u["cls"] for s in f["sections"] for u in s["units"]}
    assert set(cls.values()) <= set(CLASSES) and Counter(cls.values()) == Counter({k: v for k, v in f["tally"].items() if v})
    # "tight" is the map's own filter for what binds now; a friction outside the chain is never put on that scale
    assert {i for i, c in cls.items() if c == "tight"} == {r["id"] for r in rows if r["focus"] in ("now", "both")}
    assert all((r["reading"]["kind"] == "tally") == cls[r["id"]].startswith("friction") for r in rows)
    assert all((r["reading"]["kind"] == "withheld") == (cls[r["id"]] == "unscored") for r in rows)
    for st, drawn in zip(doc["stages"], f["stages"], strict=True):
        acts = [r["id"] for r in rows if r["cells"].get(st["id"], {}).get("bites")]
        assert drawn["label"] == st["label"] and sorted(u["id"] for u in drawn["units"]) == sorted(acts) and drawn["total"] == len(acts)
        assert [CLASSES.index(u["cls"]) for u in drawn["units"]] == sorted(CLASSES.index(u["cls"]) for u in drawn["units"])
        assert all(u["cls"] == cls[u["id"]] and u["href"] == f"#why-{u['id']}" for u in drawn["units"])
        assert [x["id"] for x in drawn["now"]] == [u["id"] for u in drawn["units"] if u["cls"] == "tight"]
        assert {x["id"] for x in drawn["expected"]} == {r["id"] for r in rows if r["cells"].get(st["id"], {}).get("writers")}
    for part in (*f["stages"], *f["sections"], *f["kinds"]):  # the folded table's counts are the squares drawn
        assert part["counts"] == dict(Counter(u["cls"] for u in part["units"])) and sum(part["counts"].values()) == part["total"]
    chain = [r for r in rows if r["reading"]["kind"] != "tally"]
    assert sum(k["total"] for k in f["kinds"]) == len(chain)
    assert all({r["reading"]["kind_of_tight"] for r in chain if r["id"] in {u["id"] for u in k["units"]}} == {k["id"]} for k in f["kinds"])


def test_how_firm_the_map_is_adds_up_and_every_bar_ends_at_a_hundred():
    f, doc, barriers, judged = _figs()
    rows = _rows(doc)
    bars = {b["id"]: b for b in f["firm"]}
    assert list(bars) == ["chain", "outside", "barriers"]
    for b in bars.values():
        assert [s["key"] for s in b["segs"]] == ["reading", "judged", "blank"]
        assert sum(s["n"] for s in b["segs"]) == b["total"] > 0
        x = 0.0
        for s in b["segs"]:
            assert abs(s["x"] - x) < 1e-6 and s["w"] >= 0
            x += s["w"]
        assert abs(x - 100) < 1e-6
    n = lambda bar, key: next(s["n"] for s in bars[bar]["segs"] if s["key"] == key)  # noqa: E731
    scored = [r for r in rows if r["reading"]["kind"] == "scored"]
    withheld = [r for r in rows if r["reading"]["kind"] == "withheld"]
    assert n("chain", "reading") == len(scored) and bars["chain"]["low"] == sum(r["reading"]["hatched"] for r in scored)
    assert n("chain", "judged") == sum(r["id"] in judged["surfaces"]["tightness"] for r in withheld)
    assert n("chain", "judged") + n("chain", "blank") == len(withheld)
    outside = [r for r in rows if r["reading"]["kind"] == "tally"]
    assert n("outside", "reading") == sum(bool(r["reading"]["instruments"] or r["reading"]["readings"]) for r in outside)
    assert n("outside", "judged") == 0  # no model judges a whole row outside the chain
    assert n("barriers", "reading") == sum(s["watched"] for s in barriers["summary"])
    assert n("barriers", "judged") == sum(not b["related"] and str(b["id"]) in judged["surfaces"]["barriers"] for b in barriers["items"])
    assert bars["barriers"]["total"] == len(barriers["items"])


def test_each_family_draws_its_own_barriers_and_a_judgement_is_never_drawn_as_a_reading():
    f, doc, barriers, judged = _figs()
    words = judged["surfaces"]["barriers"]
    assert [x["total"] for x in f["families"]] == [s["items"] for s in barriers["summary"]]
    assert [x["name"] for x in f["families"]] == [r["name"] for r in _rows(doc) if r["id"].startswith("family_")]
    items = {b["id"]: b for b in barriers["items"]}
    for fam, s in zip(f["families"], barriers["summary"], strict=True):
        assert fam["counts"].get("read", 0) == s["watched"] and sum(fam["counts"].values()) == fam["total"] == len(fam["units"])
        for u in fam["units"]:
            b = items[u["id"]]
            assert b["section"] == s["name"] and u["title"] == b["title"] and u["href"] == f"#b{b['id']}"
            if b["related"]:
                assert u["cls"] == "read" and u["label"] is None
            else:
                j = words.get(str(b["id"]))
                assert (u["cls"], u["label"]) == ((j["word"], j["label"]) if j else ("blank", None))
    assert [w["id"] for w in f["judged_words"]] and {w["id"]: w["label"] for w in f["judged_words"]} == {j["word"]: j["label"] for j in words.values()}
    assert sum(w["n"] for w in f["judged_words"]) == next(s["n"] for b in f["firm"] if b["id"] == "barriers" for s in b["segs"] if s["key"] == "judged")
    assert f["made_by"] == judged["made_by"]


def test_the_expectations_strip_counts_every_claim_listed_under_a_row_in_its_exported_state():
    f, doc, _, _ = _figs()
    rows = [r for r in _rows(doc) if r["claims"]]
    c = f["claims"]
    assert c["states"] == ["holding", "failing", "both", "untestable"]
    assert [r["id"] for r in c["rows"]] == [r["id"] for r in rows]
    for drawn, r in zip(c["rows"], rows, strict=True):
        assert drawn["name"] == r["name"] and drawn["href"] == f"#why-{r['id']}"
        assert {s: [(m["who"], m["href"]) for m in drawn["cells"][s]] for s in c["states"]} == {
            s: [(w["who"], w["href"]) for w in r["claims"] if w["state"] == s] for s in c["states"]
        }
    assert c["tally"] == {s: sum(w["state"] == s for r in rows for w in r["claims"]) for s in c["states"]}
    assert c["total"] == sum(len(r["claims"]) for r in rows) == sum(c["tally"].values())
    assert c["site"] == sum(w["who"].startswith(bottleneck_map.SITE) for r in rows for w in r["claims"])


def test_the_money_strip_places_each_sub_layer_on_one_axis_and_types_no_amount():
    f, doc, _, _ = _figs()
    m = f["money"]
    assert [r["id"] for r in m["rows"]] == [b["sublayer"]["id"] for b in doc["bets"]]
    assert m["ticks"] and all(0 <= t["x"] <= 100 and t["label"] for t in m["ticks"])
    placed = []
    for drawn, b in zip(m["rows"], doc["bets"], strict=True):
        assert drawn["firms"] == b["firms"] and drawn["venture"] == b["venture"]
        assert (drawn["x"] is None) == (b["venture"] is None)
        assert drawn["flip"] == (b["venture"] is not None and drawn["x"] > 60)  # a label never runs off the right edge
        if b["venture"]:
            assert 0 <= drawn["x"] <= 100
            placed.append((b["venture"]["value"], drawn["x"]))
        assert drawn["inputs"] == [next(r["name"] for r in _rows(doc) if r["id"] == i) for i in b["rows"]]
    assert [x for _, x in sorted(placed)] == sorted(x for _, x in placed)  # more money sits further right


def _words(src: str) -> list[str]:
    """What a reader reads in a component: text between tags and the quoted strings left once layout attributes go."""
    src = re.sub(r'^import .*$|^const link = "[^"]*";$', "", src, flags=re.M)
    src = re.sub(r"//.*$", "", src, flags=re.M)
    src = re.sub(r"var\(--[a-z0-9-]+\)|url\(#[a-z0-9-]+\)", "", src)
    src = re.sub(r'\b(className|viewBox|width|height|x|y|x1|x2|y1|y2|d|r|rx|strokeWidth|strokeDasharray|points|id|href|markerEnd|refX|refY|markerWidth|markerHeight|orient)="[^"]*"', "", src)
    src = re.sub(r"className=\{`[^`]*`\}", "", src)
    return re.findall(r">([^<>{}]+)<", src) + re.findall(r'"([^"\n]*)"', src) + re.findall(r"`([^`]*)`", src)


def test_every_figure_states_its_kind_has_a_key_and_a_foot_and_types_no_number():
    src = TSX.read_text()
    figures = re.findall(r'<Figure\s+id="fig-([a-z]+)"\s+title=.*?note=\{?(`[^`]+`|"[^"]+"|KIND_LABEL\.[a-z]+)', src, re.S)
    total = len(re.findall(r"<Figure\b", src))
    assert total == len(figures) >= 5, figures  # none without a stated kind
    assert len(re.findall(r"\bkeys=\{", src)) == total and len(re.findall(r"\bfoot=\{", src)) == total
    assert any("model" in kind for _, kind in figures) and any("chart" in kind for _, kind in figures)
    assert "A model, not a measurement" in (ROOT / "web/src/components/diagrams/kit.tsx").read_text()
    page = PAGE.read_text()
    exported = re.findall(r"export function (\w+)", src)
    assert len(exported) >= 5 and all(f"<{name} " in page for name in exported)  # every figure is on the page
    for keep in ("<BottleneckMap ", "<MapReasons ", "<Bets ", "<Judged "):  # nothing already on the page is dropped
        assert keep in page or keep in src, keep
    for text in _words(src) + _words(PARTS.read_text()):
        assert not re.search(r"\d", re.sub(r"\b(19|20)\d\d\b", "", text)), text
        assert not NUMBER_WORD.search(text), text


def test_hatching_is_kept_for_a_models_judgement_and_the_judgement_is_named_where_it_is_drawn():
    src = TSX.read_text()
    counted = src[src.index("export function MapCounted") : src.index("export function MapFirmness")]
    assert "hatch" not in counted  # rows and their scores are records
    for name in ("MapFirmness", "BarrierFamilies"):
        body = src[src.index(f"export function {name}") :]
        body = body[: body.index("\nexport function ", 1)] if "\nexport function " in body[1:] else body
        assert "hatch" in body and "judgement" in body and "made_by" in body, name
