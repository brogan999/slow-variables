"""X route (v2 §5.4): never scraped. Two connectors, both tier 7, both `watch.x.<handle>.pt` value_text rows.

- `x_drop`: URLs a human drops into seed/x_drop.yaml, fetched through X's public oEmbed endpoint (no key).
- `x_list`: X API v2 `lists/{id}/tweets` over a curated List (the List membership is the handle verification);
  needs X_BEARER_TOKEN and X_LIST_ID, and is `optional` so the nightly stays green without them.
Links in a post to non-X pages are appended to the row so a human can turn a tier 1-6 artifact into a manual row.
Tweets never move a status.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path

import yaml

from ...schema import Basis, Extraction, Observation, Tier
from ..base import Connector, RawItem
from ..scrub import html_to_text, normalise

OEMBED = "https://publish.x.com/oembed?omit_script=true&url="
X_HOSTS = ("x.com", "twitter.com", "t.co")


def _row(
    c: Connector, item: RawItem, handle: str, text: str, when: date, url: str, links: list[str]
) -> Observation:
    body = normalise(text)[:500] + (" links: " + " ".join(links[:5]) if links else "")
    return c.obs(
        item.__class__(url, item.body, item.http_status, item.retrieved_at, item.content_hash),
        series_key=f"watch.x.{handle.lower()}.pt",
        unit="post",
        as_of_date=when,
        published_date=when,
        value_text=body,
        tier=Tier.ACTOR_STATEMENT,
        audited_vs_reported=Basis.reported,
        extraction_method=Extraction.api,
        raw_snippet=normalise(text)[:200],
    )


class XDrop(Connector):
    source_id = "x_drop"
    may_be_empty = True

    def __init__(self, path: Path = Path("seed/x_drop.yaml")) -> None:
        super().__init__()
        rows = (yaml.safe_load(path.read_text()) or {}).get("tweets") or [] if path.exists() else []
        self.tweets = [r["url"] for r in rows]
        self.urls = [OEMBED + u for u in self.tweets]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item in items:
            d = json.loads(item.body)
            html = d.get("html", "")
            m = re.search(r"<p[^>]*>(.*?)</p>", html, re.S)
            text = html_to_text(m.group(1)) if m else ""
            when_m = re.search(r">([A-Z][a-z]+ \d{1,2}, \d{4})</a>", html)
            when = (
                datetime.strptime(when_m.group(1), "%B %d, %Y").date() if when_m else item.retrieved_at.date()
            )
            handle = d.get("author_url", "").rstrip("/").rsplit("/", 1)[-1] or "unknown"
            links = [
                u
                for u in re.findall(r'href="([^"]+)"', m.group(1) if m else "")
                if not any(h in u for h in X_HOSTS)
            ]
            out.append(_row(self, item, handle, text, when, d.get("url") or item.url, links))
        return out


class XList(Connector):
    source_id = "x_list"
    optional = True

    def __init__(self) -> None:
        super().__init__()
        self.list_id = os.environ.get("X_LIST_ID", "")
        self.urls = [
            f"https://api.x.com/2/lists/{self.list_id}/tweets?max_results=100"
            "&tweet.fields=created_at,entities,author_id&expansions=author_id&user.fields=username"
        ]

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        token = os.environ.get("X_BEARER_TOKEN")
        if not token or not self.list_id:
            raise RuntimeError("X_BEARER_TOKEN and X_LIST_ID are not set; the drop file is the fallback")
        self.headers = {"Authorization": f"Bearer {token}"}
        return super().fetch(day, refetch)

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out = []
        for item in items:
            d = json.loads(item.body)
            users = {u["id"]: u["username"] for u in d.get("includes", {}).get("users", [])}
            for t in d.get("data", []):
                handle = users.get(t.get("author_id"), "unknown")
                when = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")).date()
                links = [
                    u.get("expanded_url", "")
                    for u in t.get("entities", {}).get("urls", [])
                    if not any(h in u.get("expanded_url", "") for h in X_HOSTS)
                ]
                out.append(
                    _row(
                        self,
                        item,
                        handle,
                        t.get("text", ""),
                        when,
                        f"https://x.com/{handle}/status/{t['id']}",
                        links,
                    )
                )
        return out
