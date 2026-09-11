"""The query service: a stdlib HTTP server over one Store. Runs on Fly; the site proxies to it.

GET  /health              -> {ok, generated_at, observations}
POST /sql   {query}       -> read-only SQL (bearer token)
POST /ask   {question}    -> ask() (bearer token; daily spend cap)
GET  /golden              -> golden run (bearer token)
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .. import store as st
from ..analysis.metrics import run_metrics
from . import ask as ask_mod

log = logging.getLogger("ai-tracker.query")


class Service:
    def __init__(self) -> None:
        self.store = st.Store()
        if not self.store.derived:
            self.store.derived = run_metrics(self.store.con)
            self.store.semantic_tables()
        self.tools = ask_mod.Tools(self.store)
        self.token = os.environ.get("QUERY_TOKEN", "")
        self.cap = float(os.environ.get("QUERY_DAILY_USD_CAP", "5"))
        self.spend: dict[
            str, float
        ] = {}  # ponytail: in-memory ledger, resets on restart; a file if the cap ever matters
        self.lock = threading.Lock()

    def spent_today(self) -> float:
        return self.spend.get(date.today().isoformat(), 0.0)

    def add_spend(self, usd: float) -> None:
        with self.lock:
            self.spend[date.today().isoformat()] = self.spent_today() + usd


class Handler(BaseHTTPRequestHandler):
    svc: Service

    def _send(self, code: int, body: dict) -> None:
        raw = json.dumps(body, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authed(self) -> bool:
        return bool(self.svc.token) and self.headers.get("Authorization") == f"Bearer {self.svc.token}"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            n = self.svc.store.con.execute("SELECT count(*) FROM observations").fetchone()[0]
            return self._send(
                200,
                {
                    "ok": True,
                    "observations": n,
                    "model": ask_mod.MODEL,
                    "spent_today_usd": round(self.svc.spent_today(), 4),
                },
            )
        if self.path == "/golden":
            if not self._authed():
                return self._send(401, {"error": "unauthorised"})
            if not os.environ.get("ANTHROPIC_API_KEY"):
                return self._send(503, {"error": "no ANTHROPIC_API_KEY"})
            if self.svc.spent_today() >= self.svc.cap:
                return self._send(429, {"error": "daily cap reached", "cap_usd": self.svc.cap})
            res = ask_mod.golden(self.svc.store, self.svc.tools)
            self.svc.add_spend(sum(r["usd"] for r in res))
            return self._send(200, {"passed": sum(r["ok"] for r in res), "total": len(res), "results": res})
        return self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._authed():
            return self._send(401, {"error": "unauthorised"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", "0")) or 0) or b"{}")
        except ValueError:
            return self._send(400, {"error": "bad json"})
        if self.path == "/sql":
            return self._send(200, self.svc.tools.sql(str(body.get("query", ""))))
        if self.path == "/ask":
            q = str(body.get("question", "")).strip()
            if not q or len(q) > 2000:
                return self._send(400, {"error": "question must be 1-2000 characters"})
            if not os.environ.get("ANTHROPIC_API_KEY"):
                return self._send(503, {"error": "offline", "detail": "no model key configured"})
            if self.svc.spent_today() >= self.svc.cap:
                return self._send(429, {"error": "daily cap reached", "cap_usd": self.svc.cap})
            try:
                res = ask_mod.ask(self.svc.store, q, self.svc.tools)
            except Exception as e:  # noqa: BLE001 - surfaced to the drawer as offline
                log.exception("ask failed")
                return self._send(502, {"error": "model error", "detail": str(e)[:200]})
            self.svc.add_spend(res["usage"]["usd"])
            return self._send(200, res)
        return self._send(404, {"error": "not found"})

    def log_message(self, fmt: str, *args: object) -> None:
        log.info("%s %s", self.address_string(), fmt % args)


def serve(port: int = 8080) -> None:
    Handler.svc = Service()
    log.info("query service on :%d", port)
    ThreadingHTTPServer(("", port), Handler).serve_forever()
