"""/story (Part 46): the argument as a run of figures reused from the other pages. The page adds no number and no
finding. Its own words are seed text (seed/story.yaml) with no digit and no number word; every panel names its kind and
links to the figure it cuts down; each carry line holds the caveats a review made mandatory on the source page; and a
panel whose figure has no data is left out whole by the export, never by a component."""

import json
import re
from pathlib import Path

import pytest

from ai_tracker import illustrations, story

from .test_outlook import NUMBER_WORD

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
DATA = ROOT / "web" / "data"
PAGE = WEB / "app" / "story" / "page.tsx"
PANEL = WEB / "components" / "StoryPanel.tsx"
CSS = WEB / "app" / "globals.css"
KINDS = {"chart", "model", "illustration", "mixed"}
SPEC = story.load()
PANELS = story.panels(SPEC)  # the acts' panels, then the coda's
BY = {p["id"]: p for p in PANELS}

SCREEN = ["a screen scored by three AI models", "not a claim about what AI can do", "not a forecast"]
# what a staff review made mandatory on the source page (docs/plan.md, the Part named), by panel
MUST = {
    "clocks": ["divided by its own first reading", "leaves out readings"],
    "lag": ["not of any data", "measure nothing"],  # 45c
    "gauges": ["no verdict yet", "casts no vote"],  # 45c
    "readings": ["includes an estimate for OpenAI and Anthropic", "has not scored"],  # 45i
    "whole": [*SCREEN, "all three models pass"],  # 44, 45b
    "screen": [*SCREEN, "the models that voted no", "a floor"],  # 45b
    "perez": ["not data", "published rule"],
    "stack": ["an estimate for OpenAI and Anthropic", "left out", "Microsoft's cloud business alone"],  # staff review of this page
    "labs": ["run-rates", "not audited", "not money paid", "by the same rule", "not the same as having promised nothing"],  # 45f
    "ties": ["not money paid", "records no direction", "a tie, not a flow", "disputed"],  # 45f
    "chain": ["not the size of any market", "a judgement, not a measurement", "made by Anthropic"],  # 45g
    "scale": ["not ranked with the rest", "no meaningful order"],  # 45d
    "anatomy": ["judgement", "no reading tests it whole"],  # 44
    "reach": ["does not mean either side has the better of the argument", "ties to Anthropic", "does not hand the argument to the other side"],  # 45j
    "tally": ["not a final verdict", "no word for wrong"],  # 45a
    "leans": ["judgements, not readings", "made by Anthropic", "no person reviewed each lean", "with extra care"],  # 45a
    "timeline": ["scale is not even", "start of its year", "by the same rule"],  # 45k
    "said": ["not evidence that forecasts are converging", "height is not distance"],  # 45k
    "worlds": ["not ruled out"],  # 45k
    "fiction": ["not forecasts", "not evidence", "no guide to how long a story written today will wait", "not a typical wait"],  # 45k
}


def _carry(p) -> list[str]:
    return [c if isinstance(c, str) else c["text"] for c in p["carry"]]


