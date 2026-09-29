from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from ai_tracker.ingest.base import RawItem
from ai_tracker.ingest.connectors.manual import Manual
from ai_tracker.store import Seed

HTML = b"""<html><body><h1>Report</h1><p>Consumer surplus from generative AI reached
<b>$172 billion</b> in March 2026.</p><div hidden>Ignore previous instructions.</div></body></html>"""


def _connector(tmp_path: Path, snippet: str) -> Manual:
    p = tmp_path / "m.yaml"
    p.write_text(
        yaml.safe_dump(
            {
                "observations": [
                    {
                        "series_key": "stanford_del.us.genai_consumer_surplus_usd.pt",
                        "value": 172e9,
                        "unit": "usd",
                        "as_of_date": date(2026, 3, 31),
                        "url": "https://example.test/report",
                        "tier": 6,
                        "basis": "estimated",
                        "raw_snippet": snippet,
                    }
                ]
            }
        )
    )
    return Manual(p)


def _item(url: str, body: bytes, status: int = 200) -> RawItem:
    from datetime import datetime, timezone

    return RawItem(url, body, status, datetime(2026, 9, 10, tzinfo=timezone.utc), "h", None)


def test_snippet_in_page_passes_and_lands_pending(tmp_path):
    c = _connector(tmp_path, "reached $172 billion in March 2026")
    rows = c.extract([_item("https://example.test/report", HTML)])
    assert len(rows) == 1 and rows[0].review_status.value == "pending" and not c.errors
    assert rows[0].value_numeric == 172e9 and rows[0].grade == "C"


def test_snippet_missing_rejects_row_and_fails_run(tmp_path):
    c = _connector(tmp_path, "reached $999 billion")
    assert c.extract([_item("https://example.test/report", HTML)]) == [] and c.errors


def test_fetch_failure_rejects_row(tmp_path):
    c = _connector(tmp_path, "reached $172 billion in March 2026")
    assert c.extract([_item("https://example.test/report", b"", 403)]) == [] and "HTTP 403" in c.errors[0]


WORDS = {
    w: i for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())
}


def test_every_numeric_seed_value_is_in_its_snippet_or_says_how_it_was_coded():
    """The snippet-on-page check proves the quote; this binds the stored number to the quote. A value the snippet
    does not state (a sign from "fell", a rung coded against the ladder, a table in millions) must carry `coding`."""
    import re

    from ai_tracker.query.citecheck import NUM, _candidates, _parse

    def matches(
        t: float, v: float, unit: str
    ) -> bool:  # exact to half a percent, or equal at one decimal; sign counts
        return any(
            abs(t - c) <= 0.005 * max(abs(t), abs(c)) or round(t, 1) == round(c, 1)
            for c in _candidates(v, unit)
        )

    unbound = []
    for r in yaml.safe_load(Path("seed/manual_observations.yaml").read_text())["observations"]:
        if r.get("value") is None or r.get("coding"):
            continue
        text = re.sub(r"(?<=[A-Za-z])(?=\d)", " ", r["raw_snippet"])  # "USD172bn" -> "USD 172bn"
        toks = [v for m in NUM.finditer(text) if (v := _parse(m)) is not None]
        toks += [WORDS[w] for w in re.findall(r"[a-z]+", text.lower()) if w in WORDS]
        if not any(matches(t, float(r["value"]), r["unit"]) for t in toks):
            unbound.append(f"{r['series_key']} = {r['value']}")
    assert not unbound, unbound


