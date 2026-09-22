import re
from datetime import date
from types import SimpleNamespace

from ai_tracker import argument as ar
from ai_tracker import store as st

YEAR = re.compile(r"\(?(1[6-9]\d\d|20\d\d)s?[\"”]?[,.;:)]?")  # a year may close a quotation


def _migration_strings(spec: dict) -> list[str]:
    """Every sentence a reader sees on /argument/migration that is not the essay file itself."""
    import yaml

    m, t = spec["migration"], yaml.safe_load(ar.TIGHTNESS.read_text())
    out = [p["claim"] + " " + p["text"] for p in m["predictions"]]
    out += [r["label"] for r in m["strip"]["rows"]] + [
        sp["because"] for r in m["strip"]["rows"] for sp in r["spans"]
    ]
    out += [v for k, v in t["rules"].items() if k.endswith("rationale")] + list(
        t["rules"]["reasons"].values()
    )
    out += [k["name"] + " " + k["tight_means"] for k in t["kinds"]]
    for i in t["inputs"]:
        out += [i["name"], i["what"], i.get("reads", ""), i.get("ceiling_rationale", "")]
        out += [i["withheld"]["because"]] if "withheld" in i else []
        for g in i.get("gauges") or []:
            out += [g["label"], g.get("scale_rationale", ""), (g.get("unfed") or {}).get("because", "")]
    return [x for x in out if x]


def test_essays_and_plain_sentences_type_no_number():
    spec = ar.load()
    texts = [p.read_text() for p in ar.ESSAYS.values()]
    texts += (
        [v["sentence"] for v in spec["slow_variables"]]
        + [e["text"] for e in spec["exits"]]
        + [spec["phase"]["rule"]]
    )
    texts += _migration_strings(spec)
    for t in texts:
        stray = [w for w in re.sub(r"\[(fact|plate):[a-z0-9_]+\]", "", t).split() if re.search(r"\d", w)]
        assert all(YEAR.fullmatch(w) for w in stray), (
            stray
        )  # a figure belongs to a [fact:] token, a year may stand


def test_every_token_resolves_and_every_fact_links_to_its_records():
    s = st.Store()
    errors, _ = ar.problems(s)
    assert errors == []
    for k, f in ar.facts(s, ar.load()).items():
        assert f is None or (f["obs_ids"] and f["href"].startswith("/")), k


def test_a_fact_without_data_is_attention_not_an_error(monkeypatch):
    s = st.Store()
    spec = ar.load()
    spec["facts"]["capex_to_revenue"] = {
        "metric": "capex_to_revenue_stack",
        "dims": {"nope": "x"},
        "expect": {"gte": 1},
    }
    spec["facts"]["hours_assisted"]["expect"] = {
        "gt": 1
    }  # a share can never exceed one: the sentence no longer holds
    monkeypatch.setattr(ar, "load", lambda: spec)
    errors, notes = ar.problems(s)
    assert errors == []
    assert any("capex_to_revenue has no reading" in n for n in notes)
    assert any("hours_assisted no longer meets" in n for n in notes)


def _fake(capex, fin):
    rows = {
        "c": [SimpleNamespace(as_of_date=date.fromisoformat(d), value=v, input_observation_ids=[]) for d, v in capex],
        "f": [SimpleNamespace(as_of_date=date.fromisoformat(d), value=v, input_observation_ids=[]) for d, v in fin],
    }
    return SimpleNamespace(
        derived_for=lambda m, dims=None: rows[m], _chart_sources=lambda ids, metric=None: {"sources": []}
    )


SPEC = {"phase": {"capex": "c", "financing": "f", "rule": "r"}}


