"""The figures on /capture (Part 45f). Every number they draw is a record's, summed and laid out by the export; the
model of the page's rule is seed text with no number; the page only places what the export wrote."""

import json
import os
import re
from pathlib import Path

import pytest

from ai_tracker import capture_figures as cf
from ai_tracker import store as st
from ai_tracker.analysis.metrics import run_metrics

REPO = Path(__file__).resolve().parents[1]
TSX = [REPO / "web/src/components/CaptureFigures.tsx", REPO / "web/src/components/diagrams/capture.tsx"]
PAGE = REPO / "web/src/app/capture/page.tsx"
YEAR = re.compile(r"\b(19|20)\d\d\b")
OLD_KEYS = {"as_of", "verdict", "what_would_change", "recent_status_events", "gross_profit_stack", "margin_stack", "layers"}


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    cwd = os.getcwd()
    os.chdir(REPO)
    s = st.Store()
    s.derived = run_metrics(s.con)
    out = tmp_path_factory.mktemp("web")
    s.export(out)
    os.chdir(cwd)
    return s, json.loads((out / "lens" / "capture.json").read_text())


def test_the_export_adds_one_block_and_changes_nothing_else(world):
    s, cap = world
    assert set(cap) == OLD_KEYS | {"figures"}
    assert set(cap["figures"]) == {"gauges", "year", "labs", "ties", "concentration", "rule"}
    cards = {i.id: s._card(i) for i in s.seed.indicators}
    assert cap["layers"] == json.loads(json.dumps([s._capture_layer(layer, cards) for layer in s.seed.layers], default=str))


def test_every_capture_gauge_is_one_mark_under_the_word_it_reads_tonight(world):
    s, cap = world
    g = cap["figures"]["gauges"]
    layers = {layer["id"]: layer for layer in cap["layers"]}
    assert [row["id"] for row in g["layers"]] == [layer.id for layer in s.seed.layers]
    for row in g["layers"]:
        want = {i.id for i in s.seed.indicators if i.layer_id == row["id"] and i.published and i.direction_rule}
        marks = [m for grp in row["groups"] for m in grp["marks"]]
        assert {m["id"] for m in marks} == want and len(marks) == len(want) == row["n"]
        assert row["status"] == layers[row["id"]]["status"] and row["href"] == f"/layers/{row['id']}"
        assert [grp["word"] for grp in row["groups"]] == [w["id"] for w in g["words"]]
        cards = {c["id"]: c for c in layers[row["id"]]["indicators"]}
        for grp in row["groups"]:
            assert grp["n"] == len(grp["marks"])
            for m in grp["marks"]:
                assert m["status"] == cards[m["id"]]["status"] and m["href"] == f"/indicators/{m['id']}"
                assert cf.word(m["status"]) == grp["word"]
    assert g["n"] == sum(row["n"] for row in g["layers"]) > 20


def test_the_year_figure_reads_the_stacks_newest_quarter_and_the_one_a_year_before(world):
    _, cap = world
    rows = cap["figures"]["year"]["rows"]
    assert {r["stack"] for r in rows} == {"gross_profit", "operating_income"}
    for key, name in (("gross_profit_stack", "gross_profit"), ("margin_stack", "operating_income")):
        quarters = {q["as_of"]: q for q in cap[key]["quarters"] if q["parts"]}
        newest = quarters[max(quarters)]
        mine = [r for r in rows if r["stack"] == name]
        assert [r["id"] for r in mine] == [p["id"] for p in newest["parts"]]
        for r, p in zip(mine, newest["parts"]):
            assert r["now"]["value"] == p["value"] and r["now"]["obs_ids"] == p["obs_ids"] and r["now"]["href"] == p["href"]
            assert r["now"]["estimated"] == p["estimated"] and abs(r["now"]["x"] - 100 * p["value"]) < 0.01
            assert r["estimated"] == (r["now"]["estimated"] or bool(r["then"] and r["then"]["estimated"]))
            if r["then"]:
                assert r["then"]["as_of"] == f"{int(r['now']['as_of'][:4]) - 1}{r['now']['as_of'][4:]}"
                old = next(o for o in quarters[r["then"]["as_of"]]["parts"] if o["id"] == r["id"])
                assert r["then"]["value"] == old["value"] and 0 <= r["then"]["x"] <= 100 and r["change"]
                assert r["then"]["estimated"] == old["estimated"]
        assert abs(sum(r["now"]["value"] for r in mine) - 1) < 1e-6  # the parts of one quarter are the whole of it
    assert any(r["then"] for r in rows)


