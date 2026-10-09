"""The future in which access to models splits by country goes on the atlas's dial only once the outlook holds named
writers who argue it, each fetched with its record, and a rival view beside it."""

import json
import re
from pathlib import Path

from ai_tracker import chain_atlas as ca
from ai_tracker.outlook import load as load_outlook
from ai_tracker.outlook import problems as outlook_problems

ROOT = Path(__file__).resolve().parents[1]
OUTLOOK = load_outlook()
SPEC = ca.load()


def test_the_outlook_holds_the_position_its_writers_and_a_rival():
    positions = {p["id"]: p for p in OUTLOOK["positions"]}
    sources = {s["id"]: s for s in OUTLOOK["sources"]}
    held = positions["access_by_state"]
    assert held["attribution"] == "author" and len(held["holders"]) >= 2
    for h in held["holders"]:
        s = sources[h]
        assert (
            s["who"]
            and s["field"]
            and s["finding"]
            and s["http_status"] == 200
            and re.fullmatch(r"[0-9a-f]{64}", s["content_hash"])
        )
        assert str(s["retrieved_at"]) >= "2026-10-08", "fetched for this change, not carried over"
    rival = positions[held["rival"]]
    assert rival["rival"] == "access_by_state" and rival["attribution"] == "site" and not rival["holders"]
    claim = next(c for c in OUTLOOK["claims"] if c["position"] == "access_by_state")
    assert claim["falsifier"] and "test" not in claim, (
        "no public repeatable reading exists yet, so the claim says so by having no test"
    )
    assert outlook_problems(OUTLOOK) == []


def test_the_future_leaves_the_waiting_list_and_joins_the_dial():
    owners = {o["id"]: o for o in SPEC["ownership"]}
    split = owners["country_split"]
    assert set(split["argued_by"]) == set(
        next(p for p in OUTLOOK["positions"] if p["id"] == "access_by_state")["holders"]
    )
    assert split["bears_for"] and split["bears_against"], "its own claim, and the rival's"
    assert all("country" not in w["name"].lower() for w in SPEC["waiting"])
    doc = json.loads((ROOT / "web" / "data" / "chain_atlas.json").read_text())
    f = next(f for f in doc["futures"] if f["id"] == "owners/country_split")
    assert len(f["argued_by"]) >= 2 and f["bears_for"] and f["bears_against"]
    rows = {b["id"]: b for g in doc["groups"] for b in g["businesses"]}
    mark = next(m for m in rows["policy_aware_routing"]["marks"] if m["key"] == "owners-country_split")
    assert mark["effect"] == "stronger", "the business whose worth turns on this future is judged in it"
    assert "not yet sourced" not in SPEC["businesses"]["policy_aware_routing"]["take"]