def test_phase_rule_table_and_the_two_quarter_rule():
    assert ar._raw_phase(1.2, 5, None) == "installation"
    assert ar._raw_phase(0.4, 3, 5) == "deployment"
    assert ar._raw_phase(0.4, 3, None) == "turning_point"  # no year-ago reading: deployment cannot be shown
    assert ar._raw_phase(0.8, 5, 1) == "turning_point"
    q = ["2025-03-31", "2025-06-30", "2025-09-30", "2025-12-31", "2026-03-31"]
    fin = [(d, 10.0) for d in q] + [
        ("2024-12-31", 10.0),
        ("2024-09-30", 10.0),
        ("2024-06-30", 10.0),
        ("2024-03-31", 10.0),
    ]
    one_off = ar.phase(_fake(list(zip(q, [2, 2, 0.8, 2, 2])), fin), SPEC)
    assert [h["state"] for h in one_off["history"]] == [
        "installation"
    ] * 5  # a single odd quarter changes nothing
    held = ar.phase(_fake(list(zip(q, [2, 2, 0.8, 0.8, 0.8])), fin), SPEC)
    assert [h["state"] for h in held["history"]][-3:] == ["installation", "turning_point", "turning_point"]
    assert ar.phase(_fake([], fin), SPEC)["state"] == "untestable"


ADVICE = re.compile(
    r"own it|double down|size as|enter when|exit when|stop when|don't buy|you are late|inflecting|\bbets?\b|\bbuy\b(?! it\b)",
    re.I,
)


def test_the_migration_page_predicts_and_never_advises():
    spec = ar.load()
    text = ar.ESSAYS["migration"].read_text() + " ".join(_migration_strings(spec))
    hits = [m.group(0) for m in ADVICE.finditer(text) if m.group(0).lower() != "buy"]
    assert hits == [], hits  # "what the labs buy" is a description; nothing here tells a reader what to do
    assert (
        "twenty-three" in text and len(__import__("yaml").safe_load(ar.TIGHTNESS.read_text())["inputs"]) == 23
    )


def _mig_store(values: dict[str, float], fetched: dict[str, date] | None = None):
    rows = {
        m: [SimpleNamespace(as_of_date=d, value=v, input_observation_ids=["o1"])]
        for m, (d, v) in values.items()
    }
    logs = [
        SimpleNamespace(source_id=k, ok=True, finished_at=SimpleNamespace(date=lambda d=d: d))
        for k, d in (fetched or {}).items()
    ]
    return SimpleNamespace(
        derived_for=lambda m, dims=None: rows.get(m, []),
        metric_spec=lambda m: {"unit": "ratio"},
        seed=SimpleNamespace(indicators=[]),
        fetchlog=logs,
    )


def test_a_prediction_holds_fails_or_cannot_be_tested_and_a_stale_reading_tests_nothing():
    today = date(2026, 9, 21)
    block = {
        "facts": {
            "gap": {"metric": "gap", "expect": {"gt": 2}, "max_age_days": 120},
            "now": {"metric": "now", "expect": {"lte": "then"}, "max_age_days": 200},
            "then": {"metric": "then"},
        },
        "predictions": [
            {"id": "a", "when": "now", "claim": "c", "text": "t", "test": {"fact": "gap", "gt": 2}},
            {"id": "b", "when": "next", "claim": "c", "text": "t", "test": {"fact": "now", "gt": "then"}},
            {"id": "c", "when": "watch", "claim": "c", "text": "t"},
        ],
    }
    fresh = _mig_store(
        {"gap": (date(2026, 9, 20), 4.4), "now": (date(2026, 6, 30), 3.0), "then": (date(2025, 6, 30), 4.0)}
    )
    f = ar.facts(fresh, block, today)
    assert (f["gap"]["holds"], f["now"]["holds"], f["gap"]["href"]) == (
        True,
        True,
        "/query#gap",
    )  # never a bare /query
    assert [p["state"] for p in ar.predictions(block, f)] == ["holding", "failing", "untestable"]
    old = _mig_store(
        {"gap": (date(2026, 1, 1), 4.4), "now": (date(2026, 6, 30), 5.0), "then": (date(2025, 6, 30), 4.0)}
    )
    f = ar.facts(old, block, today)
    assert f["gap"]["stale"] is True and f["gap"]["holds"] is None  # a frozen series would hold for ever
    assert [p["state"] for p in ar.predictions(block, f)] == ["untestable", "holding", "untestable"]
    fell = ar.facts(_mig_store({"gap": (date(2026, 9, 20), 1.9)}), block, today)
    assert ar.predictions(block, fell)[0]["state"] == "failing"


