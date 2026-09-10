"""Watchlist over RSS/Atom feeds. A matching post becomes a value_text observation so the nightly PR surfaces it.

The point is never to miss a data release on a page we cannot scrape (openai.com blocks the fetcher; its feed
does not). A human turns the post into figures via seed/manual_observations.yaml; the watch row is the reminder.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import replace
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import yaml

from ...schema import Basis, Extraction, Observation, Source
from ..base import Connector, RawItem
from ..scrub import html_to_text, normalise

ATOM = "{http://www.w3.org/2005/Atom}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"  # Substack and others ship the full post here


def parse_feed(body: bytes) -> list[tuple[str, str, str, date | None, str]]:
    """(title, link, body, published, summary) for RSS 2.0 and Atom; body prefers the full post, summary never does."""
    root = ET.fromstring(body)
    out = []
    for it in root.iter("item"):
        d = it.findtext("pubDate")
        out.append(
            (
                (it.findtext("title") or "").strip(),
                (it.findtext("link") or "").strip(),
                it.findtext(CONTENT) or it.findtext("description") or "",
                parsedate_to_datetime(d).date() if d else None,
                it.findtext("description") or "",
            )
        )
    for e in root.iter(f"{ATOM}entry"):
        link = e.find(f"{ATOM}link")
        d = e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated")
        out.append(
            (
                (e.findtext(f"{ATOM}title") or "").strip(),
                (link.get("href") if link is not None else "") or "",
                e.findtext(f"{ATOM}summary") or e.findtext(f"{ATOM}content") or "",
                datetime.fromisoformat(d.replace("Z", "+00:00")).date() if d else None,
                e.findtext(f"{ATOM}summary") or "",
            )
        )
    return out


class Feeds(Connector):
    source_id = "feeds"
    kind = "api"  # feed rows; html page-watch rows are robots-checked per URL in fetch

    def __init__(self, path: Path = Path("seed/sources.yaml")) -> None:
        super().__init__()
        rows = (yaml.safe_load(path.read_text()) or {}).get("sources") or []
        self.sources = [Source(**r) for r in rows if r.get("connector") == "feeds"]
        self.urls = [s.url for s in self.sources]

    def extract(self, items: list[RawItem]) -> list[Observation]:
        out: list[Observation] = []
        for src, item in zip(self.sources, items):
            if (
                src.kind.value == "html"
            ):  # page watch: a blog with no feed; one row per content change, keyed by hash
                text = normalise(html_to_text(item.body.decode("utf-8", "ignore")))
                for slug, pattern in src.watch.items():
                    if re.search(pattern, text, re.I):
                        out.append(
                            self.obs(
                                item,
                                source_id=src.id,
                                series_key=f"watch.{src.id}.{slug}.pt",
                                unit="page",
                                as_of_date=item.retrieved_at.date(),
                                published_date=item.retrieved_at.date(),
                                value_text=f"page changed; matches {slug} (content hash {item.content_hash[:12]})",
                                tier=src.default_tier,
                                audited_vs_reported=Basis.reported,
                                extraction_method=Extraction.scrape,
                                raw_snippet=text[:200],
                            )
                        )
                continue
            posts = parse_feed(item.body)
            if not posts:
                self.errors.append(f"{src.id}: feed parsed to 0 posts")
                continue
            for title, link, _body, published, summary in posts:
                text = normalise(
                    f"{title} {html_to_text(summary)}"
                )  # title + summary only: a full body matches everything
                for slug, pattern in src.watch.items():
                    if re.search(pattern, text, re.I) and published:
                        out.append(
                            self.obs(
                                replace(item, url=link or item.url),
                                source_id=src.id,
                                series_key=f"watch.{src.id}.{slug}.pt",
                                unit="post",
                                as_of_date=published,
                                published_date=published,
                                value_text=title,
                                tier=src.default_tier,
                                audited_vs_reported=Basis.reported,
                                extraction_method=Extraction.api,
                                raw_snippet=title,
                            )
                        )
        return out