def test_an_estimated_share_names_the_dated_run_rates_it_rests_on_at_both_ends(world):
    s, cap = world
    rows = [r for r in cap["figures"]["year"]["rows"] if r["estimated"]]
    assert rows and all(r["then"] and r["then"]["estimated"] for r in rows)  # the earlier dot is an estimate too
    obs = {o["id"]: o for o in s.observations("epoch.*.revenue_run_rate_usd.pt")}
    for r in rows:
        for end in (r["now"], r["then"]):
            want = sorted((o["as_of_date"].isoformat(), o["id"]) for i in end["obs_ids"] if (o := obs.get(i)))
            assert want and sorted((b["as_of"], b["obs_ids"][0]) for b in end["basis"]) == want
            for b in end["basis"]:
                assert b["as_of"] <= end["as_of"] and b["when"] == f"{obs[b['obs_ids'][0]]['as_of_date']:%B %Y}" and b["name"]
    assert all("basis" not in r["now"] for r in cap["figures"]["year"]["rows"] if not r["estimated"])


def test_each_labs_bars_are_its_own_records_and_the_ratio_is_the_sites_metric(world):
    s, cap = world
    labs = cap["figures"]["labs"]
    ratio = {}
    for d in s.derived_for("lab_recoupment_ratio"):
        ratio[d.dims["entity"]] = d  # sorted by date, so the last one stands
    assert {r["subject"] for r in labs["rows"]} == set(ratio) and len(labs["rows"]) >= 4
    obs = {o["id"]: o for o in s.observations("epoch.*.revenue_run_rate_usd.pt", "epoch.*.round_equity_usd.pt", "circular.*")}
    top = max(b["value"] for r in labs["rows"] if not r["thin"] for b in (r["run_rate"], r["equity"], r["promised"]) if b)
    for r in labs["rows"]:
        d = ratio[r["subject"]]
        assert obs[r["run_rate"]["obs_ids"][0]]["measure"] == "revenue_run_rate_usd" and r["run_rate"]["value"] == obs[r["run_rate"]["obs_ids"][0]]["value_numeric"]
        assert abs(r["equity"]["value"] - sum(obs[i]["value_numeric"] for i in r["equity"]["obs_ids"])) < 1
        assert sorted(r["run_rate"]["obs_ids"] + r["equity"]["obs_ids"]) == sorted(d.input_observation_ids)
        assert abs(r["run_rate"]["value"] / r["equity"]["value"] - d.value) < 1e-9
        assert (r["ratio"] is None) == r["thin"] and (r["thin"] or abs(r["ratio"]["value"] - d.value) < 1e-9)
        assert r["equity"]["n"] == len(r["equity"]["obs_ids"]) and r["run_rate"]["stamp"] == s.stamp_of(r["run_rate"]["obs_ids"])
        if r["promised"]:
            rows = [obs[i] for i in r["promised"]["obs_ids"]]
            assert abs(r["promised"]["value"] - sum(o["value_numeric"] for o in rows)) < 1 and r["promised"]["n"] == len(rows)
            assert all(cf.KIND[o["series_key"].split(".")[2].removesuffix("_usd")] == "buy" for o in rows)
        for b in (r["run_rate"], r["equity"], r["promised"]):
            if b and r["thin"]:
                assert "w" not in b  # no bar is drawn for a lab that is not compared
            elif b:
                assert abs(b["w"] - 100 * b["value"] / top) < 0.01 and 0 <= b["w"] <= 100
                assert b["small"] == (b["w"] < cf.SLIVER)  # a bar too thin to read is said in words, not drawn as a sliver
    # even-handed: the labs are in one order by one rule, and a frontier lab with no run-rate on record is named
    assert [r["equity"]["value"] for r in labs["rows"]] == sorted((r["equity"]["value"] for r in labs["rows"]), reverse=True)
    frontier = {e.id: e for e in s.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)}
    drawn = {r["id"] for r in labs["rows"]}
    assert {"openai", "anthropic"} <= drawn and len(labs["absent"]) == len(set(frontier) - drawn) > 0


