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
    rec = t.records([("obs", row[0])])[f"obs:{row[0]}"]
    dispute = s.con.execute("SELECT dispute_text FROM observation_all WHERE id = ?", [row[0]]).fetchone()[0]
    assert dispute[:20] in rec.snippet


def test_derived_records_carry_their_description_and_the_indicator_tool_names_its_row():
    s = st.Store()
    s.derived = run_metrics(s.con)
    t = Tools(s)
    c = next(d for d in s.derived if d.metric == "cross_tracker_concordance")
    assert "-3%" in t.records([("derived", c.id)])[f"derived:{c.id}"].snippet  # g05: a quoted threshold verifies
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
    for q in [  # every spelling of the raw table fails: the SQL database does not contain it
        "SELECT * FROM observation_all",
        'SELECT * FROM "OBSERVATION_ALL"',
        "SELECT * FROM query('SELECT * FROM observation' || '_all')",
        """SELECT count(*) FROM "query"('SELECT * FROM observation'||'_all')""",
        "SELECT count(*) FROM query/**/('SELECT * FROM observation'||'_all')",
        "SELECT * FROM json_execute_serialized_sql(json_serialize_sql('SELECT * FROM observation'||'_all'))",
    ]:
        assert "error" in t.sql(q), q
    n = s.con.execute("SELECT count(*) FROM observations").fetchone()[0]
    assert t.sql("SELECT count(*) FROM observations")["rows"] == [[n]]
    assert t.sql("SELECT count(*) FROM venture_rounds")["rows"][0][0] > 0
    for view in (
        "hyperscaler_capex_ttm",
        "dc_sites",
    ):  # the views three saved formulas read must run in the console too
        assert "error" not in t.sql(f"SELECT count(*) FROM {view}"), view
    assert "error" in t.sql(
        "SELECT getenv('QUERY_TOKEN')"
    )  # a DuckDB upgrade that adds getenv must fail here
    for q in [
        "SET enable_external_access = true",
        "RESET enable_external_access",
        "SET lock_configuration = false",
    ]:
        for con in (s.con, t.pub):
            with pytest.raises(duckdb.Error):
                con.execute(q)
    Tools(s)  # a second Tools on a locked store must not raise
    assert t.sql("SELECT count(*) AS n FROM observations")["rows"][0][0] > 0


class ScriptClient:
    """Replays scripted turns: a dict is a tool call, a string is the final text."""

    def __init__(self, turns):
        self.turns = list(turns)
        self.models = []

    def __getattr__(self, name):
        if name != "messages":
            raise AttributeError(name)
        return self

    def create(self, **kw):
        from types import SimpleNamespace as NS

        self.models.append(kw["model"])
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
    assert check(f"It doubles every {f['value']:.0f} days [derived:{f['id']}].", t.records([("derived", f["id"])])).ok
    assert "error" in t.fit_trend("no.such.series")
    h = t.fit_trend("metr.*.horizon_50.pt", "2024-01-01", "hyperbolic")  # the brief's second model, and the AIC to compare them
    assert h["kind"] == "divergence_year" and h["unit"] == "calendar year" and h["id"] != f["id"]
    assert f["aic"]["hyperbolic"] == h["aic"]["this"] and "error" in t.fit_trend("metr.*.horizon_50.pt", None, "ord")
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
    assert {r["id"] for r in res if r["informational"]} == {"g14", "g15", "g17", "g18", "g19", "g20"}
    assert not any(r["ok"] for r in res if r["id"] not in ("g16",))


def test_audit_pull_appends_only_new_rows_and_only_the_audit_keys(tmp_path, monkeypatch):
    from types import SimpleNamespace as NS

    import httpx

    from ai_tracker import cli

    monkeypatch.setattr(st, "DATA", tmp_path)
    monkeypatch.setenv("QUERY_TOKEN", "t")
    (tmp_path / "query_log.jsonl").write_text(json.dumps({"time": "2026-09-10T00:00:00+00:00"}) + "\n")
    rows = [
        {"time": "2026-09-09T00:00:00+00:00", "status": "ok"},
        {"time": "2026-09-11T00:00:00+00:00", "status": "ok", "usd": 0.01, "tools": 2, "cites": ["obs:0123456789abcdef", "obs:my-secret.example.com", "ind:metr_horizon_50", "ind:hello_secret"],
         "model": "m", "prompt_version": "2", "question": "must not land"},
    ]
    monkeypatch.setattr(httpx, "get", lambda *a, **k: NS(raise_for_status=lambda: None, json=lambda: {"rows": rows}))
    assert cli.cmd_audit_pull(NS()) == 0
    lines = (tmp_path / "query_log.jsonl").read_text().splitlines()
    assert len(lines) == 2 and "must not land" not in lines[1] and json.loads(lines[1])["status"] == "ok"
    assert json.loads(lines[1])["cites"] == ["obs:0123456789abcdef", "ind:metr_horizon_50"]
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


