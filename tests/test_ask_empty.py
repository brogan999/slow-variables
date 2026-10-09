"""Ask never reports an empty answer as an answer: it asks once more for the text, in one call with no tools, and
failing that it fails loudly with what the attempt cost, so the reader sees an error and the day's ledger is right."""

from types import SimpleNamespace as NS

import pytest

from ai_tracker import store as st
from ai_tracker.query import ask as mod
from ai_tracker.query.ask import NoAnswer, Tools, ask

USAGE = NS(input_tokens=1000, output_tokens=100)
TOOL = lambda i: NS(type="tool_use", id=i, name="scenarios", input={})  # noqa: E731
TEXT = lambda t: NS(type="text", text=t)  # noqa: E731


def valid(messages):
    """What the Messages API would refuse: an empty turn, a whitespace-only text block, a tool call left unanswered."""
    for i, m in enumerate(messages):
        assert m["content"], "an empty turn"
        if m["role"] != "assistant":
            continue
        assert all(getattr(b, "type", "") != "text" or b.text.strip() for b in m["content"]), (
            "a whitespace-only text block"
        )
        asked = {b.id for b in m["content"] if getattr(b, "type", "") == "tool_use"}
        after = messages[i + 1]["content"] if i + 1 < len(messages) else []
        answered = (
            {r["tool_use_id"] for r in after if isinstance(r, dict) and r.get("type") == "tool_result"}
            if isinstance(after, list)
            else set()
        )
        assert asked <= answered, "a tool call with no result"


class Fake:
    """Replies from a script of (stop_reason, content) turns; once nudged, replies with `nudged`."""

    def __init__(self, script, nudged=None):
        self.script, self.nudged, self.calls, self.nudges = list(script), nudged, 0, []

    def __getattr__(self, name):
        return self

    def create(self, **kw):
        self.calls += 1
        valid(kw["messages"])
        if kw.get("tool_choice") == {"type": "none"}:
            self.nudges.append(list(kw["messages"]))
            return NS(stop_reason="end_turn", usage=USAGE, content=[TEXT(self.nudged)] if self.nudged else [])
        stop, content = self.script.pop(0) if len(self.script) > 1 else self.script[0]
        return NS(stop_reason=stop, usage=USAGE, content=content)


def run(client, question="what futures are there?"):
    s = st.Store()
    return ask(s, question, Tools(s), client)


def test_an_empty_first_answer_is_asked_for_once_more_in_one_call_without_tools():
    client = Fake(
        [("tool_use", [TOOL("t1")]), ("end_turn", [])], nudged="The outlook's grid holds its futures."
    )
    res = run(client)
    assert res["answer"] == "The outlook's grid holds its futures." and res["status"] == "ok"
    assert len(client.nudges) == 1 and client.calls == 3


def test_a_model_that_only_ever_calls_tools_is_stopped_after_its_rounds_and_one_nudge():
    client = Fake([("tool_use", [TOOL("t")])], nudged="An answer at last.")
    assert run(client)["answer"] == "An answer at last."
    assert client.calls == 13, "twelve rounds, then one call that may not use a tool"


def test_whitespace_a_cut_off_tool_call_or_a_preamble_before_one_are_not_an_answer():
    for content, stop in (
        ([TEXT("\n")], "end_turn"),
        ([TOOL("t2")], "max_tokens"),
        ([TEXT("Let me look that up."), TOOL("t3")], "max_tokens"),
    ):
        client = Fake([("tool_use", [TOOL("t1")]), (stop, content)], nudged="The answer.")
        assert run(client)["answer"] == "The answer.", content


def test_a_reply_that_is_only_a_card_is_not_an_answer():
    card = '```card\n{"kind": "idea"}\n```'
    client = Fake([("end_turn", [TEXT(card)])], nudged="The answer.")
    assert run(client)["answer"] == "The answer."


def test_an_answer_that_stays_empty_fails_loudly_and_says_what_it_cost():
    with pytest.raises(NoAnswer) as e:
        run(Fake([("end_turn", [])]))
    assert e.value.usd > 0, "the failed attempt's spend goes with the error, for the day's ledger"


def test_no_time_left_means_no_nudge(monkeypatch):
    monkeypatch.setattr(mod, "NUDGE_BY_S", -1)
    client = Fake([("end_turn", [])], nudged="Too late.")
    with pytest.raises(NoAnswer):
        run(client)
    assert client.calls == 1


def test_an_empty_retry_on_the_stronger_model_leaves_the_answer_blocked(monkeypatch):
    monkeypatch.setattr(
        mod,
        "check",
        lambda text, records: NS(
            ok=not text.strip(), failures=["a number with no record"], numbers=[], annotated=text
        ),
    )

    class Fades(Fake):
        def create(self, **kw):
            if kw.get("model") == mod.ESCALATE_MODEL:
                self.calls += 1
                return NS(stop_reason="end_turn", usage=USAGE, content=[])
            return super().create(**kw)

    res = run(Fades([("end_turn", [TEXT("A figure of 9 with no record.")])], nudged="Still 9."))
    assert res["status"] == "blocked" and res["answer"].strip()


def test_the_service_ledgers_a_failed_attempt_and_tells_the_reader_why():
    server = open("src/ai_tracker/query/server.py").read()
    assert 'add_spend(getattr(e, "usd", 0.0))' in server and '"no answer"' in server
    assert "too wide to answer in one go" in open("web/src/components/AskShared.tsx").read()
