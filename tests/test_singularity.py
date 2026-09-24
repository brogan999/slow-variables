import re
from datetime import date
from types import SimpleNamespace

from ai_tracker import singularity as sg


def test_the_axis_rises_and_bins_the_ends():
    xs = [sg.x(y) for y in (1900, 1950, 1985, 2020, 2035, 2050, 2075, 2100, 2500)]
    assert xs == sorted(xs) and xs[0] == sg.BEFORE and xs[-1] == sg.AFTER
    assert sg.x(2050) - sg.x(2020) > sg.x(2020) - sg.x(1950)  # the decades that matter get most of the width
    ax = sg.axis()
    assert [t["x"] for t in ax["ticks"]] == sorted(t["x"] for t in ax["ticks"])


def _pred(i, ledger="singularity", url="https://a.example/x", start=None, published=True):
    return SimpleNamespace(id=i, ledger=ledger, claim_url=url, window_start=start, published=published)


SPEC = {
    "sources": [],
    "facts": {"f1": {"indicator": "i1"}},
    "lanes": [{"id": "agi", "label": "AGI", "definition": "d", "forecasts": [{"id": "p1"}], "signposts": ["f1", "i2"]}],
    "questions": [{"id": "q1", "question": "Q?", "reads": "i1"}],
    "worlds": [{"id": "a", "label": "A", "text": "t", "cells": [{"progress": "steady", "rules": "unclear"}]}],
    "fiction": [],
}
OUTLOOK = {"sources": [{"id": "s1", "url": "https://a.example/x"}], "facts": {}, "scenarios": {"cells": [{"progress": "steady", "rules": "unclear"}]}}


def test_a_clean_spec_has_no_problems():
    assert sg.problems(SPEC, [_pred("p1")], OUTLOOK, {"i1", "i2"}, set(), {"p1": None}, date(2026, 9, 24)) == []


def test_problems_catch_each_break():
    today = date(2026, 9, 24)
    spec = {**SPEC, "lanes": [{**SPEC["lanes"][0], "signposts": ["nope"]}]}
    errs = sg.problems(spec, [_pred("p1"), _pred("p2", url="https://b.example")], OUTLOOK, {"i1"}, {"p1"},
                       {"p1": "behind", "p2": None}, today)
    joined = " ".join(errs)
    assert "signpost nope" in joined and "p2 sits on no lane" in joined
    assert "p2 links to a url" in joined and "p1 is listed in compare.yaml" in joined
    late = sg.problems(SPEC, [_pred("p1", start=date(2027, 1, 1))], OUTLOOK, {"i1", "i2"}, set(), {"p1": "behind"}, today)
    assert any("not_yet_testable" in e for e in late)
    bad_world = {**SPEC, "worlds": [{"id": "z", "label": "Z", "text": "t", "cells": [{"progress": "x", "rules": "y"}]}]}
    assert any("no grid cell" in e for e in sg.problems(bad_world, [_pred("p1")], OUTLOOK, {"i1", "i2"}, set(), {}, today))


def test_the_seed_resolves_and_types_no_figure():
    spec = sg.load()
    for t in sg.strings(spec):
        stray = [w for w in re.sub(r"\[(fact|cite|test):[a-z0-9_]+\]", "", t).split() if re.search(r"\d", w)]
        assert all(re.fullmatch(r"\(?(1[6-9]\d\d|2\d\d\d)(s|'s)?[,.;:)]?", w) for w in stray), stray


def test_the_ledger_rows_in_the_sites_words_type_no_figure():
    import yaml

    rows = [r for r in yaml.safe_load(open("seed/predictions.yaml"))["predictions"] if r["ledger"] == "singularity"]
    assert rows
    for r in rows:
        for k in ("claim_text", "operationalisation", "counterevidence"):
            stray = [w for w in r[k].split() if re.search(r"\d", w)]
            assert all(re.fullmatch(r"\(?(1[6-9]\d\d|2\d\d\d)(s|'s)?[,.;:)]?", w) for w in stray), (r["id"], k, stray)
    for x in sg.load()["sources"]:
        q = x.get("quote") or ""
        assert len(q.split()) < 15 and not re.search(r"\d(?!\d{3}\b)", re.sub(r"\b(1[6-9]|2[01])\d\d\b", "", q)), x["id"]