def test_store_reads_agree_across_threads():
    from concurrent.futures import ThreadPoolExecutor

    s = st.Store()
    n = len(s.observations("*"))
    with ThreadPoolExecutor(4) as ex:  # the query service answers each request on its own thread
        counts = list(ex.map(lambda _: len(s.observations("*")), range(24)))
    assert set(counts) == {n}


def test_a_citation_token_that_resolves_to_no_record_never_reaches_the_audit_row():
    s = st.Store()
    t = Tools(s)
    oid = s.con.execute("SELECT id FROM observations LIMIT 1").fetchone()[0]
    text = f"Noted [obs:my-secret.example.com] and [obs:{oid}]."  # a visitor can make the model echo anything
    res = ask(s, "q", t, ScriptClient([text]))
    assert res["audit"]["cites"] == [f"obs:{oid}"] and [c["id"] for c in res["citations"]] == [oid]
    assert "secret" not in json.dumps(res["audit"])


def test_an_indicator_record_carries_its_own_reading_and_status_reason():
    s = st.Store()
    s.derived = run_metrics(s.con)
    t = Tools(s)
    ind = next(i for i in s.seed.indicators if i.id == "btos_firm_use")
    value, _as_of, _ids, _tier = s.band_input(ind)
    rec = t.records([("ind", "btos_firm_use")])["ind:btos_firm_use"]
    assert value in rec.values and rec.snippet == s.current("btos_firm_use").reason  # the card's own number verifies


def test_a_blocked_answer_retries_on_the_stronger_model_and_is_billed_at_its_rate():
    from ai_tracker.query.ask import ESCALATE_MODEL, MODEL

    s = st.Store()
    t = Tools(s)
    oid, value = s.con.execute("SELECT id, value_numeric FROM observations WHERE unit = 'USD' LIMIT 1").fetchone()
    bad = "Revenue was $123,456,789 [obs:" + oid + "]."
    good = "No figure is quoted here [obs:" + oid + "]."
    c = ScriptClient([bad, bad, good])
    res = ask(s, "q", t, c)
    assert res["status"] == "retried" and res["model"] == ESCALATE_MODEL and res["audit"]["model"] == ESCALATE_MODEL
    assert c.models[:2] == [MODEL, MODEL] and c.models[-1] == ESCALATE_MODEL  # only the fresh attempt escalates
    assert value is not None


def test_fit_trend_never_fits_a_projection_or_a_row_epoch_withdrew(monkeypatch):
    from datetime import date, timedelta

    s = st.Store()
    day = date.today()

    def row(i: int, v: float, days: int, ns: str = "epoch_dc", disputed: bool = False) -> dict:
        return {
            "id": f"o{i}", "series_key": f"{ns}.x.power_mw.pt", "unit": "MW", "value_numeric": v,
            "as_of_date": day + timedelta(days=days), "disputed": disputed, "source_ns": ns,
        }  # fmt: skip

    built = [row(1, 100.0, -720), row(2, 200.0, -360), row(3, 400.0, -1)]
    monkeypatch.setattr(
        s, "observations", lambda series: built + [row(4, 9000.0, 400), row(5, 1.0, -30, disputed=True)]
    )
    f = Tools(s).fit_trend("epoch_dc.x.power_mw.pt")
    assert (
        f["n_points"] == 3 and 300 < f["value"] < 420
    )  # doubling about yearly: the projection and the withdrawn row are out
    monkeypatch.setattr(
        s,
        "observations",
        lambda series: [
            row(i, v, d, ns="epoch", disputed=True)
            for i, v, d in ((1, 1.0, -720), (2, 2.0, -360), (3, 4.0, -1))
        ],
    )
    assert (
        Tools(s).fit_trend("epoch.x.power_mw.pt")["n_points"] == 3
    )  # elsewhere a disputed figure still stands


def test_a_model_error_never_logs_or_returns_the_question():
    from ai_tracker.query.server import model_error

    class APIError(Exception):
        request_id = "req_1"

    question = "what is my salary at Acme"
    line, payload = model_error(APIError(f"bad request: {question}"))
    assert question not in line and question not in json.dumps(payload)
    assert line == "ask failed: APIError request_id=req_1" and payload["detail"] == "APIError"


def _tools_with_board():
    s = st.Store()
    s.derived = run_metrics(s.con)
    s.semantic_tables()
    s.prediction_table()
    return Tools(s)


def test_the_outlook_tools_cite_writers_claims_and_predictions_and_the_ids_verify():
    from ai_tracker.query.citecheck import check

    t = _tools_with_board()
    cells = t.scenarios()["cells"]
    assert cells and all(isinstance(c["consistent_with_tonight"], bool) for c in cells)
    src = next(a["cite"] for c in cells for a in c["argued_by"])
    sign = next(g for c in cells for g in c["signposts"])
    assert "[" not in sign["text"]  # tokens rendered or dropped, never shown raw
    hits = t.claims("open models catch up margins", k=3)
    assert hits[0]["cite"].startswith("pos:") and all("[fact:" not in h["case"] for h in hits)
    claim = next(c for h in hits for c in h["claims"] if c["tested_against"])
    kind, cid = claim["cite"].split(":")
    ok = f"Tonight it is tested against {claim['tested_against']} [claim:{cid}]."
    assert check(ok, t.records([(kind, cid)])).ok
    skind, sid = src.split(":")
    assert t.records([(skind, sid)])[src].snippet and t.href(skind, sid) == f"/outlook#source-{sid}"
    assert t.href("pos", "commodity") == "/outlook#position-commodity"
    pid = t.pub.execute("SELECT id FROM predictions LIMIT 1").fetchone()[0]
    assert t.records([("pred", pid)]) and t.href("pred", pid)
    assert t.detail("claim", cid)["snippet"] and t.detail("pred", pid)["label"] and "2027-" not in t.detail("pred", pid)["label"][-12:]