def test_a_lab_with_too_little_on_record_is_listed_without_a_multiple_and_none_is_dropped_silently(world):
    from datetime import date

    s, cap = world
    labs = cap["figures"]["labs"]
    newest = max(date.fromisoformat(r["run_rate"]["as_of"]) for r in labs["rows"])
    rounds: dict[str, list[dict]] = {}
    for o in s.observations("epoch.*.round_equity_usd.pt"):
        rounds.setdefault(o["subject"], []).append(o)
    for r in labs["rows"]:
        at = date.fromisoformat(r["run_rate"]["as_of"])
        few, stale = r["equity"]["n"] < cf.MIN_ROUNDS, (newest - at).days > cf.STALE_DAYS
        assert r["thin"] == (few or stale) and r["thin_why"] == ("rounds" if few else "stale" if stale else None)
        after = [o for o in rounds[r["subject"]] if o["as_of_date"] > at]  # a round on record that the date rule cuts out
        if after:
            assert abs(r["later"]["value"] - sum(o["value_numeric"] for o in after)) < 1 and r["later"]["n"] == len(after)
            assert sorted(r["later"]["obs_ids"]) == sorted(o["id"] for o in after)
        else:
            assert r["later"] is None
        # the date and who said it are beside the bars, from the record: Epoch's own source type and grade
        o = next(o for o in s.observations("epoch.*.revenue_run_rate_usd.pt") if o["id"] == r["run_rate"]["obs_ids"][0])
        told = json.loads(o["raw_snippet"])
        assert r["run_rate"]["when"] == f"{at:%B %Y}" and r["run_rate"]["said"] == cf.SAID.get(told["Source type"], "other") != "other"
        if not r["thin"]:  # the key's claim: hatched is a press report graded likely, solid is the company's own word
            assert (r["run_rate"]["stamp"] == "estimate") == (r["run_rate"]["said"] == "press")
    assert len([r for r in labs["rows"] if not r["thin"]]) >= 2 and any(r["thin"] for r in labs["rows"])
    # a lab with a run-rate and no round at all is named, not dropped
    ents = {e.id: e for e in s.seed.entities}
    bare = {o["entity_id"] or o["subject"] for o in s.observations("epoch.*.revenue_run_rate_usd.pt") if o["subject"] not in rounds}
    assert sorted(labs["no_rounds"]) == sorted(cf.display(ents[i]) if i in ents else i for i in bare) and labs["no_rounds"]
    # the foot says Anthropic's figure is a press report like the other hatched bars
    assert next(r for r in labs["rows"] if r["id"] == "anthropic")["run_rate"]["said"] == "press"


def test_what_a_lab_has_signed_up_to_pay_counts_only_deals_in_which_it_is_the_payer(world):
    s, cap = world
    led = {r["id"]: r for r in s._ledger()}
    assert cf.KIND["backstop"] == "backstop"  # a guarantee of unsold capacity is not read as a purchase without being named
    seen = 0
    for r in cap["figures"]["labs"]["rows"]:
        for i in (r["promised"] or {"obs_ids": []})["obs_ids"]:
            row = led[i]
            assert cf.KIND[row["instrument"]] == "buy" and cf.payer(row) == r["id"]
            assert row["parties"][-1]["entity_id"] == r["id"] or cf.PAYER.get(row["series_key"]) == r["id"]
            seen += 1
        if r["promised"]:
            assert r["promised"]["href"] == "/ledger" and r["equity"]["href"].startswith("/series/epoch.")
    assert seen > 5


