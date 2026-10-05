"""A model's judgement in words where the site has no reading (plan Part 39): one seed file, one check, one label."""

from pathlib import Path

import yaml

from ai_tracker import judgements as jd

ROOT = Path(__file__).resolve().parents[1]
MADE = {"model": "claude-opus-5-5", "date": "2026-10-05", "method": "m", "reviewed_by": "a second pass"}
DOC = {
    "made_by": MADE,
    "surfaces": {
        "tightness": {
            "words": {"tight": "probably tight", "slack": "probably slack"},
            "judgements": [{"id": "minerals", "word": "tight", "reason": "Export limits bite, though stockpiles cushion them."}],
        }
    },
}
KNOWN = {"tightness": {"minerals", "grid"}}


def _with(**change):
    j = {**DOC["surfaces"]["tightness"]["judgements"][0], **change}
    return {**DOC, "surfaces": {"tightness": {**DOC["surfaces"]["tightness"], "judgements": [j]}}}


def test_a_judgement_names_a_real_slot_a_word_from_its_surface_and_types_no_figure():
    assert jd.problems(DOC, KNOWN) == []
    for bad in (
        _with(id="nope"), _with(word="severe"), _with(reason=""), _with(reason="About 40% is mined in one country."),
        _with(reason="Output is doubling."), _with(reason="See www.example.org."), _with(reason="Twenty firms supply it."),
    ):
        assert jd.problems(bad, KNOWN), bad
    twice = {**DOC, "surfaces": {"tightness": {**DOC["surfaces"]["tightness"], "judgements": DOC["surfaces"]["tightness"]["judgements"] * 2}}}
    assert jd.problems(twice, KNOWN)
    assert jd.problems({**DOC, "made_by": {}}, KNOWN)
    assert jd.problems({**DOC, "surfaces": {"weather": DOC["surfaces"]["tightness"]}}, KNOWN)  # a surface the site does not have


def test_the_export_gives_each_slot_its_label_and_reason_and_says_who_judged():
    out = jd.build(DOC)
    assert out["made_by"]["model"] == "claude-opus-5-5"
    assert out["surfaces"]["tightness"]["minerals"] == {"word": "tight", "label": "probably tight", "reason": "Export limits bite, though stockpiles cushion them."}
    assert jd.build({}) == {"made_by": None, "surfaces": {}}


def test_the_seeded_judgements_name_real_slots_on_every_surface():
    assert jd.problems(jd.load(), jd.known()) == []


def test_each_surface_shows_its_judgements_through_the_one_labelled_component():
    web = ROOT / "web" / "src"
    comp = (web / "components" / "Judged.tsx").read_text()
    assert "judgement, not a reading" in comp
    for surface, file in (
        ("tightness", "components/MigrationParts.tsx"), ("barriers", "app/bottlenecks/page.tsx"),
        ("atlas", "components/AtlasParts.tsx"), ("indicators", "app/indicators/page.tsx"),
    ):
        assert f'surface="{surface}"' in (web / file).read_text() or f"judged.surfaces.{surface}" in (web / file).read_text(), surface
    store = (ROOT / "src/ai_tracker/store.py").read_text()
    assert "judgement" not in store.split("def prediction_table")[1].split("\n    def ")[0]  # never in what Ask reads
    assert yaml.safe_load((ROOT / "seed" / "judgements.yaml").read_text())["made_by"]["model"]
