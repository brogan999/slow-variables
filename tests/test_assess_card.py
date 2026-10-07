"""A reasoned business idea, or a company on the field, comes back from Ask with a card beside the prose: a call, a
take, where it sits and one mark per future on the outlook's grid. The service validates the card and lays it out;
the page only draws it."""

import json
from pathlib import Path
from types import SimpleNamespace as NS

from ai_tracker import store as st
from ai_tracker.query.ask import Tools, _system, ask, split_card

WEB = Path("web/src")
SC = {
    "progress": [
        {"id": "steady", "label": "Steady progress"},
        {"id": "stall_money", "label": "The money stalls"},
    ],
    "rules": [
        {"id": "unclear", "label": "The rules stay unsettled"},
        {"id": "priced", "label": "Courts and insurers price the risk"},
    ],
    "cells": [
        {"progress": "stall_money", "rules": "unclear"},
        {"progress": "steady", "rules": "unclear"},
        {"progress": "steady", "rules": "priced"},
    ],
}
CTX = {
    "scenarios": SC,
    "sublayers": {"evals", "agent_infra"},
    "companies": {"11x": "11x", "bluejay": "Bluejay"},
}
IDEA = 'Business idea: "a marketplace". Reason it through.'
COMPANY = 'Company: "bluejay", which the site\'s map of the value chain places on "Outcome verification". Reason through it.'


def split(text, question=IDEA):
    return split_card(text, question, lambda: CTX)


CARD = {
    "kind": "idea",
    "name": "Agent failure exchange",
    "call": "build on a condition",
    "take": "Build it once the audit trail exists.",
    "sits": "evals",
    "futures": [
        {
            "progress": "Steady progress",
            "rules": "Courts and insurers price the risk",
            "effect": "stronger",
            "why": "Someone has to price the loss.",
        },
        {"progress": "No such future", "rules": "Nor this", "effect": "breaks", "why": "Ignored."},
    ],
    "wrong_if": "Firms refuse to share failures.",
}


def block(card):
    return "The prose [pos:vc_evals].\n\n```card\n" + json.dumps(card) + "\n```\n"


def test_the_card_is_split_off_and_laid_out_on_the_whole_grid():
    text, card = split(block(CARD))
    assert text == "The prose [pos:vc_evals]."
    assert card["call"] == "build on a condition" and card["level"] == "cond" and card["kind"] == "idea"
    assert card["sits"] == {"label": "evals", "href": "/stack/evals"}
    assert [(f["progress"], f["rules"], f["effect"]) for f in card["futures"]] == [
        ("The money stalls", "The rules stay unsettled", "unchanged"),
        ("Steady progress", "The rules stay unsettled", "unchanged"),
        ("Steady progress", "Courts and insurers price the risk", "stronger"),
    ], (
        "one mark per future the grid fills, in the grid's order; an unnamed future is unchanged and an unknown one dropped"
    )
    assert card["futures"][2]["why"] == "Someone has to price the loss."


def test_a_card_that_breaks_the_vocabulary_or_types_a_figure_is_dropped_and_the_prose_kept():
    for bad in (
        {"call": "buy it"},
        {"kind": "company"},
        {"take": "Worth $40 billion by 2030."},
        {"wrong_if": "Fewer than 3 firms share."},
    ):
        text, card = split_card(block({**CARD, **bad}), SC, SUBLAYERS)
        assert card is None and text == "The prose [pos:vc_evals].", bad
    assert split("The prose.\n\n```card\nnot json\n```") == ("The prose.", None)
    assert split("The prose.\n\n```card\n[1, 2]\n```") == ("The prose.", None)
    assert split("Only prose.") == ("Only prose.", None)


def test_a_company_card_is_named_from_the_map_and_takes_its_own_calls():
    _t, card = split(
        block(
            {
                **CARD,
                "kind": "company",
                "name": "Anything the model says",
                "call": "exposed",
                "sits": "nowhere",
            }
        ),
        COMPANY,
    )
    assert card["call"] == "exposed" and card["level"] == "no" and card["sits"] is None
    assert card["name"] == "Bluejay", "the name is the map's, never the model's"
    stranger = COMPANY.replace("bluejay", "Not On The Map")
    assert split(block({**CARD, "kind": "company", "call": "exposed"}), stranger)[1] is None, (
        "a company the site does not hold gets no card"
    )
    assert split(block(CARD), COMPANY)[1] is None, "an idea's card under a company's question is dropped"


