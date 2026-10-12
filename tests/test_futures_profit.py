"""The futures section's second judgement of profit (Part 54): for each idea, how large a prize it would be, who would
pay, and which seller would keep what is left, each in plain words with a reason. A model's judgement, kept apart from
the older rubric answers, which stay for the pages and tools that still read them."""

from pathlib import Path

from ai_tracker import futures as fu

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "web" / "src"
SPEC = fu.verdict_spec()
ROW = {
    "id": "x1",
    "prize": "large",
    "prize_why": "It changes what farming costs.",
    "payer": "businesses",
    "seller": "incumbents",
    "money_why": "Farms buy it and seed firms sell it.",
    "sure": "fairly",
}


def test_the_real_file_passes_and_check_reads_it():
    ids = {x["id"] for x in fu.ideas()}
    assert fu.verdict_problems(list(fu.verdicts().values()), SPEC, ids) == []
    assert "futures.verdict_problems(" in (ROOT / "src" / "ai_tracker" / "cli.py").read_text()
    made = SPEC["made_by"]
    assert made["model"] and made["method"] and made["reviewed_by"]


def test_a_broken_verdict_names_each_problem():
    bad = [
        {**ROW, "id": "nobody_home"},
        {**ROW, "prize": "huge"},
        {**ROW, "prize": "none"},
        {**ROW, "money_why": "About 40 firms sell it."},
        {**ROW, "prize_why": ""},
        ROW,
        ROW,
    ]
    errors = "\n".join(fu.verdict_problems(bad, SPEC, {"x1"}))
    for part in (
        "nobody_home is not an idea",
        "prize huge",
        "go together",
        "types a figure",
        "has no prize_why",
        "x1 is judged twice",
    ):
        assert part in errors, part


def test_a_card_carries_the_verdict_in_words_and_keeps_the_old_line():
    words = SPEC["words"]
    v = fu.verdict_card(ROW, SPEC)
    assert v == {
        "prize": "large",
        "prize_word": words["prize"]["large"],
        "payer_word": words["payer"]["businesses"],
        "seller_word": words["seller"]["incumbents"],
        "key": "large-incumbents",
        "prize_why": ROW["prize_why"],
        "money_why": ROW["money_why"],
        "sure": words["sure"]["fairly"],
    }
    nothing = fu.verdict_card({**ROW, "prize": "none", "payer": "nobody", "seller": "none"}, SPEC)
    assert nothing["payer_word"] == words["payer"]["nobody"] and nothing["key"] == "none-none"
    doc = fu.build()
    cards = [c for d in doc["categories"].values() for c in d["ideas"]]
    assert all("profit" in c and "verdict" in c for c in cards), (
        "the old line stays until a page stops reading it"
    )
    assert all(c["verdict"] for c in cards if c["id"] in fu.verdicts())


def test_a_category_gets_its_table_only_when_every_idea_in_it_is_judged():
    doc, judged = fu.build(), fu.verdicts()
    for cid, d in doc["categories"].items():
        whole = all(c["id"] in judged for c in d["ideas"])
        assert (d["matrix"] is not None) == whole, cid
        if whole:
            assert [p["id"] for p in d["matrix"]["prizes"]] == list(SPEC["words"]["prize"])
            assert sum(cell["n"] for row in d["matrix"]["rows"] for cell in row["cells"]) == d["n"]
            assert all(
                cell["key"] == f"{p['id']}-{row['id']}"
                for row in d["matrix"]["rows"]
                for cell, p in zip(row["cells"], d["matrix"]["prizes"])
            )


def test_the_page_draws_the_verdict_with_its_reasons_folded_and_labels_it():
    parts = (WEB / "components" / "FuturesParts.tsx").read_text()
    card = parts.split("export function IdeaCard")[1].split("\nexport ")[0]
    assert "x.verdict" in card and "<details" in card and "x.profit" in card, (
        "the new verdict where there is one, the old line where not"
    )
    assert "A model&apos;s judgement, not a reading" in card
    page = (WEB / "app" / "futures" / "category" / "[id]" / "page.tsx").read_text()
    assert "c.matrix" in page and "VerdictTable" in page
    assert '"use client"' not in parts, "the table filters with radios and CSS, no script"


def test_every_idea_of_a_known_kind_is_judged():
    judged = fu.verdicts()
    assert not [x["id"] for x in fu.ideas() if x["category"] != "cannot_judge" and x["id"] not in judged]


