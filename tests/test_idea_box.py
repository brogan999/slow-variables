"""A reader's own business idea goes to Ask as one fixed question: the page adds no model, no endpoint and no
arithmetic, so the answer is cite-checked like any other."""

import re
from pathlib import Path

from ai_tracker import store as st
from ai_tracker.query.ask import HISTORY_Q, _system

WEB = Path("web/src")
LIB = (WEB / "lib" / "idea.ts").read_text()
QUESTION = re.search(r"ideaQuestion = [^`]*`([^`]*)`", LIB).group(1)
IDEA_MAX = int(re.search(r"IDEA_MAX = (\d+)", LIB).group(1))


def test_the_idea_question_names_what_ask_must_cover_in_plain_words():
    for part in (
        "value chain",
        "rent rule",
        "futures",
        "what would prove it wrong",
        "build, build on a condition, or don't build alone",
    ):
        assert part in QUESTION, f"the idea question leaves out: {part}"
    assert not re.search(r"\d|[a-z]_[a-z]", QUESTION), (
        "the reader sees this as their question: no figure and no tool name"
    )
    assert QUESTION.startswith('Business idea: "${clip(idea)}"'), (
        "the idea leads and is set off from the instructions"
    )
    assert "Array.from(" in LIB, "the clip never splits a character"


def test_the_idea_fits_the_service_and_survives_as_a_remembered_turn():
    assert len(QUESTION) + IDEA_MAX < 2000  # the service's cap on a question
    assert IDEA_MAX + len('Business idea: "".') <= HISTORY_Q  # a follow-up still carries the whole idea


def test_ask_may_end_a_reasoned_idea_with_a_call():
    p = _system(st.Store())
    assert "no personal recommendation" in p
    assert "A business idea put to you to be reasoned through is judged as a business" in p


def test_the_ask_page_builds_the_question_from_an_idea():
    page = (WEB / "app" / "ask" / "page.tsx").read_text()
    assert "ideaQuestion(" in page and "idea?:" in page


def test_the_box_is_a_plain_form_on_the_businesses_page_and_hides_with_ask():
    box = (WEB / "components" / "IdeaBox.tsx").read_text()
    assert '"use client"' not in box, "a plain form: it needs no script"
    assert 'action="/ask"' in box and 'name="idea"' in box and "maxLength" in box
    assert "if (!SITE.askOnline) return null" in box
    assert "a model" in box and "not reviewed" in box, "the box says who answers"
    assert "aria-describedby" in box, "the description and the caution belong to the field"
    assert "Leave out anything confidential" in box and "page address" in box
    assert "<IdeaBox" in (WEB / "app" / "value-chain" / "opportunities" / "page.tsx").read_text()


def test_a_question_in_a_link_is_disclosed_and_not_crawled():
    assert "arrives in a link" in (WEB / "app" / "legal" / "page.tsx").read_text()
    assert (
        'disallow: "/ask?"' in (WEB / "app" / "robots.ts").read_text()
    )  # a crawler following a link would spend on an answer
