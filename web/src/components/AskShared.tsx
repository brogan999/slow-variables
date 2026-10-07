"use client";

import { AssessCard, type Assess } from "@/components/AssessCard";
import Link from "next/link";
import { Check, Copy, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnswerBody, citeOrder, type Cite } from "@/components/AnswerBody";

// What the Ask page and the side panel share: one way of asking, and one way of drawing an answer.
export type Answer = { answer: string; status: "ok" | "revised" | "retried" | "blocked"; citations: Cite[]; followups?: string[]; card?: Assess | null };
export type Turn = { q: string; from?: string; a?: Answer; error?: string };

const OFFLINE = "The query service is offline right now. Everything on the site still links to its observations.";
export const STAGES = ["Looking things up…", "Checking every number against the record it cites…", "Still working: a careful answer can take up to a minute."];

/** A conversation held in memory. Each question goes out with the last few turns, so a follow-up can say "that". */
export function useAsk(initial: Turn[] | (() => Turn[]) = [], startBusy = false) {
  const [turns, setTurns] = useState<Turn[]>(initial);
  const [busy, setBusy] = useState(startBusy);
  const [stage, setStage] = useState(0);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!busy) return;
    const t = [setTimeout(() => setStage(1), 8000), setTimeout(() => setStage(2), 25000)];
    return () => t.forEach(clearTimeout);
  }, [busy]);

  // retry replaces the last turn: it is asked again with the history that came before it;
  // `arrived` does the same for a question already on screen when the page loaded
  async function send(text: string, from?: string, retry = false, arrived = false) {
    const question = text.trim();
    if (!question || (busy && !arrived)) return;
    const before = retry || arrived ? turns.slice(0, -1) : turns;
    const history = before.filter((t) => t.a && t.a.status !== "blocked").slice(-4).map((t) => ({ q: t.q, a: t.a!.answer }));
    setTurns([...before, { q: question, from }]);
    setStage(0);
    setBusy(true);
    const ctl = new AbortController();
    abort.current = ctl;
    const done = (patch: Partial<Turn>) => setTurns((ts) => ts.map((t, i) => (i === ts.length - 1 ? { ...t, ...patch } : t)));
    try {
      const r = await fetch("/api/query/ask", {
        method: "POST", headers: { "Content-Type": "application/json" }, signal: ctl.signal,
        body: JSON.stringify({ question: from ? `${question} (asked from ${from})` : question, history }),
      });
      const j = await r.json();
      if (r.status === 429) done({ error: "Today's question budget is spent; it resets at midnight UTC." });
      else if (!r.ok) done({ error: j.error === "offline" ? OFFLINE : `The service answered with an error (${j.error ?? r.status}).` });
      else done({ a: j });
    } catch (e) {
      done({ error: (e as Error).name === "AbortError" ? "Stopped." : OFFLINE });
    } finally {
      setBusy(false);
      abort.current = null;
    }
  }

  const last = turns[turns.length - 1];
  return {
    turns, busy, stage, send,
    stop: () => abort.current?.abort(),
    reset: () => { abort.current?.abort(); setTurns([]); },
    status: busy ? STAGES[stage] : last?.a ? "Answer ready." : last?.error ?? "",  // for a role="status" line
  };
}

const LOOK = {
  page: { icon: "inline-flex items-center justify-center size-8 rounded-lg text-muted hover:bg-surface-2 hover:text-ink transition-colors disabled:opacity-50", glyph: "size-4", body: "font-serif text-[1.0625rem] leading-[1.7]", error: "text-sm", list: "flex flex-col gap-0.5 pt-1 border-t border-grid/70", item: "w-full text-left text-sm text-ink-2 hover:text-ink hover:bg-surface-2 rounded-lg px-2 py-2 -mx-2 transition-colors" },
  panel: { icon: "inline-flex items-center justify-center size-7 rounded-[6px] text-muted hover:bg-ink/6 hover:text-ink transition-colors disabled:opacity-50", glyph: "size-3.5", body: "text-[14px] leading-[1.6]", error: "text-[13px]", list: "flex flex-wrap gap-1.5 pt-1", item: "text-left text-[13px] leading-snug text-ink-2 rounded-[14px] border border-ink/12 px-3 py-1.5 hover:bg-ink/5 hover:text-ink transition-colors disabled:opacity-50" },
};

/** One turn's reply: the error or the answer, its sources, the citation check's verdict, copy, retry and follow-ups. */
export function AnswerView({ t, last, busy, onAsk, onRetry, look = "page" }: { t: Turn; last: boolean; busy: boolean; onAsk: (q: string) => void; onRetry: () => void; look?: keyof typeof LOOK }) {
  const [copied, setCopied] = useState(false);
  const a = t.a, k = LOOK[look];
  const cites = a ? citeOrder(a.answer, a.citations) : [];
  return (
    <>
      {t.error ? (
        <div className={`flex items-center gap-2 text-error ${k.error}`}>
          <span>{t.error}</span>
          {last && !busy ? <button type="button" onClick={onRetry} className={k.icon} aria-label="Retry"><RotateCcw className={k.glyph} /></button> : null}
        </div>
      ) : null}
      {a ? (
        <div className="flex flex-col gap-3 min-w-0">
          {a.status === "blocked" ? <p className="text-xs text-error">This answer failed the citation check after a revision and a fresh attempt; the unverified numbers are marked and should not be relied on.</p> : null}
          {a.card ? <AssessCard card={a.card} /> : null}
          <AnswerBody text={a.answer} cites={a.citations} className={k.body} />
          {cites.length ? (
            <details className="text-xs text-ink-2">
              <summary className="cursor-pointer text-muted hover:text-ink w-fit">{cites.length} source{cites.length === 1 ? "" : "s"}</summary>
              <ol className="mt-2 flex flex-col gap-1.5 list-decimal pl-5">
                {cites.map((c) => <li key={`${c.kind}:${c.id}`}>{c.href ? <Link href={c.href} className="underline decoration-grid underline-offset-2 hover:text-ink break-words">{c.label ?? c.id}</Link> : <span className="break-words">{c.label ?? c.id}</span>}{c.value || c.date ? <span className="num text-muted"> · {[c.value, c.date].filter(Boolean).join(" · ")}</span> : null}</li>)}
              </ol>
            </details>
          ) : null}
          <div className="flex flex-wrap items-center gap-1 -ml-1.5 text-xs text-muted">
            <button type="button" aria-label={copied ? "Copied" : "Copy"} title="Copy" className={k.icon} onClick={() => { void navigator.clipboard.writeText(a.answer.replace(/\s*\[[a-z]+:[A-Za-z0-9_.-]+\]/g, "")).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); }); }}>
              {copied ? <Check className={k.glyph} /> : <Copy className={k.glyph} />}
            </button>
            {last ? <button type="button" aria-label="Retry" title="Retry" disabled={busy} onClick={onRetry} className={k.icon}><RotateCcw className={k.glyph} /></button> : null}
            {a.status === "revised" ? <span className="ml-2">Revised once after the citation check</span> : null}
            {a.status === "retried" ? <span className="ml-2">Asked afresh after the first answer failed the citation check twice</span> : null}
          </div>
          {last && a.followups?.length ? (
            <ul className={k.list} aria-label="Follow-up questions">
              {a.followups.map((f) => <li key={f}><button type="button" disabled={busy} onClick={() => onAsk(f)} className={k.item}>{f}</button></li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