def test_prose_records_match_numbers_only_as_whole_tokens():
    from ai_tracker.query.citecheck import Record, check

    recs = {"c1": Record("c1", "claim", [], "", "Adoption stays below 15% by 2030, far short of 150 firms.")}
    assert check("It stays below 15% [claim:c1].", recs).ok
    assert not check("It stays below 5% [claim:c1].", recs).ok  # 5 sits inside 15 and 150
    assert not check("It stays below 15x [claim:c1].", recs).ok  # the unit must match too
    assert not check("Some 20 firms [claim:c1].", recs).ok  # 20 sits inside 2030


def test_the_company_card_carries_rounds_indicators_and_leaning_predictions():
    from ai_tracker.query.citecheck import check

    t = _tools_with_board()
    card = t.entity("Harvey")
    r = card["venture_rounds"][0]
    oid = r["cite"].split(":")[1]
    assert check(f"It raised ${r['usd'] / 1e6:.0f}M [obs:{oid}].", t.records([("obs", oid)])).ok
    assert card["layer_indicators"] and all(p["cite"].startswith("pred:") for p in card["predictions"])
    assert "error" in t.entity("No Such Company Ltd")


def test_the_rent_rubric_derives_where_rent_pools_by_the_fixed_rules():
    t = Tools(st.Store())
    assert set(t.rent_rubric()) == {"inputs", "pools", "tiers"}
    easy_copy = dict(appropriability="weak", complementary_assets="specialised", asset_owner="incumbents")
    r = t.rent_rubric(**easy_copy, rent_kind="switching_cost", durability="medium")
    assert (r["rent_pools_with"], r["tier"]) == ("incumbents", "moderate")
    assert t.rent_rubric(appropriability="weak", complementary_assets="generic")["tier"] == "none"
    assert "error" in t.rent_rubric(appropriability="loose")


def test_history_is_trimmed_and_follow_ups_are_split_off_before_the_check():
    from ai_tracker.query.ask import HISTORY_TURNS, _conversation, split_followups

    turns = [{"q": f"q{i}", "a": "a" * 5000} for i in range(6)] + [{"q": "blank", "a": "  "}]
    (msg,) = _conversation("now", turns)
    body = msg["content"]
    assert msg["role"] == "user" and body.endswith("The question now: now")  # never stands as the model's own turn
    assert body.count("Q: ") == HISTORY_TURNS - 1 and "Q: q2" not in body and "blank" not in body and "a" * 1501 not in body
    assert _conversation("now", None) == [{"role": "user", "content": "now"}]
    body, qs = split_followups("The answer.\n\nFollow-ups:\n- Why?\n- Is 47% of work gone?\n- What next?\n- Who else?\n")
    assert body == "The answer." and qs == ["Why?", "What next?", "Who else?"]  # an unchecked number never shows
    assert split_followups("Just an answer.") == ("Just an answer.", [])
    s = st.Store()
    res = ask(s, "q", Tools(s), ScriptClient(["No record.\n\nFollow-ups:\n- Which layer?"]), history=turns)
    assert res["followups"] == ["Which layer?"] and res["answer"] == "No record."


def test_a_prose_citation_needs_the_whole_token_and_kinds_never_overwrite_each_other():
    from ai_tracker.query.citecheck import Record, check

    bill = {"src:b": Record("b", "src", [], "", "Colorado SB26-189, issue 129, every 122 days")}
    for bad in ("$189B [src:b].", "$129B [src:b].", "$122B [src:b]."):
        assert not check(f"Revenue will be {bad}", bill).ok
    assert check("It runs every 122 days [src:b].", bill).ok
    test_line = {"claim:c": Record("c", "claim", [0.5], "share", "most projects, tested against 50%")}
    assert check("The line is 50% [claim:c].", test_line).ok
    assert not check("The line is 1% [claim:c].", test_line).ok  # no loose tolerance on a test line
    t = _tools_with_board()
    shared = t.pub.execute("SELECT id FROM predictions WHERE kind = 'outlook' AND test_fact IS NOT NULL LIMIT 1").fetchone()[0]
    recs = t.records([("claim", shared), ("pred", shared)])
    assert {f"claim:{shared}", f"pred:{shared}"} <= set(recs)  # same id, two records
    assert not any(x in recs[f"claim:{shared}"].snippet for x in ("[fact:",))