def test_the_ties_add_up_to_the_ledgers_counted_total_and_every_band_sits_inside_its_ends(world):
    s, cap = world
    t = cap["figures"]["ties"]
    total = s.derived_for("circular_commitments_total")[-1]
    assert t["total"]["value"] == total.value and sorted(t["total"]["obs_ids"]) == sorted(total.input_observation_ids)
    assert abs(sum(p["value"] for p in t["pairs"]) - total.value) < 1
    assert sorted(i for p in t["pairs"] for i in p["obs_ids"]) == sorted(total.input_observation_ids)
    assert all(p["kind"] in ("buy", "stake") and p["n"] == len(p["obs_ids"]) for p in t["pairs"])
    led = {r["id"]: r for r in s._ledger()}
    for p in t["pairs"]:  # a backstop is a purchase only where the module names the series; otherwise credit behind the other side
        for i in p["obs_ids"]:
            if led[i]["instrument"] == "backstop":
                assert p["kind"] == ("buy" if led[i]["series_key"] in cf.BACKSTOP_BUY else "stake")
    for side in ("left", "right"):
        nodes = t[side]
        assert abs(sum(n["value"] for n in nodes) - total.value) < 1
        for a, b in zip(nodes, nodes[1:]):
            assert a["y"] + a["h"] <= b["y"] + 1e-6  # nodes never overlap
        assert nodes[0]["y"] >= 0 and nodes[-1]["y"] + nodes[-1]["h"] <= 100.001
        for n in nodes:
            mine = [b for b in t["bands"] if b[side] == n["id"]]
            assert abs(sum(b["value"] for b in mine) - n["value"]) < 1 and abs(sum(b[f"{side}_h"] for b in mine) - n["h"]) < 0.05
            assert all(n["y"] - 0.01 <= b[f"{side}_y"] and b[f"{side}_y"] + b[f"{side}_h"] <= n["y"] + n["h"] + 0.05 for b in mine)
    assert abs(sum(b["value"] for b in t["bands"]) - total.value) < 1 and all(b["d"].startswith("M") for b in t["bands"])
    labs = {e.id for e in s.seed.entities if any(m.is_primary and m.sublayer_id == "frontier_labs" for m in e.memberships)}
    assert {n["id"] for n in t["right"]} - {"none"} <= labs
    # the title asks which companies both fund the labs and sell to them and which do only one: the flag on a named
    # company is exactly "a band of each kind to the same lab", checked against the pairs it is made of, and both sorts exist
    kinds: dict[tuple[str, str], set[str]] = {}
    for b in t["bands"]:
        if b["left"] not in ("other", "none"):
            kinds.setdefault((b["left"], b["right"]), set()).add(b["kind"])
    both = {left for (left, _), k in kinds.items() if k == {"buy", "stake"}}
    named = {n["id"] for n in t["left"]} - {"other", "none"}
    assert both == {n["id"] for n in t["left"] if n["both"]} and both and named - both
    for left in named:
        by_lab: dict[str, set[str]] = {}
        for p in t["pairs"]:
            if p["a"] == left and p["lab"]:
                by_lab.setdefault(p["b"], set()).add(p["kind"])
        assert (left in both) == any(k == {"buy", "stake"} for k in by_lab.values())
    # a disputed deal is drawn apart: the disputed bands hold exactly the counted rows the ledger marks disputed
    disputed = sorted(i for i in total.input_observation_ids if led[i]["disputed"])
    assert disputed and sorted(i for b in t["bands"] if b["disputed"] for i in b["obs_ids"]) == disputed
    assert sum(p["disputed"] for p in t["pairs"]) == len(disputed) and len({(b["left"], b["right"], b["kind"], b["disputed"]) for b in t["bands"]}) == len(t["bands"])
    # the share of everything drawn that each lab is party to is the export's, and the largest is said near the drawing
    for n in t["right"]:
        assert abs(n["share"] - n["value"] / total.value) < 1e-9
    assert t["right"][0]["id"] != "none" and t["right"][0]["value"] == max(n["value"] for n in t["right"])
    # the foot's claims: this total is every signed deal, so larger than the gauge's trailing year; Meta is filed with the
    # labs and Alphabet is here as an investor; a lab outside the frontier group falls in the bottom band
    assert total.value > s.derived_for("circular_commitments_new_4q")[-1].value
    assert "meta" in {n["id"] for n in t["right"]} and "googl" in {p["a"] for p in t["pairs"] if p["lab"]}
    assert any(p["b"] == "mistral" and not p["lab"] for p in t["pairs"])
    assert t["total"]["when"] == f"{total.as_of_date:%B %Y}"
    # the foot says a few very large deals make up most of it: the three largest pairings are more than half
    by_pair: dict[tuple[str, str], float] = {}
    for p in t["pairs"]:
        by_pair[(p["a"], p["b"])] = by_pair.get((p["a"], p["b"]), 0) + p["value"]
    assert sum(sorted(by_pair.values(), reverse=True)[:3]) > total.value / 2


