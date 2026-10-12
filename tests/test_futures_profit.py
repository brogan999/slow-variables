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


def test_nothing_else_reads_the_judgement_file():
    src = Path(fu.__file__).parent
    for p in src.rglob("*.py"):
        text = p.read_text()
        if p.name == "futures.py":
            continue
        uses = [ln for ln in text.splitlines() if "verdicts(" in ln or "profit.jsonl" in ln or "PROFIT_ROWS" in ln]
        assert all("verdict_problems" in ln for ln in uses), f"{p.name} reads the futures profit judgement: {uses}"
