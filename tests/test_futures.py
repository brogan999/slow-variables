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