def test_the_concentration_strip_places_each_index_at_its_latest_reading(world):
    s, cap = world
    cards = {c["id"]: c for layer in cap["layers"] for c in layer["indicators"]}
    rows = cap["figures"]["concentration"]["rows"]
    ids = [i for _, group in cf.CONCENTRATION for i in group]
    assert len(rows) >= 3 and [r["id"] for r in rows] == [i for i in ids if i in cards]
    assert {r["id"]: r["group"] for r in rows} == {i: g for g, group in cf.CONCENTRATION for i in group if i in cards}
    for r in rows:
        latest = cards[r["id"]]["latest"]
        assert cards[r["id"]]["unit"] == "index" and r["value"] == latest["value"] and r["obs_ids"] == latest["obs_ids"]
        assert abs(r["x"] - 100 * r["value"]) < 0.01 and 0 <= r["x"] <= 100 and r["as_of"] == latest["as_of"]
        assert r["counts"] == next(i.definition for i in s.seed.indicators if i.id == r["id"])


def test_each_index_is_drawn_beside_the_lowest_it_could_read(world):
    """An index over n firms cannot read below equal shares, one over n: the strip draws that floor, so a dot is read
    against its own floor and never ranked against another row's."""
    s, cap = world
    lab = "CASE split_part(raw_snippet, '/', 1) WHEN 'meta-llama' THEN 'meta' WHEN 'qwen' THEN 'alibaba' ELSE split_part(raw_snippet, '/', 1) END"
    count = {"firms": "count(DISTINCT subject)", "labs": f"count(DISTINCT {lab})", "models": "count(*)"}
    for r in cap["figures"]["concentration"]["rows"]:
        (n,) = s.con.execute(f"SELECT {count[r['of']]} FROM observations WHERE id IN (SELECT unnest(?))", [r["obs_ids"]]).fetchone()
        assert r["n"] == n > 1 and abs(r["floor_x"] - 100 / n) < 0.01
        assert r["floor_x"] <= r["x"] <= 100 and r["when"]
    by = {r["id"]: r for r in cap["figures"]["concentration"]["rows"]}
    assert by["lab_hhi"]["of"] == "labs" and by["model_token_concentration"]["of"] == "models" and by["semis_hhi"]["of"] == "firms"
    # the lab count follows the metric's own grouping: the index recomputed over those groups is the reading drawn
    (hhi,) = s.con.execute(
        f"SELECT sum(sh * sh) FROM (SELECT sum(value_numeric) / sum(sum(value_numeric)) OVER () AS sh FROM observations WHERE id IN (SELECT unnest(?)) GROUP BY {lab})",
        [by["lab_hhi"]["obs_ids"]],
    ).fetchone()
    assert abs(hhi - by["lab_hhi"]["value"]) < 1e-9


