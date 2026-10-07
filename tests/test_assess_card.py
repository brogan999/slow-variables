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
SUBLAYERS = {"evals", "agent_infra"}
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
    text, card = split_card(block(CARD), SC, SUBLAYERS)
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
    assert split_card("The prose.\n\n```card\nnot json\n```", SC, SUBLAYERS) == ("The prose.", None)
    assert split_card("Only prose.", SC, SUBLAYERS) == ("Only prose.", None)


def test_a_company_takes_its_own_calls_and_an_unknown_part_is_left_off():
    _t, card = split_card(
        block({**CARD, "kind": "company", "name": "11x", "call": "exposed", "sits": "nowhere"}), SC, SUBLAYERS
    )
    assert (
        card["call"] == "exposed" and card["level"] == "no" and card["name"] == "11x" and card["sits"] is None
    )


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
    res = ask(s, "an idea", Tools(s), CardClient())
    assert "```" not in res["answer"] and res["answer"].startswith("The prose")
    assert res["card"]["call"] == "build on a condition" and len(res["card"]["futures"]) == 8
    assert res["card"]["sits"]["href"] == "/stack/evals"


def test_the_prompt_asks_for_the_card_and_holds_a_company_to_no_ranking():
    p = _system(st.Store())
    assert "```card" in p and "well placed, placed on a condition, or exposed" in p
    assert "never rank it against another company" in p


def test_the_page_draws_the_card_and_computes_nothing():
    card = (WEB / "components" / "AssessCard.tsx").read_text()
    assert "A model&apos;s judgement, not a reading" in card and "card.futures.map" in card
    shared = (WEB / "components" / "AskShared.tsx").read_text()
    assert "a.card ? <AssessCard" in shared


def test_a_company_on_the_map_can_be_put_to_ask():
    lib = (WEB / "lib" / "idea.ts").read_text()
    assert "companyQuestion" in lib and "well placed, placed on a condition, or exposed" in lib
    page = (WEB / "app" / "ask" / "page.tsx").read_text()
    assert "companyQuestion(" in page and "company?:" in page
    mm = (WEB / "components" / "MarketMap.tsx").read_text()
    assert "/ask?${new URLSearchParams({ company:" in mm and "SITE.askOnline" in mm
