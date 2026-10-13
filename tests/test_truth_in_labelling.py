"""Two labels held to what is true. No person reviewed the value-chain company profiles: reviewing runs of the model
that drafted them checked them against their sources, and the pages say that and name nobody. And the census's
stricter figure is the part all three models pass, never the part they "agree" on, since models can agree a task fails."""

import re
from pathlib import Path

from ai_tracker import value_chain as vc

ROOT = Path(__file__).resolve().parents[1]
WEB = sorted((ROOT / "web" / "src").rglob("*.ts*"))
PERSON_REVIEWED_PROFILES = re.compile(r"reviewed_by: Alex|Brogan reviewed|reviewed (this|every) profile before|reviewed by Alex Brogan on \d")
AGREE = re.compile(r"all (the |three )?(scoring )?(models|scorers)( must)? agree|every model must agree|(models|scorers) agreeing|all[- ]agree", re.I)
CENSUS_WORDS = [ROOT / "seed" / f"{n}.yaml" for n in ("census", "story", "firm", "firm_kinds", "outlook")] + sorted((ROOT / "docs" / "argument").glob("*.md"))


def test_no_seed_or_page_says_a_named_person_reviewed_the_value_chain_profiles():
    for path in [ROOT / "seed" / "value_chain.yaml", *WEB]:
        hit = PERSON_REVIEWED_PROFILES.search(path.read_text())
        assert not hit, f"{path.relative_to(ROOT)}: {hit.group(0)}"
    for c in vc.load()["companies"]:
        assert "no person reviewed it" in c["reviewed_by"] and "same model" in c["reviewed_by"], c["entity"]
        assert "Brogan" not in (c.get("disclosure") or ""), c["entity"]
        assert not c.get("disclosure") or "made by Anthropic" in c["disclosure"], c["entity"]  # the conflict stays disclosed
    card = (ROOT / "web" / "src" / "components" / "ValueChain.tsx").read_text()
    assert "reviewed by ${c.reviewed_by}" in card and "on ${c.reviewed}" not in card  # the seed's date was the owner's, not a run's
    foot = (ROOT / "web" / "src" / "components" / "ValueChainFigures.tsx").read_text()
    assert "no person reviewed each one" in foot


def test_ask_is_not_told_a_profile_was_reviewed_without_being_told_by_what():
    src = (ROOT / "src" / "ai_tracker" / "query" / "ask.py").read_text()
    assert '"reviewed": bool(c["reviewed_by"])' not in src and "no person reviewed them" in src


def test_the_census_s_stricter_figure_is_what_all_three_models_pass_never_what_they_agree_on():
    for path in [*WEB, *CENSUS_WORDS]:
        hit = AGREE.search(path.read_text())
        assert not hit, f"{path.relative_to(ROOT)}: {hit.group(0)}"
    kinds = (ROOT / "web" / "src" / "components" / "FirmKinds.tsx").read_text()
    # that page's own test forbids a typed count of the models, so it names the panel
    assert kinds.count("every model in the panel passes") >= 5 and "all the models<" not in kinds