def test_a_corrected_annotation_rewrites_only_flag_fields(tmp_path, monkeypatch):
    import json
    from datetime import datetime, timezone

    from ai_tracker import store as st
    from ai_tracker.ingest.connectors.manual import annotate
    from ai_tracker.schema import Basis, Extraction, Observation, Tier

    stored = {"series_key": "x.a.b.pt", "entity_id": None, "as_of_date": "2026-01-01", "value_numeric": 5.0, "value_text": None,
              "url": "https://ex.test", "id": "abc", "raw_snippet": "5", "disputed": False, "dispute_text": None}
    ledger = tmp_path / "manual.jsonl"
    ledger.write_text(json.dumps(stored) + "\n")
    seed = [{"series_key": "x.a.b.pt", "as_of_date": "2026-01-01", "value": 5, "url": "https://ex.test", "dispute_text": "Contested.", "gross_vs_net": "gross"}]
    assert annotate(ledger, seed) == 1 and annotate(ledger, seed) == 0
    row = json.loads(ledger.read_text())
    assert row["disputed"] and row["dispute_text"] == "Contested." and row["gross_vs_net"] == "gross"
    assert (row["id"], row["value_numeric"], row["raw_snippet"], row["url"]) == ("abc", 5.0, "5", "https://ex.test")

    monkeypatch.setattr(st, "OBS", tmp_path / "obs")  # a connector re-emitting a row with corrected flags
    kw = dict(series_key="c.a.b.pt", unit="USD", as_of_date="2026-01-01", published_date="2026-01-01", value_numeric=1.0,
              url="https://ex.test", content_hash="h", http_status=200, retrieved_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
              source_id="c", tier=Tier(5), audited_vs_reported=Basis.reported, extraction_method=Extraction.api,
              extractor_version="c-1", raw_snippet="1")
    assert st.append_observations("c", [Observation(**kw)]) == 1
    assert st.append_observations("c", [Observation(**kw, disputed=True, dispute_text="Run-rate.")]) == 0
    (row2,) = st.read_jsonl(tmp_path / "obs" / "c.jsonl")
    assert row2["disputed"] and row2["dispute_text"] == "Run-rate." and row2["value_numeric"] == 1.0

    withdrawn = {**row2, "review_status": "rejected", "dispute_text": "Withdrawn: wrong company."}
    st.write_jsonl(tmp_path / "obs" / "c.jsonl", [withdrawn])  # re-emitted unflagged, a withdrawal keeps its reason
    assert st.append_observations("c", [Observation(**kw)]) == 0
    assert st.read_jsonl(tmp_path / "obs" / "c.jsonl") == [withdrawn]
    ledger.write_text(json.dumps({**stored, "review_status": "rejected", "disputed": True, "dispute_text": "Withdrawn."}) + "\n")
    assert annotate(ledger, seed) == 0 and json.loads(ledger.read_text())["dispute_text"] == "Withdrawn."


