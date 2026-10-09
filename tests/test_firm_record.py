"""The twenty-first business: the firm's own record of itself, kept on its own servers. It is a record on the
businesses page, a call on the atlas, and the company that names the idea is placed on the map from its own site."""

import json
from pathlib import Path

from ai_tracker import chain_atlas as ca
from ai_tracker import opportunities

ROOT = Path(__file__).resolve().parents[1]
ID = "firm_own_record"


def test_the_record_is_published_last_and_sits_on_a_firms_own_knowledge():
    recs = [o for o in opportunities.load()["opportunities"] if o.get("published")]
    r = recs[-1]
    assert r["id"] == ID and r["primary"] == "context_and_memory", (
        "the owner's order is kept: a new record goes last"
    )
    assert all(
        r.get(k)
        for k in (
            "customer",
            "bottleneck",
            "wedge",
            "why_not_bundled",
            "durable_asset",
            "falsifier",
            "prerequisites",
            "acquirers",
            "next_action",
        )
    )
    doc = json.loads((ROOT / "web" / "data" / "opportunities.json").read_text())
    mark = next(m for m in doc["figures"]["marks"] if m["id"] == ID)
    assert mark["n"] == len(recs) and mark["verdict"]


def test_the_atlas_takes_a_position_on_it_in_the_futures_that_bear_on_it():
    b = ca.load()["businesses"][ID]
    assert b["call"] in ("build", "cond", "no") and b["take"] and b["kills"]
    assert {f.split("/")[0] for f in b["futures"]} >= {"owners"}, (
        "who owns the models bears on a record kept at home"
    )
    assert ID in ca.load()["builds"] and "record" in ca.load()["builds"][ID]
    doc = json.loads((ROOT / "web" / "data" / "chain_atlas.json").read_text())
    row = next(b for g in doc["groups"] for b in g["businesses"] if b["id"] == ID)
    assert row["n"] == 21 and row["primary"]["name"] == "Context and memory"


def test_the_company_that_names_the_idea_is_on_the_map_from_its_own_site():
    mm = json.loads((ROOT / "web" / "data" / "market_map.json").read_text())
    cat = next(c for layer in mm["layers"] for c in layer["categories"] if c["id"] == "context_and_memory")
    e = next(e for e in cat["entities"] if e["id"] == "textql")
    assert e["source"] == "hand" and "its own site" in e["label"] and e["verified"] is False
    doc = json.loads((ROOT / "web" / "data" / "opportunities.json").read_text())
    rec = next(o for o in doc["opportunities"] if o["id"] == ID)
    assert rec["primary"]["n_entities"] == cat["n_entities"]
