from ai_tracker import futures as fu


def test_dates_normalise_by_fixed_rules_and_never_to_a_midpoint():
    assert fu.when("1998.0") == {"kind": "year", "year": 1998, "decade": 1990}
    assert fu.when("1960s") == {"kind": "decade", "year": None, "decade": 1960}
    for vague in ("20th century", "Antiquity", "-", "N/A", None, "In development"):
        assert fu.when(vague)["kind"] == "unclear"


def test_arrival_keeps_things_that_came_first_out_of_the_lags():
    assert fu.arrival(1726, "Yes", "1998") == {
        "state": "marked_built",
        "kind": "year",
        "year": 1998,
        "decade": 1990,
        "lag_years": 272,
    }
    assert (
        fu.arrival(1985, "Yes", "1947")["state"] == "already_existed"
    )  # the microwave oven before the story
    assert fu.arrival(1911, "Yes", "2000s")["lag_decades"] == 9
    assert fu.arrival(1950, "Yes", "20th century")["state"] == "marked_built_date_unclear"
    assert fu.arrival(1950, "No", None)["state"] == "not_marked_built"


def test_teece_decides_where_the_rent_pools():
    base = {"rent_kind": "scarcity", "durability": "medium"}
    assert (
        fu.pools(
            {
                **base,
                "appropriability": "tight",
                "complementary_assets": "generic",
                "asset_owner": "incumbents",
            }
        )
        == "innovator"
    )
    assert (
        fu.pools(
            {
                **base,
                "appropriability": "weak",
                "complementary_assets": "specialised",
                "asset_owner": "incumbents",
            }
        )
        == "incumbents"
    )  # EMI and GE
    assert (
        fu.pools(
            {
                **base,
                "appropriability": "weak",
                "complementary_assets": "specialised",
                "asset_owner": "innovator",
            }
        )
        == "innovator"
    )
    assert (
        fu.pools(
            {**base, "appropriability": "weak", "complementary_assets": "generic", "asset_owner": "platforms"}
        )
        == "users"
    )


def test_the_tier_follows_rent_kind_and_durability_and_is_none_when_competed_away():
    tight = {"appropriability": "tight", "complementary_assets": "generic", "asset_owner": "innovator"}
    assert fu.tier({**tight, "rent_kind": "scale_network", "durability": "long"}) == "monopoly_like"
    assert fu.tier({**tight, "rent_kind": "scarcity", "durability": "medium"}) == "moderate"
    assert fu.tier({**tight, "rent_kind": "none", "durability": "long"}) == "none"
    weak = {"appropriability": "weak", "complementary_assets": "generic", "asset_owner": "innovator"}
    assert fu.tier({**weak, "rent_kind": "regulatory", "durability": "long"}) == "none"


def test_the_rubric_is_total():
    assert fu.problems(fu.rubric()) == []


def _idea(**kw):
    base = {
        "id": "tv-x",
        "line": "A flying car.",
        "category": "transport",
        "rent_kind": "scarcity",
        "appropriability": "tight",
        "complementary_assets": "generic",
        "asset_owner": "innovator",
        "durability": "medium",
        "arrival_decade": "2030s",
        "needs": "cost_decline",
    }
    base |= {"technology": "yes"} | kw
    base["votes"] = {k: [base[k]] * 3 for k in fu.VOTED}
    base["pools"], base["tier"] = fu.judged(base, fu.rubric())
    return base


def test_the_seed_checks_catch_a_tier_that_does_not_follow_the_rules():
    spec = fu.rubric()
    good = _idea()
    assert (good["pools"], good["tier"]) == ("innovator", "moderate")
    assert fu.idea_problems([good], spec) == []
    assert fu.idea_problems([{**good, "tier": "fat"}], spec)
    assert fu.idea_problems([{**good, "line": "A car from 2050."}], spec)
    assert fu.idea_problems([{**good, "rent_kind": "tight"}], spec)
    assert fu.idea_problems([{**good, "rent_kind": "no_majority"}], spec)  # one scorer: nothing to split
    moved = {**good, "arrival_decade": "2020s"}
    assert fu.idea_problems([moved], spec)
    assert fu.idea_problems([{**moved, "overrides": {"arrival_decade": "It is sold today."}}], spec) == []


