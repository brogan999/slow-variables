"use client";

import { useState } from "react";

type Result = { columns: string[]; rows: unknown[][]; truncated: boolean } | { error: string };

export function QueryConsole({ initial }: { initial: string }) {
  const [sql, setSql] = useState(initial);
  const [res, setRes] = useState<Result | "offline" | null>(null);
  const [busy, setBusy] = useState(false);
  async function run(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      const r = await fetch("/api/query/sql", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ query: sql }) });
      setRes(r.status === 503 ? "offline" : await r.json());
    } catch { setRes("offline"); } finally { setBusy(false); }
  }
  return (
    <form onSubmit={run} className="flex flex-col gap-2">
      <textarea value={sql} onChange={(e) => setSql(e.target.value)} rows={5} spellCheck={false} aria-label="SQL" className="w-full resize-y rounded-md ring-hair bg-surface px-3 py-2 font-mono text-xs" />
      <div className="flex items-center gap-3 text-xs text-muted">
        <button type="submit" disabled={busy} className="rounded-full bg-ink px-3 py-1 text-xs text-bg disabled:opacity-50">{busy ? "Running…" : "Run"}</button>
        <span>Read-only, 200 rows, five seconds. Tables: observations, derived, status_events, indicators, metrics.</span>
      </div>
      <div aria-live="polite">
        {res === "offline" ? <p className="text-sm text-slow">The query service is offline; the saved analyses above are the nightly export.</p> : null}
        {res && res !== "offline" && "error" in res ? <pre className="text-xs text-slow whitespace-pre-wrap">{res.error}</pre> : null}
        {res && res !== "offline" && "columns" in res ? (
          <div className="overflow-x-auto"><table className="data w-full text-xs"><thead><tr>{res.columns.map((c) => <th key={c} scope="col">{c}</th>)}</tr></thead>
            <tbody>{res.rows.map((r, i) => <tr key={i}>{r.map((v, j) => <td key={j} className="tabular-nums max-w-[24rem] truncate">{typeof v === "object" ? JSON.stringify(v) : String(v ?? "")}</td>)}</tr>)}</tbody></table>
            {res.truncated ? <p className="text-xs text-muted mt-1">Truncated at 200 rows.</p> : null}</div>
        ) : null}
      </div>
    </form>
  );
}
