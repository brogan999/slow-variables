"""OpenRouter list prices per model (public API, no key). The series records change-points, not daily snapshots.

Models METR has measured are keyed by METR's model id so the price joins the horizon series on `subject`
(semantic metric frontier_price_per_horizon_hour); everything else is keyed by its OpenRouter id.
"""

from __future__ import annotations

import json
from pathlib import Path

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem, expect, slug

URL = "https://openrouter.ai/api/v1/models"
VENDORS = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "googl",
    "x-ai": None,
    "meta-llama": None,
    "deepseek": None,
}
ALIASES = {  # METR model id -> OpenRouter id (verified against the live list on 2026-09-10)
    "gpt_5_4": "openai/gpt-5.4",
    "gpt_5_2": "openai/gpt-5.2",
    "gpt_5_3_codex": "openai/gpt-5.3-codex",
    "gpt_5_1_codex_max_inspect": "openai/gpt-5.1-codex-max",
    "gpt_5_2025_08_07_inspect": "openai/gpt-5",
    "o3_inspect": "openai/o3",
    "o1_inspect": "openai/o1",
    "gpt_4o_inspect": "openai/gpt-4o",
    "gpt_4_turbo_inspect": "openai/gpt-4-turbo",
    "gpt_4": "openai/gpt-4",
    "gpt_3_5_turbo_instruct": "openai/gpt-3.5-turbo-instruct",
    "claude_opus_4_6_inspect": "anthropic/claude-opus-4.6",
    "claude_opus_4_5_inspect": "anthropic/claude-opus-4.5",
    "claude_4_1_opus_inspect": "anthropic/claude-opus-4.1",
    "claude_4_opus_inspect": "anthropic/claude-opus-4",
    "gemini_3_1_pro": "google/gemini-3.1-pro-preview",
}
SUBJECT = {v: k for k, v in ALIASES.items()}


def _latest(ledger: Path) -> dict[str, tuple[str, float]]:
    """series_key -> (as_of_date, value) of the newest row already in the ledger."""
    out: dict[str, tuple[str, float]] = {}
    if ledger.exists():
        for line in ledger.read_text().splitlines():
            o = json.loads(line)
            if o["series_key"] not in out or o["as_of_date"] > out[o["series_key"]][0]:
                out[o["series_key"]] = (o["as_of_date"], o["value_numeric"])
    return out


class OpenRouter(Connector):
    source_id = "openrouter"
    urls = [URL]
    expect_series = ["openrouter.gpt_5_4.price_prompt_usd_per_mtok.pt"]

    def __init__(self, ledger: Path = Path("data/observations/openrouter.jsonl")) -> None:
        super().__init__()
        self.latest = _latest(ledger)

    def extract(self, items: list[RawItem]) -> list[Observation]:
        item = items[0]
        models = json.loads(item.body).get("data") or []
        expect(set(models[0]) if models else set(), {"id", "pricing"}, "openrouter models")
        today = item.retrieved_at.date()
        out: list[Observation] = []
        for m in models:
            vendor = m["id"].split("/")[0]
            if vendor not in VENDORS or ":" in m["id"]:
                continue
            subject = SUBJECT.get(m["id"]) or slug(m["id"])
            for side in ("prompt", "completion"):
                usd = float(m["pricing"].get(side) or 0) * 1e6
                if usd <= 0:
                    continue
                key = f"openrouter.{subject}.price_{side}_usd_per_mtok.pt"
                prev = self.latest.get(key)
                as_of = (
                    today if prev is None or abs(prev[1] - usd) > 1e-9 else prev[0]
                )  # unchanged -> same row, skipped
                out.append(
                    self.obs(
                        item,
                        series_key=key,
                        entity_id=VENDORS[vendor],
                        unit="USD",
                        as_of_date=as_of,
                        published_date=as_of,
                        value_numeric=usd,
                        tier=Tier.PRODUCT_BEHAVIOUR,
                        audited_vs_reported=Basis.reported,
                        extraction_method=Extraction.api,
                        raw_snippet=f"{m['id']} pricing.{side} {m['pricing'][side]}",
                    )
                )
        return out