def test_a_split_blocks_a_result_only_where_the_rule_needs_it():
    spec = fu.rubric()
    assert fu.judged(_idea(asset_owner="no_majority"), spec) == ("innovator", "moderate")
    assert fu.judged(_idea(appropriability="cannot_judge"), spec) == (None, None)
    assert fu.judged(
        _idea(appropriability="weak", complementary_assets="generic", rent_kind="no_majority"), spec
    ) == ("users", "none")
    assert fu.judged(_idea(durability="no_majority"), spec) == ("innovator", None)
    assert fu.judged(_idea(category="exotic_physics"), spec) == (None, None)
    assert fu.judged(_idea(arrival_decade="not_physically_possible"), spec) == (None, None)
    assert fu.judged(_idea(technology="no"), spec) == (None, None)


def test_a_split_takes_opus_vote_only_when_marked_and_no_market_means_no_rent():
    spec = fu.rubric()
    split = _idea(arrival_decade="2040s")
    split["votes"]["arrival_decade"] = ["2040s", "2030s", "2050s"]
    assert fu.idea_problems([split], spec)  # a split answered without saying so
    assert fu.idea_problems([{**split, "tiebreak": ["arrival_decade"]}], spec) == []
    assert fu.idea_problems([{**split, "arrival_decade": "2030s", "tiebreak": ["arrival_decade"]}], spec)
    for m in ("one_off", "banned", "cannot_judge"):
        assert fu.judged(_idea(market=m), spec) == (None, None)
    assert fu.judged(_idea(market="sold"), spec) == ("innovator", "moderate")


def _fc(**kw):
    base = {"id": "cf-x", "who": "A", "technology": "t", "line": "A expects brain uploads by 2045.", "category": "mind_neurotech",
            "when": {"kind": "by", "year": 2045, "low": None, "high": None}, "odds": None, "quote": None,
            "ai_milestone": False, "ledger_id": None, "works": ["w"]}
    return base | kw


def test_canon_forecasts_date_themselves_as_stated_and_follow_the_text_rules():
    spec, src = fu.rubric(), [{"id": "w", "title": "T", "author": "A", "year": 2001}]
    assert fu.forecast_problems([_fc()], src, spec, set()) == []
    assert fu.forecast_problems([_fc(line="A expects a 10x rise by 2045.")], src, spec, set())
    assert fu.forecast_problems([_fc(line="A expects GPT-4's successor by mid-2027.")], src, spec, set()) == []
    assert fu.forecast_problems([_fc(odds="10%")], src, spec, set())
    assert fu.forecast_problems([_fc(when={"kind": "midpoint", "year": 2040})], src, spec, set())
    assert fu.forecast_problems([_fc(works=["missing"])], src, spec, set())
    assert fu.forecast_problems([_fc(ledger_id="nope")], src, spec, set())
    assert fu.forecast_problems([_fc(ledger_id="known")], src, spec, {"known"}) == []


def test_the_canon_seed_passes_its_checks():
    import yaml

    ledger = {p["id"] for p in yaml.safe_load(open(fu.ROOT / "seed" / "predictions.yaml"))["predictions"]}
    assert fu.forecast_problems(fu.forecasts(), fu.canon_sources(), fu.rubric(), ledger) == []


def test_the_futures_export_counts_every_idea_once_and_withholds_failed_images():
    import yaml

    b = fu.build()
    i = b["index"]
    assert sum(d["n"] for d in i["imagined"]) == len(fu.ideas())
    assert sum(c["n"] for c in i["categories"]) + sum(x["category"] not in fu.CATEGORY_NAMES for x in fu.ideas()) == len(fu.ideas())
    on_pages = {x["id"] for k, d in b["decades"].items() if k.startswith("imagined/") for g in d["groups"] for x in g["ideas"]}
    assert on_pages == {x["id"] for x in fu.ideas()}
    assert sum(d["stated"] for d in i["expected"]) == len(fu.forecasts())
    withheld = {x["idea"] for x in yaml.safe_load(fu.IMAGES.read_text())["images"] if x.get("withheld") and x.get("idea")}
    shown = {x["id"] for d in b["decades"].values() for g in d["groups"] for x in g["ideas"] if x["image"]}
    assert withheld and not withheld & shown
    assert all(0 <= d["width"] <= 100 for d in i["imagined"]) and max(d["width"] for d in i["imagined"]) == 100
    assert len(i["credits"]) == 2 and all(c["url"].startswith("https://") for c in i["credits"])


def test_futures_is_in_the_nav_and_the_sitemap():
    web = fu.ROOT / "web" / "src"
    assert '"/futures"' in (web / "lib" / "nav.ts").read_text()
    assert "futures()" in (web / "app" / "sitemap.ts").read_text()
