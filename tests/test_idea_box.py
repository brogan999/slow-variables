"""A reader's own business idea goes to Ask as one fixed question: the page adds no model, no endpoint and no
arithmetic, so the answer is cite-checked like any other."""

import re
from pathlib import Path

WEB = Path("web/src")


def test_the_idea_question_names_what_ask_must_cover():
    lib = (WEB / "lib" / "idea.ts").read_text()
    for part in ("value_chain", "rent_rubric", "scenarios", "what would prove it wrong", "build, build on a condition, or don't build alone"):
        assert part in lib, f"the idea question leaves out: {part}"
    assert not re.search(r"\d", re.sub(r"//.*", "", lib)), "the idea question types no figure"


def test_the_ask_page_builds_the_question_from_an_idea():
    page = (WEB / "app" / "ask" / "page.tsx").read_text()
    assert "ideaQuestion(" in page and "idea?:" in page


def test_the_box_is_a_plain_form_on_the_businesses_page_and_hides_with_ask():
    box = (WEB / "components" / "IdeaBox.tsx").read_text()
    assert '"use client"' not in box, "a plain form: it needs no script"
    assert 'action="/ask"' in box and 'name="idea"' in box and "maxLength" in box
    assert "if (!SITE.askOnline) return null" in box
    assert "a model" in box and "not reviewed" in box, "the box says who answers"
    assert "<IdeaBox" in (WEB / "app" / "value-chain" / "opportunities" / "page.tsx").read_text()