def test_each_cell_counts_the_cards_it_shows_and_the_table_tallies_nothing_else():
    for cid, d in fu.build()["categories"].items():
        if not d["matrix"]:
            continue
        assert "payers" not in d["matrix"], "a count that filters nothing is a bare tally of judgements"
        for row in d["matrix"]["rows"]:
            for cell in row["cells"]:
                assert cell["n"] == sum(1 for c in d["ideas"] if c["verdict"]["key"] == cell["key"]), (cid, cell["key"])
                assert cell["key"].replace("-", "").isalpha(), "the key becomes a CSS id"


def test_the_headline_says_it_is_a_judgement_without_being_opened():
    parts = (WEB / "components" / "FuturesParts.tsx").read_text()
    card = parts.split("export function IdeaCard")[1].split("\nexport ")[0]
    assert "as a model judges it" in card.split("<details")[0], "decade pages show the card with no table above it"
    table = parts.split("export function VerdictTable")[1].split("\nexport ")[0]
    assert 'role="radiogroup"' in table and "data-v" in card and "fv-${c.key}" in table


def test_only_ask_reads_the_judgement_file_and_it_says_whose_judgement_it_is():
    src = Path(fu.__file__).parent
    for p in src.rglob("*.py"):
        if p.name in ("futures.py", "ask.py"):
            continue
        uses = [ln for ln in p.read_text().splitlines() if "verdicts(" in ln or "profit.jsonl" in ln or "PROFIT_ROWS" in ln]
        assert all("verdict_problems" in ln for ln in uses), f"{p.name} reads the futures profit judgement: {uses}"
    from ai_tracker import store as st
    from ai_tracker.query.ask import TOOLS, Tools

    judged = fu.verdicts()
    hits = Tools(st.Store()).futures("food made without farms", kind="idea", k=5)
    assert hits and all({"rent", "profit_tier", "profit_pools_with"}.isdisjoint(h) for h in hits), "the older rubric is gone"
    for h in hits:
        r = judged[h["cite"].removeprefix("fut:")]
        assert h["profit"] == {
            "judged_by": "a model, not a reading", "prize": SPEC["words"]["prize"][r["prize"]],
            "who_pays": SPEC["words"]["payer"][r["payer"]], "seller": SPEC["words"]["seller"][r["seller"]],
            "prize_why": r["prize_why"], "money_why": r["money_why"], "sure": SPEC["words"]["sure"][r["sure"]],
        }
    about = next(t["description"] for t in TOOLS if t["name"] == "futures")
    assert "a model's judgement" in about and "rent kind" not in about


def test_the_index_tallies_the_new_prizes_not_the_older_tiers():
    doc = fu.build()
    assert "tier_words" not in doc["index"]
    for c in doc["index"]["categories"]:
        assert "tiers" not in c and "tiers" not in doc["categories"][c["id"]]
        assert [p["word"] for p in c["prizes"]] == ["vast", "large", "small", "no prize"]
        assert sum(p["n"] for p in c["prizes"]) == c["n"]
    page = (WEB / "app" / "futures" / "page.tsx").read_text()
    assert "c.prizes" in page and "tier_words" not in page and "as a model judges it" in page
    assert "monopoly-like" not in page, "the lede explains the judgement the tally shows"
    method = (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert "how large a prize" in method and "no prize" in method, "the method page says how the new judgement is made"



# A pinned list, not the rule itself: ideas a person read and placed under "done to someone without their say, to hurt
# them, break their mind or override their will or body" (plan Part 56), and near neighbours the rule leaves priced.
NO_PRIZE = ("tv-17773bf73d tv-090afb57c0 tv-f41c183010 tv-74a4ab4a94 tv-bb47e48592 tv-acdea59b5e tv-e7893c2990 tv-e223ea183a "
            "tv-3252d4f1e8 tv-50cb9cdc7a tv-e991cd2a4c tv-2bc1683f5c tv-f82bcd62e5 tv-30f0c2bd3a tv-6b7b54f30f tv-869248d145 "
            "tv-25daafbdf5 tv-ba7c1a1581 tv-969494bade tv-1d848f92b4 tv-28aaba424e tv-e5a30c862b tv-bec58bb3cc tv-7bf8c18a7d "
            "tv-93908538db tv-454323bb79").split()
STILL_PRICED = "tv-ab168e842f tv-201b5e5ac0 tv-ab7e27ff5a tv-7cd5ed5528 tv-2ade83aa31 tv-5365ae0802 tv-8d18cca47b tv-55645c5db3".split()


def test_the_pinned_ideas_done_to_a_person_without_their_say_have_no_prize_and_their_neighbours_keep_one():
    judged = fu.verdicts()
    assert [i for i in NO_PRIZE if judged[i]["prize"] != "none"] == []
    assert [i for i in STILL_PRICED if judged[i]["prize"] == "none"] == []
    method = (WEB / "app" / "methodology" / "page.tsx").read_text()
    assert "without their say" in method and "left standing" not in method
