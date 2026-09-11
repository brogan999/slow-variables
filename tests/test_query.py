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


def test_records_carry_dispute_text_so_quoted_caveats_verify():
    s = st.Store()
    t = Tools(s)
    row = s.con.execute(
        "SELECT id FROM observation_all WHERE dispute_text IS NOT NULL AND dispute_text <> '' LIMIT 1"
    ).fetchone()
    assert row, "fixture data has a disputed row"
    rec = t.records([("obs", row[0])])[row[0]]
    dispute = s.con.execute("SELECT dispute_text FROM observation_all WHERE id = ?", [row[0]]).fetchone()[0]
    assert dispute[:20] in rec.snippet


def test_derived_records_carry_their_description_and_the_indicator_tool_names_its_row():
    s = st.Store()
    s.derived = run_metrics(s.con)
    t = Tools(s)
    c = next(d for d in s.derived if d.metric == "cross_tracker_concordance")
    assert "-3%" in t.records([("derived", c.id)])[c.id].snippet  # g05: a quoted threshold verifies
    bi = t.indicator("margin_stack_semis_share")["band_input"]
    fit = s.band_fit(next(i for i in s.seed.indicators if i.id == "margin_stack_semis_share"))
    assert bi["derived_id"] == fit.id and bi["dims"] == {"layer_id": "compute_semis"}  # g07: cite this row


def test_sql_tool_cannot_read_files_the_network_or_raw_rows():
    import duckdb
    import pytest

    s = st.Store()
    t = Tools(s)
    for q in [
        "SELECT * FROM read_text('/proc/self/environ')",
        "SELECT * FROM read_text('pyproject.toml')",
        "SELECT * FROM read_csv('https://example.com/x.csv')",
        "SELECT * FROM glob('*')",
    ]:
        assert "Permission Error" in t.sql(q).get("error", ""), q
    for q in [
        "SELECT * FROM observation_all",
        'SELECT * FROM "OBSERVATION_ALL"',
        "SELECT * FROM query('SELECT * FROM observation' || '_all')",
        "SELECT * FROM query_table('observations')",
    ]:
        assert "raw table" in t.sql(q).get("error", ""), q
    assert "error" in t.sql(
        "SELECT getenv('QUERY_TOKEN')"
    )  # a DuckDB upgrade that adds getenv must fail here
    for q in [
        "SET enable_external_access = true",
        "RESET enable_external_access",
        "SET lock_configuration = false",
    ]:
        with pytest.raises(duckdb.Error):
            s.con.execute(q)
    Tools(s)  # a second Tools on a locked store must not raise
    assert t.sql("SELECT count(*) AS n FROM observations")["rows"][0][0] > 0


class ScriptClient:
    """Replays scripted turns: a dict is a tool call, a string is the final text."""

    def __init__(self, turns):
        self.turns = list(turns)

    def __getattr__(self, name):
        if name != "messages":
            raise AttributeError(name)
        return self

    def create(self, **kw):
        from types import SimpleNamespace as NS

        t = self.turns.pop(0) if len(self.turns) > 1 else self.turns[0]
        usage = NS(input_tokens=100, output_tokens=10, cache_creation_input_tokens=1000, cache_read_input_tokens=0)
        if isinstance(t, dict):
            return NS(stop_reason="tool_use", usage=usage, content=[NS(type="tool_use", id="t", **t)])
        return NS(stop_reason="end_turn", usage=usage, content=[NS(type="text", text=t)])


def test_the_five_spec_tools_answer_and_their_ids_verify():
    from ai_tracker.query.citecheck import check

    s = st.Store()
    s.derived = run_metrics(s.con)
    t = Tools(s)
    hits = t.search_evidence("developer speed randomized trial", k=20)
    assert any(h["cite"] and h["cite"].startswith("obs:") for h in hits)
    assert all("BOTTLENECK_PROMPT" not in h.get("doc", "") for h in hits)
    assert all(h["cite"] is None for h in hits if "doc" in h)  # notes are context, never citable
    f = t.fit_trend("metr.*.horizon_50.pt", "2024-01-01")
    assert f["kind"] == "doubling_days" and f["n_points"] >= 3
    assert check(f"It doubles every {f['value_days']:.0f} days [derived:{f['id']}].", t.records([("derived", f["id"])])).ok
    assert "error" in t.fit_trend("no.such.series")
    c = t.concordance()
    assert len(c["trackers"]) == 4 and all(x["fast_band"] for x in c["trackers"]) and c["concordance"]["id"]
    assert t.crosswalk(layer_id="model") and all(r["layer_id"] == "model" for r in t.crosswalk(layer_id="model"))
    assert t.entity("CoreWeave")["id"] == "crwv" and "sec.crwv.revenue.q" in t.entity("crwv")["series"]
    assert "crwv" in t.entity("Corewave")["close_matches"]
    assert t.sql("SELECT created_at FROM status_events LIMIT 1")["rows"]  # stored as UTC, fetchable without pytz


