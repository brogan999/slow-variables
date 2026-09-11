from ai_tracker.store import Seed


def test_bottlenecks_and_compare_reference_real_things():
    s = Seed.load()
    inds = {i.id for i in s.indicators}
    preds = {p.id for p in s.predictions}
    assert [b.id for b in s.bottlenecks] == list(range(1, 90))
    codes = {e.code for e in s.essays}
    assert all(c in codes for b in s.bottlenecks for c in b.source_codes)
    assert all(i in inds for b in s.bottlenecks for i in b.related_indicators)
    assert {b.bucket_id for b in s.bottlenecks} <= {b.id for b in s.buckets}
    assert s.compare and all(r.indicator in inds for r in s.compare)
    assert all(p in preds for r in s.compare for p in r.nk_predictions + r.ai2027_predictions)


def test_skipped_sources_are_unique_and_the_paid_tier_is_listed():
    from ai_tracker.ingest.connectors.paid import PAID
    from ai_tracker.store import Seed

    seed = Seed.load()
    skipped = [s.id for s in seed.skipped]
    sources = {s.id for s in seed.sources}
    assert len(skipped) == len(set(skipped)) and not set(skipped) & sources
    assert {c.source_id for c in PAID} <= set(
        skipped
    ) | sources  # the paid tier shows on /sources, never silently


def test_no_tracked_file_carries_private_chat_links_or_the_delisted_firm():
    import subprocess

    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    hits = []
    for f in files:
        if f.startswith(("web/public/", "data/observations/")) or f.endswith(
            (".png", ".ttf", ".ico", ".woff2")
        ):
            continue
        try:
            text = open(f, encoding="utf-8").read()
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        chat, firm, garble = (
            "claude.ai" + "/chat",
            "Better" + "Brain",
            "a private " + "value-chain map",
        )  # split: no self-match
        if chat in text or firm in text or garble in text:
            hits.append(f)
    assert not hits, hits


def test_entity_ids_and_aliases_are_unique_and_memberships_point_at_real_sublayers():
    import re

    from ai_tracker import store as st

    seed = st.Seed.load()
    ids = [e.id for e in seed.entities]
    assert len(ids) == len(set(ids)), "duplicate entity id"
    owner: dict[str, str] = {}
    for e in seed.entities:
        for n in {e.id, e.name, *e.aliases}:
            k = re.sub(r"[^a-z0-9]", "", n.lower())  # "Arcee AI" and "arcee_ai" are one name
            assert owner.setdefault(k, e.id) == e.id, f"{n!r} names both {owner[k]} and {e.id}"
    subs = {(x.layer_id, x.id) for x in seed.sublayers}
    for e in seed.entities:
        for m in e.memberships:
            assert m.sublayer_id is None or (m.layer_id, m.sublayer_id) in subs, (e.id, m)


def test_prediction_assessments_are_digit_free_and_compare_groups_claims_by_ledger():
    import re

    from ai_tracker import store as st

    s = st.Store()
    for p in s.seed.predictions:
        for f in ("direction_assessment", "magnitude_assessment", "timing_assessment"):
            assert not re.search(r"\d", getattr(p, f) or ""), (p.id, f)  # a figure belongs to a cited record, not prose
    rows = {r["indicator"]: r for r in s._compare({i.id: s._card(i) for i in s.seed.indicators})["rows"]}
    dev = rows["dev_rct_uplift"]["columns"]
    assert [x["id"] for x in dev["lab"]["predictions"]] == ["amodei_swe_end_to_end_6_12mo"] and not dev["ai2027"]["predictions"]
    assert rows["margin_stack_semis_share"]["leans"] is None  # a capture row takes no worldview lean


def test_every_bottleneck_has_a_domain_and_sits_in_the_grid_once():
    from ai_tracker import store as st

    s = st.Store()
    doc = s._bottlenecks({i.id: s._card(i) for i in s.seed.indicators})
    assert all(b.domain and b.domain_basis for b in s.seed.bottlenecks)
    ids = sorted(n for row in doc["grid"] for cell in row["cells"].values() for n in cell)
    assert ids == list(range(1, 90)) and sum(r["items"] for r in doc["summary"]) == 89
