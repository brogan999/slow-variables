"""The illustrations made for /firm/kinds and the coming /story page: each served file is recorded in
seed/illustrations.yaml with its hash, its prompt and an alt text, and is shown with the one credit. They are pictures
made with AI image generation, never evidence."""

import hashlib
import json
import re
import shutil

from ai_tracker import census, firm_kinds, illustrations

from .test_outlook import NUMBER_WORD

WEB = illustrations.ROOT / "web"
PART = WEB / "src" / "components" / "diagrams" / "illustration.tsx"
CREDIT = "Illustration made with AI image generation; not evidence"
SMALL = re.compile(r"\b(one|two|three|both|pair|couple|several|dozen)\b", re.I)  # counts NUMBER_WORD lets through
REAL = re.compile(r"\b(photo|photograph|real|actual|shows how|evidence)\b", re.I)


def _records():
    return illustrations.load()


def test_the_record_and_the_files_agree():
    rows = _records()
    assert illustrations.problems(rows) == []
    assert len(rows) == len({r["stem"] for r in rows}) == 16
    for r in rows:
        data = (illustrations.DIR / f"{r['stem']}.webp").read_bytes()
        assert hashlib.sha256(data).hexdigest() == r["sha256"], r["stem"]
        assert illustrations.webp_size(data) == (illustrations.WIDTH, illustrations.HEIGHT) == (720, 480), r["stem"]
        assert r["prompt"].strip() and r["model"].startswith("fal-ai/qwen-image") and r["placement"].strip()


def test_no_file_is_served_without_a_record():
    assert {p.stem for p in illustrations.DIR.glob("*")} == {r["stem"] for r in _records()}
    assert all(p.suffix == ".webp" for p in illustrations.DIR.glob("*"))  # the PNG masters are not committed


def test_the_check_names_a_changed_file_a_missing_one_an_orphan_and_a_record_without_words(tmp_path):
    rows = _records()
    for r in rows[:3]:
        shutil.copy(illustrations.DIR / f"{r['stem']}.webp", tmp_path)
    assert illustrations.problems(rows[:3], tmp_path) == []
    (tmp_path / f"{rows[0]['stem']}.webp").write_bytes(b"RIFF....WEBPnot the picture")
    (tmp_path / f"{rows[1]['stem']}.webp").unlink()
    (tmp_path / "stray.webp").write_bytes(b"x")
    found = "\n".join(illustrations.problems([rows[0], rows[1], {**rows[2], "alt": " ", "prompt": ""}], tmp_path))
    assert f"{rows[0]['stem']}.webp differs from its recorded sha256" in found
    assert f"{rows[1]['stem']}.webp is missing" in found
    assert "stray.webp has no record" in found
    assert f"{rows[2]['stem']} has no alt text" in found and f"{rows[2]['stem']} has no prompt" in found
    small = (illustrations.DIR / f"{rows[2]['stem']}.webp").read_bytes()
    assert illustrations.webp_size(small[:26] + b"\x40\x01\xf0\x00" + small[30:]) == (320, 240)


def test_a_record_is_placed_on_a_page_or_waits_for_one_and_a_stage_is_next_or_later():
    for r in _records():
        assert bool(r.get("page")) != bool(r.get("waits_for")), r["stem"]
        assert r.get("stage") in (None, "next", "later"), r["stem"]
        if r["placement"].endswith((", next", ", later", ": next")):
            assert r["stage"] == r["placement"].rsplit(" ", 1)[1], r["stem"]


def test_every_kind_of_firm_names_its_own_illustration_and_every_firm_picture_is_used_once():
    spec = firm_kinds.load()
    placed = firm_kinds.placed(spec)
    firm = sorted(r["stem"] for r in _records() if r.get("page") == "/firm/kinds")
    assert sorted(placed) == firm and len(firm) == len(spec["kinds"]) + 1
    assert spec["anatomy"]["illustration"] == "firm-anatomy"
    by = {k["id"]: k["illustration"] for k in spec["kinds"]}
    assert by["customer_support"] == "firm-support"
    assert all(v == f"firm-{k}" for k, v in by.items() if k != "customer_support")
    assert illustrations.placement_problems(_records(), {"/firm/kinds": placed}) == []
    wrong = illustrations.placement_problems(_records(), {"/firm/kinds": [*placed[1:], placed[1], "firm-nowhere", "story-act-1"]})
    assert any("firm-nowhere" in e for e in wrong) and any(f"{placed[1]} is placed more than once" in e for e in wrong)
    assert any(f"{placed[0]} is recorded for /firm/kinds but not placed" in e for e in wrong)
    assert any("story-act-1" in e and "waits" in e for e in wrong)


