import json

from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics
from ai_tracker.query.ask import Tools, ask


def test_sql_tool_is_read_only_and_capped():
    s = st.Store()
    t = Tools(s)
    assert "error" in t.sql("DELETE FROM observation_all")
    assert "error" in t.sql("SELECT 1; SELECT 2")
    r = t.sql("SELECT id, series_key FROM observations")
    assert r["columns"] == ["id", "series_key"] and len(r["rows"]) == 200 and r["truncated"]
    d = t.sql("DESCRIBE observations")
    assert "series_key" in [row[0] for row in d["rows"]]


class FakeClient:
    """Answers with one sql tool call, then prose that cites the row it saw."""

    def __init__(self):
        self.turn = 0

    def __getattr__(self, name):
        if name != "messages":
            raise AttributeError(name)
        return self

    def create(self, **kw):
        from types import SimpleNamespace as NS

        self.turn += 1
        if self.turn == 1:
            return NS(
                stop_reason="tool_use",
                usage=NS(input_tokens=10, output_tokens=5),
                content=[
                    NS(
                        type="tool_use",
                        id="t1",
                        name="sql",
                        input={
                            "query": "SELECT id, value_numeric FROM observations WHERE series_key LIKE 'metr.%.horizon_50.pt' ORDER BY as_of_date DESC LIMIT 1"
                        },
                    )
                ],
            )
        last = kw["messages"][-1]["content"][0]["content"]
        row = json.loads(last)["rows"][0]
        return NS(
            stop_reason="end_turn",
            usage=NS(input_tokens=10, output_tokens=5),
            content=[NS(type="text", text=f"The latest 50% horizon is {row[1] / 60:.1f} h [obs:{row[0]}].")],
        )


def test_ask_loop_cites_and_passes_the_check():
    s = st.Store()
    s.derived = run_metrics(s.con)
    res = ask(s, "latest horizon?", Tools(s), FakeClient())
    assert res["status"] == "ok", res
    assert res["citations"][0]["href"].startswith("/series/metr.")
    assert res["usage"]["usd"] > 0
