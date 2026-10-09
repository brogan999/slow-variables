"""Ask never reports an empty answer as an answer: it asks once more for the text, and failing that it fails loudly,
so the reader sees an error with a retry and not a blank reply."""

from types import SimpleNamespace as NS

import pytest

from ai_tracker import store as st
from ai_tracker.query.ask import NoAnswer, Tools, ask

USAGE = NS(input_tokens=1, output_tokens=1)


class Silent:
    """Calls a tool, then stops with no text; answers only when nudged, if `relents`."""

    def __init__(self, relents: bool, dangling: bool = False):
        self.relents, self.dangling, self.turn, self.nudges = relents, dangling, 0, []

    def __getattr__(self, name):
        return self

    def create(self, **kw):
        self.turn += 1
        last = kw["messages"][-1]
        if self.turn == 1:
            return NS(
                stop_reason="tool_use",
                usage=USAGE,
                content=[NS(type="tool_use", id="t1", name="scenarios", input={})],
            )
        if isinstance(last["content"], str) and "no further tool calls" in last["content"]:
            self.nudges.append(kw["messages"])
            text = "The outlook's grid holds its futures." if self.relents else ""
            return NS(
                stop_reason="end_turn", usage=USAGE, content=[NS(type="text", text=text)] if text else []
            )
        if self.dangling:  # cut off mid tool call: a tool_use with no result to follow
            return NS(
                stop_reason="max_tokens",
                usage=USAGE,
                content=[NS(type="tool_use", id="t2", name="scenarios", input={})],
            )
        return NS(stop_reason="end_turn", usage=USAGE, content=[])


def test_an_empty_first_answer_is_asked_for_once_more():
    s = st.Store()
    client = Silent(relents=True)
    res = ask(s, "what futures are there?", Tools(s), client)
    assert (
        res["answer"] == "The outlook's grid holds its futures."
        and res["status"] == "ok"
        and len(client.nudges) == 1
    )
    assert all(m["content"] for m in client.nudges[0]), "an empty turn is never sent back to the model"


def test_a_reply_cut_off_inside_a_tool_call_is_dropped_before_asking_again():
    s = st.Store()
    client = Silent(relents=True, dangling=True)
    res = ask(s, "what futures are there?", Tools(s), client)
    assert res["answer"]
    sent = client.nudges[0]
    assert not any(
        getattr(b, "id", None) == "t2" for m in sent if m["role"] == "assistant" for b in m["content"]
    ), "a tool call with no result cannot be sent back"


def test_an_answer_that_stays_empty_fails_loudly():
    s = st.Store()
    with pytest.raises(NoAnswer):
        ask(s, "what futures are there?", Tools(s), Silent(relents=False))