def test_the_export_hands_each_panel_a_ready_file_its_alt_and_its_stage():
    rec = {r["stem"]: r for r in _records()}
    spec = firm_kinds.load()
    doc = firm_kinds.build(spec, census.load(), firm_kinds.trades())
    pairs = [(spec["anatomy"]["illustration"], doc["anatomy"]["illustration"])]
    pairs += [(s["illustration"], k["illustration"]) for s, k in zip(spec["kinds"], doc["kinds"])]
    for stem, got in pairs:
        assert got == {"file": f"/illustrations/{stem}.webp", "alt": rec[stem]["alt"], "stage": rec[stem].get("stage")}
    assert doc["anatomy"]["illustration"]["stage"] is None and all(k["illustration"]["stage"] for k in doc["kinds"])


def test_the_story_pictures_are_recorded_and_rendered_nowhere():
    story = [r for r in _records() if r["stem"].startswith("story-act-")]
    assert len(story) == 3 and all(r["waits_for"] == "/story" and not r.get("page") for r in story)
    for p in [*(WEB / "src").rglob("*.ts*"), *(illustrations.ROOT / "seed").glob("*.yaml")]:
        if p != illustrations.SEED:
            assert "story-act" not in p.read_text(), p
    doc = firm_kinds.build(firm_kinds.load(), census.load(), firm_kinds.trades())
    assert "story-act" not in json.dumps(doc)


def test_the_flagged_pictures_carry_the_deliverys_note_and_are_used():
    rec = {r["stem"]: r for r in _records()}
    assert {s for s, r in rec.items() if r.get("note")} == {"firm-freight", "firm-retailer"}
    assert all("markings" in rec[s]["note"] and rec[s]["page"] == "/firm/kinds" for s in ("firm-freight", "firm-retailer"))
    assert "markings" in illustrations.SEED.read_text().split("\n- stem")[0]  # the decision is in the seed's comment


def test_alt_texts_are_one_plain_sentence_with_no_figure_and_no_claim_to_be_real():
    for r in _records():
        alt = r["alt"]
        assert alt.endswith(".") and alt.count(". ") == 0 and 40 < len(alt) < 260, alt
        assert not re.search(r"\d", alt) and not NUMBER_WORD.search(alt) and not SMALL.search(alt), alt
        assert not REAL.search(alt), alt
    assert len({r["alt"] for r in _records()}) == 16


def test_one_component_renders_every_illustration_with_exactly_the_credit():
    src = PART.read_text()
    assert src.count(f'"{CREDIT}"') == 1 and "{CREDIT}" in src
    assert 'loading={eager ? "eager" : "lazy"}' in src and "width={720}" in src and "height={480}" in src and "alt={alt}" in src
    assert "this site&apos;s judgement" in src and "not anything observed" in src and "stage ?" in src
    for f in (WEB / "src").rglob("*.tsx"):  # nothing else draws these files, so nothing shows one without its credit
        if f != PART:
            assert "/illustrations/" not in f.read_text(), f
    kinds = (WEB / "src" / "components" / "FirmKinds.tsx").read_text()
    assert kinds.count("<Illustration ") == 2 and "k.illustration" in kinds and "a.illustration" in kinds
    assert kinds.count("eager") == 1  # only the opening picture loads at once


def test_the_served_files_are_cached_as_the_futures_ones_are():
    cfg = (WEB / "next.config.ts").read_text()
    line = next(x for x in cfg.splitlines() if '"/futures/:path*.webp"' in x)
    assert line.replace("/futures/", "/illustrations/") in cfg
