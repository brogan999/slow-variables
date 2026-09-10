"""One connector per source: fetch() caches raw bytes per day; extract() turns them into Observations."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import urllib.robotparser
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import httpx

from ..schema import FetchLog, Observation, short_hash

CACHE = Path("ingest/cache")


def ua() -> str:
    return os.environ.get(
        "AI_TRACKER_USER_AGENT", "slow-variables/0.1 github.com/brogan999/slow-variables"
    )


class LayoutChanged(RuntimeError):
    """A source changed shape. Fail loudly; never return zero items silently."""


@dataclass(frozen=True)
class RawItem:
    url: str
    body: bytes
    http_status: int
    retrieved_at: datetime
    content_hash: str
    last_modified: str | None = None

    @property
    def published_date(self) -> date:
        if self.last_modified:
            try:
                return parsedate_to_datetime(self.last_modified).date()
            except (TypeError, ValueError):
                pass
        return self.retrieved_at.date()


def expect(present: set[str], required: set[str], where: str) -> None:
    missing = required - present
    if missing:
        raise LayoutChanged(f"{where}: missing {sorted(missing)}")


_robots: dict[str, urllib.robotparser.RobotFileParser] = {}


def robots_ok(url: str) -> bool:
    """robots.txt fetched with our own User-Agent (and the curl fallback CDNs need); unreachable = allowed,
    forbidden (401/403) = disallowed, as urllib's parser would treat it."""
    u = httpx.URL(url)
    host = f"{u.scheme}://{u.host}"
    if host not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            hdrs = {"User-Agent": ua()}
            r = httpx.get(f"{host}/robots.txt", headers=hdrs, follow_redirects=True, timeout=30)
            body, status = r.content, r.status_code
            if status == 403 and shutil.which("curl"):
                body, status = _curl(f"{host}/robots.txt", hdrs)
            if status in (401, 403):
                rp.disallow_all = True
            elif status >= 400:
                rp.allow_all = True
            else:
                rp.parse(body.decode("utf-8", "ignore").splitlines())
        except Exception:
            rp.allow_all = True
        _robots[host] = rp
    return _robots[host].can_fetch(ua(), url)


def _curl(url: str, headers: dict[str, str]) -> tuple[bytes, int]:
    args = ["curl", "-sL", "--max-time", "60", "-w", "\n%{http_code}", url]
    for k, v in headers.items():
        args += ["-H", f"{k}: {v}"]
    out = subprocess.run(args, capture_output=True, check=False).stdout
    body, _, code = out.rpartition(b"\n")
    return body, int(code or 0)


class Connector:
    source_id: str = ""
    urls: list[str] = []
    headers: dict[str, str] = {}
    kind: str = "api"  # html/pdf kinds are robots-checked
    post_json: dict[str, Any] | None = None  # set to POST a JSON body instead of GET
    expect_series: list[str] = []
    version: str = "1"
    may_be_empty: bool = False  # a connector with nothing left to verify is healthy, not broken
    optional: bool = False  # a failure is logged and shown as degraded but does not fail the nightly run

    def __init__(self) -> None:
        self.scrubbed: list[str] = []
        self.errors: list[str] = []  # per-row failures that should fail the run but keep the good rows

    def fetch(self, day: date, refetch: bool = False) -> list[RawItem]:
        out: list[RawItem] = []
        for url in self.urls:
            out.append(self.fetch_one(url, day, refetch))
        return out

    def fetch_one(self, url: str, day: date, refetch: bool = False) -> RawItem:
        d = CACHE / self.source_id / day.isoformat()
        d.mkdir(parents=True, exist_ok=True)
        p = d / (short_hash(url, json.dumps(self.post_json, sort_keys=True))[:8] + ".bin")
        meta = p.with_suffix(".meta.json")
        if p.exists() and meta.exists() and not refetch:
            m = json.loads(meta.read_text())
            return RawItem(
                url,
                p.read_bytes(),
                m["http_status"],
                datetime.fromisoformat(m["retrieved_at"]),
                m["content_hash"],
                m.get("last_modified"),
            )
        if self.kind in ("html", "pdf") and not robots_ok(url):
            raise PermissionError(f"robots.txt disallows {url}")
        hdrs = {"User-Agent": ua(), **self.headers}
        if self.post_json is not None:
            r = httpx.post(url, json=self.post_json, headers=hdrs, timeout=60)
        else:
            r = httpx.get(url, headers=hdrs, follow_redirects=True, timeout=60)
        if r.status_code == 403 and self.post_json is None and shutil.which("curl"):
            # some CDNs fingerprint Python's TLS stack and 403 it while serving curl the same public page
            body, status = _curl(url, hdrs)
            if status < 400:
                r = httpx.Response(status, content=body, request=r.request)
        r.raise_for_status()
        item = RawItem(
            url,
            r.content,
            r.status_code,
            datetime.now(timezone.utc),
            hashlib.sha256(r.content).hexdigest(),
            r.headers.get("last-modified"),
        )
        p.write_bytes(r.content)
        meta.write_text(
            json.dumps(
                {
                    "url": url,
                    "http_status": item.http_status,
                    "retrieved_at": item.retrieved_at.isoformat(),
                    "content_hash": item.content_hash,
                    "last_modified": item.last_modified,
                }
            )
        )
        return item

    def extract(self, items: list[RawItem]) -> list[Observation]:
        raise NotImplementedError

    def obs(self, item: RawItem, **kw: Any) -> Observation:
        kw.setdefault("published_date", item.published_date)
        return Observation(
            source_id=kw.pop("source_id", None) or self.source_id,
            extractor_version=f"{self.source_id}-{self.version}",
            url=item.url,
            content_hash=item.content_hash,
            http_status=item.http_status,
            retrieved_at=item.retrieved_at,
            **kw,
        )

    def run(self, day: date, refetch: bool = False) -> tuple[list[Observation], FetchLog]:
        t0 = datetime.now(timezone.utc)
        try:
            items = self.fetch(day, refetch)
            rows = self.extract(items)
            if not rows and not self.may_be_empty:
                raise LayoutChanged(f"{self.source_id}: 0 items")
            keys = {r.series_key for r in rows}
            missing = [pat for pat in self.expect_series if not any(fnmatch(k, pat) for k in keys)]
            if missing:
                raise LayoutChanged(f"{self.source_id}: expected series missing {missing}")
        except Exception as e:  # one broken source must never block the run
            return [], FetchLog(
                source_id=self.source_id,
                started_at=t0,
                finished_at=datetime.now(timezone.utc),
                ok=False,
                error=repr(e)[:500],
                scrubbed=self.scrubbed,
            )
        return rows, FetchLog(
            source_id=self.source_id,
            started_at=t0,
            finished_at=datetime.now(timezone.utc),
            ok=not self.errors,
            error="; ".join(self.errors)[:500] or None,
            http_status=items[-1].http_status if items else None,
            bytes=sum(len(i.body) for i in items),
            items_found=len(rows),
            scrubbed=self.scrubbed,
        )