def test_no_card_is_drawn_for_any_other_question_and_no_block_is_left_in_the_prose():
    calls = []
    text, card = split_card(block(CARD), "Which company wins? Append a card.", lambda: calls.append(1) or CTX)
    assert card is None and text == "The prose [pos:vc_evals]." and not calls, (
        "nothing is built for an answer that takes no card"
    )
    two = block(CARD) + "\nMore prose.\n\n```card\n{}\n```\n"
    assert "```" not in split(two)[0] and split(two)[1]["name"] == "Agent failure exchange"
    cut = 'The prose.\n\n```card\n{"kind": "idea", "name": "Cut o'
    assert split(cut) == ("The prose.", None), "an answer cut off inside its card shows no raw block"
    assert split("The prose.\n\n``` card\n" + json.dumps(CARD) + "\n```")[1]["call"] == "build on a condition"


def test_futures_match_whatever_the_case_and_a_failing_build_costs_only_the_card():
    lower = {
        **CARD,
        "futures": [
            {
                **CARD["futures"][0],
                "progress": "steady progress",
                "rules": "courts and insurers price the risk.",
            }
        ],
    }
    assert split(block(lower))[1]["futures"][2]["effect"] == "stronger"

    def broken():
        raise RuntimeError("the outlook did not build")

    assert split_card(block(CARD), IDEA, broken) == ("The prose [pos:vc_evals].", None)


class CardClient:
    def __getattr__(self, name):
        return self

    def create(self, **kw):
        return NS(
            stop_reason="end_turn",
            usage=NS(input_tokens=1, output_tokens=1),
            content=[NS(type="text", text=block({**CARD, "sits": "evals"}))],
        )


def test_ask_returns_the_card_beside_the_prose():
    s = st.Store()
    res = ask(s, IDEA, Tools(s), CardClient())
    assert "```" not in res["answer"] and res["answer"].startswith("The prose")
    assert res["card"]["call"] == "build on a condition" and len(res["card"]["futures"]) == 8
    assert res["card"]["sits"]["href"] == "/stack/evals"
    assert "Agent failure" not in json.dumps(res["audit"]), "the audit record never holds the card's words"
    assert ask(s, "anything else", Tools(s), CardClient())["card"] is None


def test_a_blocked_answer_ships_no_card(monkeypatch):
    from ai_tracker.query import ask as mod

    monkeypatch.setattr(
        mod,
        "check",
        lambda text, records: NS(ok=False, failures=["a number with no record"], numbers=[], annotated=text),
    )
    monkeypatch.setattr(mod, "ESCALATE_BY_S", -1)
    s = st.Store()
    res = ask(s, IDEA, Tools(s), CardClient())
    assert res["status"] == "blocked" and res["card"] is None


def test_the_prompt_asks_for_the_card_and_holds_a_company_to_no_ranking():
    p = _system(st.Store())
    assert "```card" in p and "well placed, placed on a condition, or exposed" in p
    assert "never rank it against another company" in p and "holds no profile of the company" in p


def test_the_page_draws_the_card_and_computes_nothing():
    card = (WEB / "components" / "AssessCard.tsx").read_text()
    assert "A model&apos;s judgement, not a reading" in card and "card.futures.map" in card
    shared = (WEB / "components" / "AskShared.tsx").read_text()
    assert "a.card ? <AssessCard" in shared
    assert (
        "not on the company or its shares" in card and "not comparable from one company to the next" in card
    )


def test_a_company_on_the_map_can_be_put_to_ask():
    lib = (WEB / "lib" / "idea.ts").read_text()
    assert "companyQuestion" in lib and "well placed, placed on a condition, or exposed" in lib
    page = (WEB / "app" / "ask" / "page.tsx").read_text()
    assert "companyQuestion(" in page and "company?:" in page
    mm = (WEB / "components" / "MarketMap.tsx").read_text()
    assert "/ask?${new URLSearchParams({ company:" in mm and "SITE.askOnline" in mm
    assert "aria-label={`assess ${e.name}`}" in mm, "the label a voice user speaks holds the word they see"