def _sentences(text: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", text.strip())


def _component(p) -> str:
    return (WEB / "components" / p["file"]).read_text()


def _body(p) -> str:
    return _component(p).split(f"export function {p['figure']}(")[1].split("\nexport function ")[0]


def test_about_twenty_panels_in_the_three_acts_of_the_path():
    nav = (WEB / "lib" / "nav.ts").read_text()
    assert [a["id"] for a in SPEC["acts"]] == re.findall(r'\{ act: "(I+)"', nav) == ["I", "II", "III"]
    assert [a["anchor"] for a in SPEC["acts"]] == ["act-now", "act-money", "act-next"]
    assert 18 <= len(PANELS) <= 22 and len(BY) == len(PANELS) and set(BY) == set(MUST)
    assert all(len(a["panels"]) >= 5 for a in SPEC["acts"])
    # staff review: the densest panel is cut, and Act III ends on the grid that crowns no world; the fiction figure,
    # evidence of nothing, sits in the coda with the imagined plates
    assert "path" not in BY and "BindingPath" not in story.FIGURES and "BindingPath" not in PAGE.read_text()
    assert SPEC["acts"][-1]["panels"][-1]["id"] == "worlds" and [p["id"] for p in SPEC["coda"]] == ["fiction"]
    page = PAGE.read_text()
    coda = page.split('aria-labelledby="coda"')[1]
    assert "doc.coda.map(" in coda and coda.index("doc.coda.map(") < coda.index("doc.closing.strip")


def test_every_panels_component_and_loader_exist_and_the_page_draws_exactly_those():
    data = (WEB / "lib" / "data.ts").read_text()
    for p in PANELS:
        assert f"export function {p['figure']}(" in _component(p), p["id"]
        assert f"export const {p['loader']} = " in data, p["id"]
    assert sorted(story.FIGURES) == sorted(p["figure"] for p in PANELS) and len(set(story.FIGURES)) == len(PANELS)
    page = PAGE.read_text()
    drawn = re.findall(r"^\s+(\w+): <", page.split("const FIGURES")[1].split("};")[0], re.M)
    assert sorted(drawn) == sorted(story.FIGURES)
    assert all(f"<{name} " in page for name in story.FIGURES)


def test_every_panel_links_to_a_real_figure_on_another_page():
    contents = (WEB / "lib" / "contents.ts").read_text()
    for p in PANELS:
        assert p["route"] != "/story" and (WEB / "app" / p["route"].strip("/") / "page.tsx").exists(), p["id"]
        entry = contents.split(f'"{p["route"]}": {{')[1].split("\n  },")[0].split('\n  "/')[0]
        assert f'["{p["anchor"]}", ' in entry or re.search(rf'\bid ?= ?"{p["anchor"]}"', _component(p)), p["id"]
        assert f'<{p["figure"]} ' in (WEB / "app" / p["route"].strip("/") / "page.tsx").read_text(), p["id"]  # it is that page's figure


def test_every_panel_declares_a_kind_that_agrees_with_its_figure():
    old = {"FourClocks": "log scale", "StackPlate": "<StackChart", "TimelinePlate": "a mark sits at the year forecast"}  # charts older than the kit
    for p in PANELS:
        src = _component(p) if p["figure"] == "WorldsGrid" else _body(p)  # its note is a constant above the function
        assert p["kind"] in KINDS, p["id"]
        if p["kind"] == "model":
            assert "KIND_LABEL.model" in src or "schematic" in src, p["id"]
        elif p["kind"] == "chart":
            assert "KIND_LABEL.chart" in src or old[p["figure"]] in src, p["id"]
        elif p["kind"] == "mixed":
            assert "judgement" in src, p["id"]
    assert {p["kind"] for p in PANELS} >= {"chart", "model", "mixed"}
    panel = PANEL.read_text()
    assert "KIND_LABEL" in panel and "mixed" in panel


def test_the_pages_own_words_type_no_digit_and_no_number_word():
    words = story.strings(SPEC)
    assert len(words) > 100
    for t in words:
        assert not re.search(r"\d", t), t
        assert not NUMBER_WORD.search(t), t
        assert "  " not in t and t == t.strip(), t


def test_a_panel_has_exactly_two_sentences_and_a_carry_line():
    for p in PANELS:
        assert len(p["words"]) == 2 and all(len(_sentences(w)) == 1 and w.endswith(".") for w in p["words"]), p["id"]
        assert 2 <= len(p["carry"]) <= 5 and all(c.endswith(".") for c in _carry(p)), p["id"]
        assert not set(p["words"]) & set(_carry(p)), p["id"]
    for a in SPEC["acts"]:
        assert len(_sentences(a["sentence"])) == 1


def test_no_carry_line_drops_a_caveat_a_review_made_mandatory():
    for pid, phrases in MUST.items():
        carry = " ".join(_carry(BY[pid]))
        for phrase in phrases:
            assert phrase in carry, f"{pid}: the carry line has lost '{phrase}'"
    page = " ".join(SPEC["disclosure"])
    for phrase in ("drafted by Claude, a model made by Anthropic", "placed by the same rule", "its long foot and its table", "Hatching",
                   "judgement", "estimate", "not evidence", "measures nothing"):
        assert phrase in page, phrase
    assert "Nothing here is advice" in PAGE.read_text() and 'href="/legal#advice"' in PAGE.read_text()


def test_the_words_never_claim_more_than_the_figure_or_point_at_what_is_hidden():
    for t in story.strings(SPEC):
        assert not re.search(r"\b(proves?(?! (it|the site) wrong)|shows that AI|is certain|table below|the foot|see below)\b", t), t
    # a title that asks a question or describes is not turned into a finding by the sentences beside it
    assert BY["ties"]["words"][0].startswith("The figure asks")
    assert "fails for want" not in " ".join(BY["screen"]["words"])  # 45b: the reason given most often, not "fails that question"
    assert not re.search(r"\b(Anthropic|OpenAI|Amodei|Altman|Musk|Nvidia|NVIDIA)\b", " ".join(w for p in PANELS for w in p["words"]))  # no lab or person singled out


def test_the_wrapper_hides_the_foot_and_the_table_and_nothing_else():
    css = CSS.read_text()
    assert ".story-fig .fig-foot, .story-fig .fig-table { display: none; }" in css
    hidden = [line for line in css.splitlines() if ".story-" in line and "display: none" in line]
    assert len(hidden) == 1 and "fig-key" not in hidden[0] and "fig-note" not in hidden[0] and "fig-head" not in hidden[0]
    panel = PANEL.read_text()
    assert 'className="story-fig' in panel and "{children}" in panel
    assert "text-[14px]" in panel and "text-[12.5px]" not in panel  # the carry line is the page's defence: body size, not fine print
    assert "The full figure, what it leaves out, and its numbers" in panel and "href={href}" in panel
    assert "<Figure" not in panel  # it redraws nothing


def test_a_panel_with_no_data_is_left_out_whole_by_the_export():
    gated = {p["id"]: p["needs"] for p in PANELS if p.get("needs")}
    full = story.build(SPEC, holds=lambda n: True)
    assert [p["id"] for p in story.panels(full)] == [p["id"] for p in PANELS]
    tonight = [p["id"] for p in story.panels(story.build(SPEC))]  # whatever tonight's exports hold, never pinned
    assert set(BY) - set(tonight) <= set(gated) and tonight == [p["id"] for p in PANELS if p["id"] in tonight]
    assert {"clocks", "perez", "stack", "ties", "leans"} <= set(gated) and set(gated.values()) <= set(story.CONDITIONS)
    for pid, name in gated.items():
        thin = story.build(SPEC, holds=lambda n, name=name: n != name)
        ids = [p["id"] for p in story.panels(thin)]
        assert pid not in ids and len(ids) == len(PANELS) - list(gated.values()).count(name), pid
        assert BY[pid]["words"][0] not in json.dumps(thin)  # its sentences go with it
    # the gates are the components' own: what each returns nothing (or a bare line) on
    assert "if (!c) return <p" in _body(BY["clocks"]) and "if (!ties) return null" in _body(BY["ties"])
    assert "if (!fig || !b.leans || !b.judged) return null" in _body(BY["leans"])
    assert "if (!stack.axis || !stack.quarters.length) return <p" in (WEB / "components" / "StackChart.tsx").read_text()
    empty = {"argument.json": {"clocks": {"chart": None}}, "lens/capture.json": {"gross_profit_stack": {"axis": None, "quarters": []}, "figures": {"ties": None}},
             "board.json": {"figures": {"leans": None}, "leans": None, "judged": None}}
    for name in ("clocks_chart", "profit_stack", "ties", "leans"):
        assert story.CONDITIONS[name](lambda f: empty[f]) is False and isinstance(story.CONDITIONS[name](story.read), bool), name
    # two half-empty figures: the clocks' own sentence flagged as no longer what the data shows, and a curve with no marker
    assert 'clocks.holds === false ? " (That is no longer what the latest data shows' in _body(BY["clocks"])
    flag = lambda holds: {"argument.json": {"clocks": {"chart": {"x": []}, "holds": holds}}}  # noqa: E731
    assert [story.CONDITIONS["clocks_chart"](lambda f, h=h: flag(h)[f]) for h in (True, None, False)] == [True, True, False]
    assert BY["perez"]["needs"] == "phase_placed" and 'phase.state === "untestable" ? "One of those series has no reading, so no position is shown."' in _body(BY["perez"])
    phase = lambda state: {"argument.json": {"phase": {"state": state}}}  # noqa: E731
    assert [story.CONDITIONS["phase_placed"](lambda f, s=s: phase(s)[f]) for s in ("frenzy", "installation", "untestable")] == [True, True, False]
    page = PAGE.read_text()
    figures = page.split("const FIGURES")[1].split("};")[0]
    assert "act.panels.map(" in page and "{FIGURES[p.figure]}" in page
    assert not re.search(r"\?|&&|\|\||\.length", figures)  # the page tests no data itself: a missing panel is the export's doing


def test_a_sentence_that_states_tonights_result_is_shown_only_while_it_is_true():
    lines = {c["when"]: (p["id"], c["text"]) for p in PANELS for c in p["carry"] if not isinstance(c, str)}
    assert {k: v[0] for k, v in lines.items()} == {"ages_near": "scale", "most_disputes_untested": "reach", "no_world_signpost_read": "worlds",
                                                   "clocks_stamps_mixed": "clocks", "most_too_early": "tally"}
    assert "measured and some are reported" in lines["clocks_stamps_mixed"][1] and "too early to tell" in lines["most_too_early"][1]
    for name, (_, text) in lines.items():
        assert text in json.dumps(story.build(SPEC, holds=lambda n: True), ensure_ascii=False)
        assert text not in json.dumps(story.build(SPEC, holds=lambda n, name=name: n != name), ensure_ascii=False)
    settle = {"outlook.json": {"figures": {"settle": {"n": 4, "counts": {"no_test": 2, "held": 2}}}}}
    assert story.CONDITIONS["most_disputes_untested"](lambda f: settle[f]) is False  # an even split is not most
    worlds = {"singularity.json": {"figures": {"worlds": {"states": {"both": 3, "holding": 1, "failing": 0}}}}}
    assert story.CONDITIONS["no_world_signpost_read"](lambda f: worlds[f]) is False
    ages = {"argument.json": {"migration": {"figures": {"ages": {"near": 0}}}}}
    assert story.CONDITIONS["ages_near"](lambda f: ages[f]) is False
    stamps = lambda *xs: {"argument.json": {"clocks": {"drawn": [{"stamp": x} for x in xs]}}}  # noqa: E731
    mixed = story.CONDITIONS["clocks_stamps_mixed"]
    assert mixed(lambda f: stamps("measured", "reported", None)[f]) is True
    assert mixed(lambda f: stamps("measured", "measured")[f]) is False and mixed(lambda f: stamps("reported", "estimate")[f]) is False
    early = lambda n, e: {"board.json": {"n": n, "tally": {"too_early": e}}}  # noqa: E731
    assert story.CONDITIONS["most_too_early"](lambda f: early(4, 3)[f]) is True and story.CONDITIONS["most_too_early"](lambda f: early(4, 2)[f]) is False
    # a sentence about a mark drawn only on some nights is worded for the night it is absent
    assert BY["readings"]["words"][1].startswith("Where a mark hangs") and "where there is one" in " ".join(_carry(BY["readings"]))


def test_the_finding_titles_the_story_repeats_are_held_to_the_data():
    # "A small part of the knowledge payroll passes the screen" (census, Part 45b: every finding title has a test)
    assert 'title="A small part of the knowledge payroll passes the screen"' in _body(BY["whole"])
    whole = json.loads((DATA / "census" / "index.json").read_text())["figures"]["whole"]
    shares = {p["part"]: p["share"] for p in whole["parts"]}
    assert min(shares, key=shares.get) == "passes" and shares["passes"] < min(v for k, v in shares.items() if k != "passes")
    # the other finding title on the page has its own test in tests/test_census_figures.py
    assert 'title="For most work that fails the screen' in _body(BY["screen"])
    assert "For most work that fails the screen" in (ROOT / "tests" / "test_census_figures.py").read_text()


def test_no_link_inside_a_reused_figure_is_dead_and_no_id_is_used_twice():
    page = PAGE.read_text()
    for call in ('<ScalePlate scale={a.migration.figures.scale} base="/argument/migration" />',
                 '<DisputeReach doc={o} base="/outlook" />', '<TimelinePlate doc={s} base="/singularity" />', 'id="fig-fiction-lag"',
                 "<Anatomy doc={firmKinds()} picture={false} />"):
        assert call in page, call
    ids = []
    for p in PANELS:
        found = re.findall(r'<Figure\s+id="([a-z-]+)"', _body(p)) + re.findall(r'id = "([a-z-]+)"', _body(p).split(") {")[0])
        ids += ["fig-fiction-lag"] if p["figure"] == "FictionLag" else [i for i in found if not (p["figure"] == "Anatomy" and i == "fig-picture")]
    assert len(ids) == len(set(ids)), sorted(i for i in ids if ids.count(i) > 1)
    assert not {a["anchor"] for a in SPEC["acts"]} & set(ids)


def test_a_new_prop_changes_nothing_on_the_figures_own_page():
    for pid, sig, uses in (
        ("scale", 'base = "" }', "href={`${base}#input-${r.id}`}"),
        ("reach", 'base = "" }', "href={`${base}#position-${c.key}`}"),
        ("timeline", 'base = "" }', "href={`${base}#${f.anchor}`}"),
        ("fiction", 'id = "fig-lag" }', "id={id}"),
        ("anatomy", "picture = true }", "{picture ? "),
    ):
        body = _body(BY[pid])
        assert sig in body.split(") {")[0] and uses in body, pid
    assert "base" not in (WEB / "components" / "BottleneckFigures.tsx").read_text().split("export function BindingPath(")[1].split(") {")[0]  # cut from the story, so its prop went too
    for route, call in (("argument/migration", "<ScalePlate scale={g.scale} />"), ("outlook", "<DisputeReach doc={doc} />"),
                        ("singularity", "<TimelinePlate doc={d} />"), ("singularity", "<FictionLag doc={d} credits={fu.credits} />"), ("firm/kinds", "<Anatomy doc={doc} />")):
        assert call in (WEB / "app" / route / "page.tsx").read_text(), call  # the home pages pass none of them


def test_story_json_holds_words_only_and_is_what_the_seed_builds():
    doc = json.loads((DATA / "story.json").read_text())
    assert doc == json.loads(json.dumps(story.build(SPEC)))

    def leaves(x):
        if isinstance(x, dict):
            for v in x.values():
                yield from leaves(v)
        elif isinstance(x, list):
            for v in x:
                yield from leaves(v)
        else:
            yield x

    assert all(v is None or isinstance(v, str) for v in leaves(doc))
    assert all(not re.search(r"\d", v) for v in leaves(doc) if v and not v.startswith("/"))  # a path may hold a stem's digit
    assert set(doc) == {"eyebrow", "title", "lede", "disclosure", "closing", "acts", "coda", "plates"}
    assert "story.json" in (ROOT / "src" / "ai_tracker" / "store.py").read_text()
    assert 'read<StoryDoc>("story.json")' in (WEB / "lib" / "data.ts").read_text()
    for p in story.panels(doc):
        assert p["href"] == f'{BY[p["id"]]["route"]}#{BY[p["id"]]["anchor"]}' and set(p) == {"id", "figure", "kind", "route", "href", "words", "carry"}


def test_each_act_opens_with_its_picture_and_the_check_holds_the_placement():
    records = illustrations.load()
    stems = story.placed(SPEC)
    assert stems == ["story-act-1", "story-act-2", "story-act-3"]
    assert illustrations.placement_problems(records, {"/story": stems}) == []
    assert all(r["page"] == "/story" and not r.get("waits_for") for r in records if r["stem"].startswith("story-act-"))
    doc = story.build(SPEC)
    rec = {r["stem"]: r for r in records}
    for a, stem in zip(doc["acts"], stems):
        assert a["illustration"] == {"file": f"/illustrations/{stem}.webp", "alt": rec[stem]["alt"], "stage": rec[stem].get("stage")}
    assert [a["illustration"]["stage"] for a in doc["acts"]] == [None, None, "next"]
    page = PAGE.read_text()
    # staff review: on /firm/kinds "next" is agents that keep context, and Act III says what comes next is disputed, so
    # this page does not print the record's stage line; it prints its own
    assert "<Illustration {...act.illustration} stage={null} " in page and "{act.picture_note}" in page
    assert [a["picture_note"] for a in doc["acts"]] == [None, None, "An imagined scene. It is not a forecast, and this site does not say this is what comes next."]
    assert doc["acts"][-1]["picture_note"] in story.strings(SPEC)
    assert page.count("<Illustration ") == 1 and "eager={i === 0}" in page and "/illustrations/" not in page
    assert "story.placed(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()
    assert story.problems(SPEC) == []
    bad = {**SPEC, "acts": [{**SPEC["acts"][0], "panels": [{**PANELS[0], "kind": "photo", "figure": "Nope", "needs": "nothing", "words": ["One."]}]}, *SPEC["acts"][1:]]}
    found = "\n".join(story.problems(bad))
    assert all(x in found for x in ("kind", "Nope", "nothing", "two sentences"))


def test_it_is_a_reference_page_in_the_contents_and_the_menu_and_linked_from_home():
    nav, contents = (WEB / "lib" / "nav.ts").read_text(), (WEB / "lib" / "contents.ts").read_text()
    assert 'EVIDENCE = [["/contents", "Contents"], ["/story", "The story in pictures"], ' in nav
    assert '"/story"' not in nav.split("export const EVIDENCE")[0]  # not a stop, and it lights none
    assert 'REFERENCE = ["/", "/story", ' in contents
    entry = contents.split('"/story": {')[1].split("\n  },")[0]
    assert re.findall(r'\["(act-[a-z]+)", "([^"]+)", "[^"]+\?"\]', entry) == [("act-now", "Now"), ("act-money", "The money"), ("act-next", "Next")]
    page = PAGE.read_text()
    assert "id={act.anchor}" in page
    home = next(line for line in (WEB / "app" / "page.tsx").read_text().splitlines() if 'href="/story"' in line)
    assert "Or see the argument as a run of figures →" in home
    # a cut-down run of figures is not "the whole argument", and the home page does not send a reader here "first"
    meta = page.split("export const metadata")[1].split("};")[0]
    for text in (SPEC["eyebrow"], meta, entry.split("sections")[0], home):
        assert not re.search(r"\bwhole\b|\bfirst\b", text), text


def test_the_page_points_at_the_arguments_own_list_of_what_would_prove_it_wrong():
    closing = SPEC["closing"]
    assert "keeps a written list of what would prove it wrong and tests it every night" in closing["words"]
    assert not re.search(r"\bfail|\bhas already\b", closing["words"] + closing["exits"])  # how a test reads is tonight's result
    page = PAGE.read_text()
    assert 'href="/argument#fig-exits"' in page and "{doc.closing.exits}" in page
    assert 'id="fig-exits"' in (WEB / "components" / "ArgumentFigures.tsx").read_text()


def test_the_closing_plates_are_named_in_the_seed_and_are_ones_the_gallery_holds():
    featured = [x["image"] for x in json.loads((DATA / "futures" / "index.json").read_text())["featured"]]
    assert len(SPEC["plates"]) == len(set(SPEC["plates"])) == 3 and set(SPEC["plates"]) <= set(featured)
    assert story.build(SPEC)["plates"] == SPEC["plates"]
    page = PAGE.read_text()
    assert "doc.plates.flatMap(" in page and "slice(0, 3)" not in page


def test_the_page_is_plain_server_html_with_no_animation_and_no_scroll_script():
    for f in (PAGE, PANEL):
        src = f.read_text()
        assert '"use client"' not in src and not re.search(r"framer|motion|gsap|IntersectionObserver|onScroll|scrollTo|useEffect|animate", src), f
    css = CSS.read_text()
    assert "scroll-snap" not in css
    assert "content-visibility" not in css  # it contains styles, so every panel's figure would restart at "Fig. 1"


@pytest.mark.parametrize("pid", sorted(MUST))
def test_each_panel_is_built_with_its_words(pid):
    doc = story.build(SPEC, holds=lambda n: True)
    p = next(x for x in story.panels(doc) if x["id"] == pid)
    assert p["words"] == BY[pid]["words"] and p["kind"] == BY[pid]["kind"]
    assert all(isinstance(c, str) for c in p["carry"]) and len(p["carry"]) == len(BY[pid]["carry"])
