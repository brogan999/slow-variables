"""The owner reviewed the needs grid on 10 Oct 2026 and made two changes: the firm's own map of its data meets the
need to write down how a firm works, and the roll-up's own customers are marked with the need it meets."""

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seed" / "firm_kinds.yaml"
SPEC = yaml.safe_load(SEED.read_text())


def test_the_new_business_meets_a_need_and_the_roll_ups_customers_have_its_need():
    needs = {n["id"]: n for n in SPEC["needs"]}
    assert needs["capture"]["opportunities"] == ["context_engineering_service", "firm_own_record"]
    kinds = {k["id"]: k for k in SPEC["kinds"]}
    assert "outcome" in kinds["accounting"]["needs"] and "outcome" in kinds["property"]["needs"]
    demand = json.loads((ROOT / "web" / "data" / "opportunities.json").read_text())["figures"]["demand"]
    assert "firm_own_record" in json.dumps(demand["rows"]) and "firm_own_record" not in json.dumps(
        demand["off"]
    )


def test_the_page_says_the_owner_reviewed_the_grid_and_claims_no_wider_review():
    foot = (ROOT / "web" / "src" / "components" / "OpportunityFigures.tsx").read_text()
    assert "the owner has not yet reviewed them" not in foot
    assert "the owner reviewed them in October 2026, after his review of the records below" in foot
    assert "reviewed by Alex Brogan on 10 Oct 2026" in SEED.read_text()
    kinds_page = (ROOT / "web" / "src" / "app" / "firm" / "kinds" / "page.tsx").read_text()
    assert "Reviewed by Alex" not in kinds_page, "he reviewed the needs grid, not that page's judgements"
