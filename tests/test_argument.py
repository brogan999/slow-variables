import re
from datetime import date
from types import SimpleNamespace

from ai_tracker import argument as ar
from ai_tracker import store as st

YEAR = re.compile(r"\(?(1[6-9]\d\d|20\d\d)s?[,.;:)]?")


def test_essays_and_plain_sentences_type_no_number():
    spec = ar.load()
    texts = [p.read_text() for p in ar.ESSAYS.values()]
    texts += (
        [v["sentence"] for v in spec["slow_variables"]]
        + [e["text"] for e in spec["exits"]]
        + [spec["phase"]["rule"]]
    )
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
        "c": [SimpleNamespace(as_of_date=date.fromisoformat(d), value=v) for d, v in capex],
        "f": [SimpleNamespace(as_of_date=date.fromisoformat(d), value=v) for d, v in fin],
    }
    return SimpleNamespace(derived_for=lambda m, dims=None: rows[m])


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