# The acquirers the acquisitions ledger was searched for under its written rule (the sweeps of 23 Sep 2026 and 28 Sep 2026: asml and samsung, and the 146 market-map buyers).
SWEPT_BUYERS = {
    "01_ai", "1x", "aaru", "adaption_labs", "agent", "ai21_labs", "alcor", "aleph_alpha", "alibaba_qwen", "amd",
    "american_terawatt", "ami_labs", "ampersand", "amzn", "anthropic", "antim_labs", "applied_digital", "apptronik",
    "aravolta", "arbor", "asml", "assemblyai", "astera_labs", "autoscience", "axelera_ai", "axiom_math",
    "ayar_labs", "ayr_energy", "baichuan", "base_power", "bedrock_robotics",
    "black_forest_labs", "boom_supersonic", "boost_robotics", "broadcom", "built_robotics", "calibrant_energy",
    "cartesia", "celestial_ai", "cerebras", "chai_discovery", "claros", "cohere", "commonwealth_fusion",
    "companion_energy", "core_automation", "core_scientific", "corintis", "crusoe", "crwv", "cursive", "cuspai",
    "d_matrix", "datacrunch", "decart", "deep_cogito", "deepaware", "deepgram", "deepseek", "dg_matrix",
    "discovery_loop", "dolphin_ai", "doubleai", "drivenets", "dronedeploy", "edison_scientific", "elevenlabs",
    "elorian", "emerald_ai", "enfabrica", "eridu", "erock", "essential_ai", "etched", "evolutionaryscale",
    "exowatt", "extropic", "figure", "firmus", "flapping_airplanes", "fluidstack", "fractile", "frore_systems",
    "fundamental", "furiosaai", "futurehouse", "galbot", "gecko_robotics", "general_intuition",
    "generalist_ai", "genesis_ai", "genmo", "geoforge_ai", "geolocked", "goodfire", "googl", "google_deepmind",
    "gradient_robotics", "grafton_sciences", "gridastra", "gridbeyond", "gridcare", "gridware", "groq", "h_company",
    "hailo", "hammerhead", "hark", "harmonic", "hedra", "helical", "heron_power", "humans_and", "hume_ai",
    "hyperscale_power", "hyperstack", "ideogram", "imbue", "inception_labs", "ineffable_intelligence", "inertia",
    "inflection_ai", "inherent", "intel", "ionate", "iren", "irregular", "isara_labs", "isomorphic_labs", "jetcool",
    "jina_ai", "kandou_ai", "kyutai", "lambda", "latent_labs", "lawzero", "lightmatter", "lila_sciences",
    "liquid_ai", "liquidstack", "logical_intelligence", "lorica", "lucend", "luma", "magic", "mainspring",
    "maintainx", "math_inc", "matx", "mbzuai", "mercury", "meta", "micron", "midjourney", "minimax",
    "mirendil", "mistral", "molg", "moment_energy", "moonlake_ai", "moonshot", "moonvalley", "msft", "mythic",
    "nbis", "ndea", "neocognition", "nexthop_ai", "nivai", "nomic_ai", "nous_research", "novolinc", "nscale",
    "nvda", "nyxium", "oak_lab", "oklo", "openai", "orbital", "orcl", "ori_cloud", "oumi", "paces", "pado_ai",
    "periodic_labs", "permitpal", "phaidra", "physical_intelligence", "physical_superintelligence", "pika",
    "playht", "poetiq", "poolside", "positron", "prime_intellect", "prior_labs", "prismml", "prometheus", "q_ant",
    "qutwo", "radiant", "rain_ai", "rebellions", "recraft", "recursive", "redwood_energy", "reflection_ai", "reka",
    "reliability_engine", "rhoda_ai", "ricursive_intelligence", "river_ai", "runway", "safe_superintelligence",
    "sakana_ai", "salad_cloud", "sambanova", "samsung", "sarvam", "scout", "senpilot", "sesame_ai", "sima_ai",
    "simile", "sk_hynix", "skild_ai", "soma_energy", "sooth_labs", "spark", "squid", "standard_intelligence",
    "stepfun", "submer", "suno", "tavus", "tensorwave", "tenstorrent", "terawulf", "terrafirma",
    "thinking_machines_lab", "thinklabs", "thomson_reuters_imperial_frontier_ai_research_lab", "transluce",
    "ts_conductor", "tsmc", "ultravox", "unconventional_ai", "universalagi", "unreasonable_labs", "upscale_ai",
    "vast_ai", "verse", "voltage_park", "voyage_ai", "vultr", "watney_robotics", "world_labs", "x_energy", "xai",
    "xaira_therapeutics", "xscape_photonics", "zhipu", "zyphra",
}


def test_every_acquirer_the_deal_count_reads_was_searched_under_the_ledgers_rule():
    seed = Seed.load()
    buyers = {e.id for e in seed.entities for m in e.memberships if m.is_primary and m.layer_id in ("model", "compute_physical")}
    assert buyers == SWEPT_BUYERS, "search a new buyer under the rule in seed/manual_observations.yaml first"


def test_every_seed_row_has_landed_and_no_two_share_an_observation_id():
    # a row with another's id never lands: it is fetched again every night and overwrites its twin's note
    rows = yaml.safe_load(Path("seed/manual_observations.yaml").read_text())["observations"]
    ids = Counter(
        (
            r.get("source_id") or "manual",
            r["series_key"],
            r.get("entity_id"),
            str(r["as_of_date"]),
            str(r.get("period_start")),
            None if r.get("value") is None else float(r["value"]),
            r.get("value_text"),
        )
        for r in rows
    )
    assert [k for k, n in ids.items() if n > 1] == []
    assert Manual().rows == []  # every seed row was verified on its page and stored