def test_unknown_tools_and_bad_arguments_come_back_as_errors_not_crashes():
    s = st.Store()
    client = ScriptClient([{"name": "drop_tables", "input": {}}, {"name": "entity", "input": {"nom": "x"}}, "No record."])
    res = ask(s, "q", Tools(s), client)
    assert res["status"] == "ok" and [c["tool"] for c in res["tool_calls"]] == ["drop_tables", "entity"]


def test_a_blocked_answer_gets_one_fresh_attempt_and_the_audit_row_holds_no_text():
    from ai_tracker.query.ask import AUDIT_KEYS

    s = st.Store()
    t = Tools(s)
    oid = s.con.execute("SELECT id, value_numeric FROM observations WHERE unit = 'USD' LIMIT 1").fetchone()
    bad = "Revenue was $123,456,789 [obs:" + oid[0] + "]."
    good = "No figure is quoted here [obs:" + oid[0] + "]."
    res = ask(s, "secret question text", t, ScriptClient([bad, bad, good]))
    assert res["status"] == "retried" and res["answer"] == good
    assert set(res["audit"]) == set(AUDIT_KEYS) and "secret" not in json.dumps(res["audit"])
    assert res["usage"]["usd"] > (330 * 2 + 30 * 10) / 1e6  # cache writes are billed, at 1.25x input


def test_golden_survives_a_hallucinated_id_and_flags_informational_questions():
    from ai_tracker.query.ask import golden

    s = st.Store()
    res = golden(s, Tools(s), ScriptClient(["No record [obs:deadbeef00000000]."]))
    assert {r["id"] for r in res if r["informational"]} == {"g14", "g15"}
    assert not any(r["ok"] for r in res if not r["id"] == "g13")


def test_audit_pull_appends_only_new_rows_and_only_the_audit_keys(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS

    import httpx

    from ai_tracker import cli

    monkeypatch.setattr(st, "DATA", tmp_path)
    monkeypatch.setenv("QUERY_TOKEN", "t")
    (tmp_path / "query_log.jsonl").write_text(json.dumps({"time": "2026-09-10T00:00:00+00:00"}) + "\n")
    rows = [
        {"time": "2026-09-09T00:00:00+00:00", "status": "ok"},
        {"time": "2026-09-11T00:00:00+00:00", "status": "ok", "usd": 0.01, "tools": 2, "cites": ["obs:a"],
         "model": "m", "prompt_version": "2", "question": "must not land"},
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: NS(raise_for_status=lambda: None, json=lambda: {"rows": rows}))
    assert cli.cmd_audit_pull(NS()) == 0
    lines = (tmp_path / "query_log.jsonl").read_text().splitlines()
    assert len(lines) == 2 and "must not land" not in lines[1] and json.loads(lines[1])["status"] == "ok"
    monkeypatch.setattr(httpx, "get", lambda *a, **k: (_ for _ in ()).throw(httpx.ConnectError("down")))
    assert cli.cmd_audit_pull(NS()) == 0  # an unreachable service never fails the nightly


def test_citecheck_ignores_cik_digits():
    from ai_tracker.query.citecheck import Record, check

    r = check("Applied Digital (CIK 0001144879) filed $5M [obs:a].", {"a": Record("a", "obs", [5e6], "USD")})
    assert r.ok and r.numbers == ["$5M"]


def test_citecheck_reads_a_written_date_as_a_date():
    from ai_tracker.query.citecheck import Record, check

    rec = {"a": Record("a", "obs", [902.9e9], "USD")}
    for text in ("It reached $902.9B as of Aug 17, 2026 [obs:a].", "It reached $902.9B on 17 August 2026 [obs:a]."):
        r = check(text, rec)
        assert r.ok and r.numbers == ["$902.9B"], (text, r.failures)
    assert not check("Revenue rose 17 percent in May [obs:a].", rec).ok  # a bare number is still a claim