def test_a_price_list_is_as_fresh_as_its_last_fetch():
    today = date(2026, 9, 21)
    s = _mig_store({}, fetched={"openrouter": date(2026, 9, 20)})
    assert ar._age(s, date(2026, 9, 10), today, "openrouter") == 1  # the last change was eleven days ago
    assert ar._age(s, date(2026, 9, 10), today) == 11 and ar._age(s, date(2027, 1, 1), today) == 0


def test_no_solid_span_passes_today_and_predicted_rows_come_from_the_predictions():
    spec = ar.load()
    st_ = ar.strip(spec["migration"], date(2026, 9, 21))
    assert 2026.7 < st_["now"] < 2026.75
    for r in st_["rows"]:
        assert all(sp["to"] <= st_["now"] and sp["from"] < sp["to"] for sp in r["spans"]), r["id"]
        assert all(
            float(sp["from"]).is_integer() for sp in r["spans"]
        )  # whole years: a half-year edge is invented precision
    assert {r["id"] for r in st_["rows"] if r["predicted"]} == {
        p["row"] for p in spec["migration"]["predictions"] if p.get("row")
    }
    # the export places every span: inside the track, ending by today, and anchored to its row in the table
    for r in st_["rows"]:
        for sp in r["spans"]:
            assert 0 <= sp["left"] and sp["left"] + sp["width"] <= st_["now_x"] + 0.01, (r["id"], sp)
    anchors = [sp["anchor"] for r in st_["rows"] for sp in r["spans"]]
    assert len(set(anchors)) == len(anchors) and all(0 <= t["x"] <= 100 for t in st_["ticks"])


def test_the_clocks_draw_every_point_on_one_axis_and_their_end_labels_never_overlap():
    fake = SimpleNamespace(href_of=lambda ids: f"/series/x#{ids[0]}", stamp_of=lambda ids: "measured")

    def line(i, start, values):
        return {"id": f"c{i}", "series": [{"as_of": f"{start + k}-06-30", "value": v, "obs_ids": [f"o{i}{k}"]} for k, v in enumerate(values)]}

    # three lines ending within a hair of each other, one starting a year before the rest
    drawn = [line(0, 2023, [1, 3, 9]), line(1, 2024, [2, 2.1]), line(2, 2024, [4, 4.2])]
    lay = ar._lay_clocks(fake, drawn)
    pts = [p for d in drawn for p in d["series"]]
    assert all(0 <= p["x"] <= 100 and 0 <= p["y"] <= 100 for p in pts)  # the earliest point is on the axis
    assert drawn[0]["series"][-1]["multiple"] == 9 and drawn[1]["series"][0]["multiple"] == 1
    ys = sorted(d["label_y"] for d in drawn)
    assert all(b - a >= 9.99 for a, b in zip(ys, ys[1:])) and 0 <= ys[0] and ys[-1] <= 100
    assert lay["y"]["log"] and [t["label"] for t in lay["y"]["ticks"]][0] == "1×"


def test_a_malformed_migration_seed_is_an_error_line_never_a_crash(monkeypatch):
    import copy

    s = st.Store()
    base = ar.load()
    for change, want in [
        (
            lambda m: m["facts"]["dc_gap"].update(expect={"ge": 2}),
            "needs exactly one of",
        ),  # no reading needed to catch it
        (
            lambda m: m["predictions"][3]["test"].update(gt="procurement_last_year"),
            "unknown fact procurement_last_year",
        ),
        (lambda m: m["predictions"][0].update(when="soon"), "unknown expect_state or when"),
        (lambda m: m["says"].update(capital=["loose"]), "unknown word loose"),
        (lambda m: m["facts"].update(orphan={"dims": {}}), "names no metric"),
        (lambda m: m["predictions"][0].update(test={"fact": "dc_gap"}), "needs exactly one of"),
        (lambda m: m["strip"]["rows"][0]["spans"][0].update(because="See [fact:dc_gap]."), "token in a span"),
    ]:
        spec = copy.deepcopy(base)
        change(spec["migration"])
        monkeypatch.setattr(ar, "load", lambda spec=spec: spec)
        errors, _ = ar.problems(s)
        assert any(want in e for e in errors), (want, errors)
