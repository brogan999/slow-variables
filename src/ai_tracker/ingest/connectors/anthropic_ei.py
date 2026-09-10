"""Anthropic Economic Index open dataset (Hugging Face): the augmentation/automation split of Claude.ai use.

Provider-published usage classification: tier 2, company_stated. Two file formats:
  raw weekly samples (Jan/Mar 2026 releases): facet=collaboration, variable=collaboration_pct, one row per mode
  monthly aggregates (Jun 2026+): metric_id=collaboration_*_pct at category_name=overall
Buckets follow Anthropic's definition: automation = directive + feedback loop; augmentation = learning +
task iteration + validation; both normalised to classified conversations (the `none` share excluded),
which is what the published `collaboration_bucket_*` metrics do. The raw files are 100-220 MB, so they are
filtered with DuckDB over HTTP and only the GLOBAL collaboration rows are cached.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import date, datetime, timedelta, timezone

import duckdb
import httpx

from ...schema import Basis, Extraction, Observation, Tier
from ..base import CACHE, Connector, RawItem, expect, ua

HF = "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/"
FILES = [
    ("raw", HF + "release_2026_01_15/data/intermediate/aei_raw_claude_ai_2025-11-13_to_2025-11-20.csv"),
    ("raw", HF + "release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv"),
    ("monthly", HF + "release_2026_06_26/data/aei_claude_ai_2026-06-26.csv"),
]
AUTOMATION = {"directive", "feedback_loop"}
AUGMENTATION = {"learning", "task_iteration", "validation"}
QUERY = {
    "raw": "SELECT date_start, date_end, variable AS metric_id, replace(cluster_name, ' ', '_') AS mode, value "
    "FROM read_csv('{url}', header=true, all_varchar=true) WHERE geo_id='GLOBAL' AND facet='collaboration' "
    "AND variable='collaboration_pct'",
    "monthly": "SELECT date_start, date_end, metric_id, NULL AS mode, value FROM read_csv('{url}', header=true, all_varchar=true) "
    "WHERE geo_id='GLOBAL' AND category_name='overall' AND metric_id LIKE 'collaboration%'",
}


class AnthropicEi(Connector):
    source_id = "anthropic_ei"
    urls = [u for _, u in FILES]
    expect_series = ["anthropic_ei.global.augmentation_share.pt", "anthropic_ei.global.automation_share.pt"]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        items: list[RawItem] = []
        for kind, url in FILES:
            d = CACHE / self.source_id
            d.mkdir(parents=True, exist_ok=True)
            p = d / (hashlib.sha1(url.encode()).hexdigest()[:8] + ".filtered.csv")
            meta = p.with_suffix(".meta.json")
            head = httpx.head(url, headers={"User-Agent": ua()}, follow_redirects=True, timeout=60)
            etag, last_mod = head.headers.get("etag"), head.headers.get("last-modified")
            if (
                p.exists()
                and meta.exists()
                and not refetch
                and json.loads(meta.read_text()).get("etag") == etag
            ):
                m = json.loads(meta.read_text())
                items.append(
                    RawItem(
                        url,
                        p.read_bytes(),
                        m["http_status"],
                        datetime.fromisoformat(m["retrieved_at"]),
                        m["content_hash"],
                        last_mod,
                    )
                )
                continue
            con = duckdb.connect()
            con.execute("INSTALL httpfs; LOAD httpfs;")
            cur = con.execute(QUERY[kind].format(url=url))
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow([c[0] for c in cur.description])
            w.writerows(cur.fetchall())
            body = buf.getvalue().encode()
            item = RawItem(
                url,
                body,
                head.status_code,
                datetime.now(timezone.utc),
                hashlib.sha256(body).hexdigest(),
                last_mod,
            )
            p.write_bytes(body)  # ponytail: only the filtered rows are cached; the 200 MB source is not kept
            meta.write_text(
                json.dumps(
                    {
                        "etag": etag,
                        "http_status": item.http_status,
                        "retrieved_at": item.retrieved_at.isoformat(),
                        "content_hash": item.content_hash,
                    }
                )
            )
            items.append(item)
        return items

    def extract(self, items: list[RawItem]) -> list[Observation]:
        rows: list[Observation] = []
        for (kind, _), item in zip(FILES, items):
            recs = list(csv.DictReader(io.StringIO(item.body.decode())))
            expect(
                set(recs[0]) if recs else set(),
                {"date_start", "date_end", "metric_id", "value"},
                f"anthropic_ei {kind}",
            )
            by_period: dict[tuple[str, str], dict[str, float]] = {}
            for r in recs:
                key = (r["date_start"], r["date_end"])
                name = (
                    r["mode"]
                    if kind == "raw"
                    else r["metric_id"].removeprefix("collaboration_").removesuffix("_pct")
                )
                by_period.setdefault(key, {})[name] = float(r["value"])
            for (start, end), m in sorted(by_period.items()):
                modes = {k: v for k, v in m.items() if k in AUTOMATION | AUGMENTATION | {"none"}}
                classified = sum(v for k, v in modes.items() if k != "none")
                if classified <= 0:
                    continue
                buckets = {
                    "augmentation_share": m.get(
                        "bucket_augmentation", sum(modes.get(k, 0) for k in AUGMENTATION) / classified * 100
                    )
                    / 100,
                    "automation_share": m.get(
                        "bucket_automation", sum(modes.get(k, 0) for k in AUTOMATION) / classified * 100
                    )
                    / 100,
                }
                as_of = date.fromisoformat(end) - timedelta(days=1)
                snippet = json.dumps(
                    {
                        "date_start": start,
                        "date_end": end,
                        "modes_pct": modes,
                        "buckets": "automation = directive + feedback_loop; augmentation = learning + task_iteration + validation; normalised excluding none",
                    },
                    sort_keys=True,
                )
                for name, v in {
                    **buckets,
                    **{f"mode_{k}_share": val / 100 for k, val in modes.items()},
                }.items():
                    rows.append(
                        self.obs(
                            item,
                            series_key=f"anthropic_ei.global.{name}.pt",
                            unit="share",
                            as_of_date=as_of,
                            period_start=date.fromisoformat(start),
                            value_numeric=round(v, 4),
                            tier=Tier.MODEL_RELEASE,
                            audited_vs_reported=Basis.company_stated,
                            extraction_method=Extraction.api,
                            raw_snippet=snippet,
                        )
                    )
        return rows