def test_the_rule_is_seed_text_and_no_word_on_the_page_types_a_number(world):
    from .test_outlook import NUMBER_WORD

    _, cap = world
    spec = cf.load()
    assert cap["figures"]["rule"] == spec["rule"] and len(spec["rule"]["outcomes"]) == 3 and len(spec["rule"]["questions"]) == 2
    for t in cf.strings(spec):
        assert not re.search(r"\d", t) and not NUMBER_WORD.search(t), t
    for f in TSX:
        src = f.read_text()
        for text in re.findall(r">([^<>{}=;]+)<", src):  # the words between tags: what a reader sees
            assert not re.search(r"\d", YEAR.sub("", text)), text.strip()[:140]
        for line in src.splitlines():
            assert not NUMBER_WORD.search(line), line.strip()[:140]


def test_every_figure_says_what_kind_it_is_and_carries_a_key_a_foot_and_its_numbers():
    src = TSX[0].read_text()
    figures = re.findall(r"<Figure\b(.*?)\n    >", src, re.S)
    assert 4 <= len(figures) <= 7
    for f in figures:
        assert "note={KIND_LABEL." in f or "note={`${KIND_LABEL." in f, f[:80]
        assert "keys={" in f and "foot={" in f, f[:80]
        assert "KIND_LABEL.model" in f or "table={" in f, f[:80]  # a chart folds its numbers beneath
    page = PAGE.read_text()
    for name in re.findall(r"export function (\w+)", src):
        assert f"<{name} " in page, name
    for kept in ("<FourPlaces ", "<StackPlate ", "<StackChart ", "c.what_would_change", "ChangelogList"):
        assert kept in page, kept
    assert len(re.findall(r"<(FourPlaces|StackPlate|StackChart|\w+Plate|Capture\w+) ", page)) >= 7
    parts = TSX[1].read_text()
    assert "Math." not in src + parts and "hatch" in src  # hatching is kept for an estimate, and says so in the key
    assert "estimate" in src


def test_the_words_claim_only_what_the_records_support():
    """The staff review (6 Oct 2026): what each title, key and foot must say, and the sentences that were untrue."""
    src, page, rule = TSX[0].read_text(), PAGE.read_text(), cf.load()["rule"]
    for said in (
        # labs: regrouped, each bar's basis, who drafted the page
        "beside what investors have put in and what the labs have signed up to pay suppliers", "Too little on record to compare",
        "so no multiple is drawn", "too old to set beside the others", "was raised after this date and is not in the bar",
        "not booked revenue", "marks every such figure as disputed", "in which the lab is the buyer", "so it is a floor",
        "have a run-rate but no funding round", "made by Anthropic", "the model has no figure of its own",
        # ties
        "Which companies both fund the labs and sell to them, and which do only one", "funds and sells", "a tie, not a flow",
        "not money paid", "marked disputed on the ledger", "Of which disputed", "counts only deals signed in the trailing year",
        "Alphabet, which owns a rival lab", "such as Mistral", "Suppliers and investors",
        # concentration
        "How concentrated each layer looks, beside the lowest each index could read", "do not rank one row against another",
        "Among the listed companies that file a segment", "published top table",
        # the model and the year
        "evidence about the rule and not a test of it", "/argument/migration", "an estimate by this site, at either end",
        "not exactly a year apart",
    ):
        assert said in src, said
    for gone in (
        "Every lab is drawn by the same rule", "single month of sales", "not its own", "what it has raised</", "at face", "face value",
        "The same companies fund the labs and sell to them", "the same rows that", "money is promised in both directions",
        "Read the order of the rows", "where it is tested", "ask these same questions", "a layer keeps profit only if",
    ):
        assert gone not in src and gone not in page and gone not in rule["foot"], gone
    assert "do not ask these questions directly" in rule["foot"] and rule["title"].startswith("The rule behind this page:")
    assert "for as long as both answers stay yes" in next(o["text"] for o in rule["outcomes"] if o["id"] == "stays")
    assert "depends on its sales catching up with what it has raised and signed up to pay" in page
    # one colour, one meaning: a payment promised to a supplier is the same colour in the labs figure and the ties figure
    assert 'buy: ["var(--s2)"' in src and '["promised", "var(--s2)"' in src
