"use client";

import Link from "next/link";
import { ArrowUp, Check, Copy, RotateCcw, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnswerBody, citeOrder, type Cite } from "@/components/AnswerBody";

type Answer = { answer: string; status: "ok" | "revised" | "retried" | "blocked"; citations: Cite[]; followups?: string[] };
type Turn = { q: string; from?: string; a?: Answer; error?: string };

const OFFLINE = "The query service is offline right now. Everything on the site still links to its observations.";
const STAGES = ["Looking things up…", "Checking every number against the record it cites…", "Still working: a careful answer can take up to a minute."];
const STARTERS = [
  "Where is value in the stack now?",
  "Where will value be in the future?",
  "What are the biggest bottlenecks in this entire loop at the moment?",
  "What will be commoditised in the future?",
  "What would have to be true for a company to be worth $1 trillion in 2035?",
];
const pill = "rounded-full border border-grid bg-surface px-3.5 py-1.5 text-sm text-ink-2 hover:bg-surface-2 hover:text-ink transition-colors text-left disabled:opacity-50";
const icon = "inline-flex items-center justify-center size-8 rounded-lg text-muted hover:bg-surface-2 hover:text-ink transition-colors";

// The Ask page: a conversation held only in this page's memory. Each question goes out with the last few turns,
// so a follow-up can say "that" and "they"; nothing is stored in the browser or on the server.
export function Chat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(0);
  const abort = useRef<AbortController | null>(null);
  const box = useRef<HTMLTextAreaElement>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {  // arriving from a "Reason through this" link or the series box: ask its question at once
    const p = new URLSearchParams(window.location.search);
    const pre = p.get("q")?.trim();
    if (pre) void send(pre, p.get("from") ?? undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps -- once, on arrival
  }, []);
  useEffect(() => {
    if (!busy) return;
    const t = [setTimeout(() => setStage(1), 8000), setTimeout(() => setStage(2), 25000)];
    return () => t.forEach(clearTimeout);
  }, [busy]);
  useEffect(() => { if (turns.length) end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns, busy]);

  // retry replaces the last turn: it is asked again with the history that came before it
  async function send(text: string, from?: string, retry = false) {
    const question = text.trim();
    if (!question || busy) return;
    const before = retry ? turns.slice(0, -1) : turns;
    const history = before.filter((t) => t.a && t.a.status !== "blocked").slice(-4).map((t) => ({ q: t.q, a: t.a!.answer }));
    setTurns([...before, { q: question, from }]);
    if (!retry) setQ("");
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
      box.current?.focus();
    }
  }

  const empty = turns.length === 0;
  const composer = (
    <form onSubmit={(e) => { e.preventDefault(); void send(q); }} className="w-full">
      <div className="rounded-2xl bg-surface ring-1 ring-grid shadow-[0_1px_2px_rgba(22,29,34,0.04),0_6px_24px_-8px_rgba(22,29,34,0.12)] focus-within:ring-2 focus-within:ring-ink/60 transition-shadow">
        <label htmlFor="ask-q" className="sr-only">Your question</label>
        <textarea
          id="ask-q" ref={box} value={q} rows={empty ? 2 : 1} aria-describedby="ask-note" autoFocus={empty}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(q); } }}
          placeholder={empty ? "Ask about AI's pace, who profits, or what happens next…" : "Reply…"}
          className="block w-full resize-none field-sizing-content max-h-[240px] bg-transparent px-4 pt-3.5 pb-1 text-[1rem] leading-relaxed outline-none placeholder:text-muted"
        />
        <div className="flex items-center justify-between gap-3 px-3 pb-3 pt-1">
          <span className="text-xs text-muted pl-1">Every number checked against its record</span>
          {busy
            ? <button type="button" onClick={() => abort.current?.abort()} aria-label="Stop" className="inline-flex items-center justify-center size-8 rounded-full bg-ink text-background hover:bg-ink-2"><Square className="size-3.5 fill-current" /></button>
            : <button type="submit" disabled={!q.trim()} aria-label="Send" className="inline-flex items-center justify-center size-8 rounded-full bg-ink text-background hover:bg-ink-2 disabled:bg-grid disabled:text-muted transition-colors"><ArrowUp className="size-4" /></button>}
        </div>
      </div>
      <p id="ask-note" className="mt-2 text-[11px] text-muted text-center">Answers are drafts from an Anthropic model; every number links to its record. Your words are never stored. <Link href="/legal#privacy" className="underline decoration-grid underline-offset-2">Privacy</Link> · <Link href="/legal#ai" className="underline decoration-grid underline-offset-2">AI content</Link> · <Link href="/sources" className="underline decoration-grid underline-offset-2">Sources</Link></p>
    </form>
  );

  if (empty) {
    return (
      <div className="mx-auto w-full max-w-[48rem] flex-1 flex flex-col justify-center gap-7 py-10">
        <div className="flex flex-col gap-3 text-center">
          <h1 className="font-serif text-[2.1rem] md:text-[2.6rem] leading-[1.1] text-ink">What do you want to know about AI&apos;s economy?</h1>
          <p className="text-ink-2 leading-relaxed max-w-[52ch] mx-auto">Answers come from the site&apos;s readings and the views of named writers. The reasoning between them is the model&apos;s, so read it as a draft.</p>
        </div>
        {composer}
        <ul className="flex flex-wrap justify-center gap-2" aria-label="Questions to start with">
          {STARTERS.map((s) => <li key={s}><button type="button" onClick={() => send(s)} className={pill}>{s}</button></li>)}
        </ul>
      </div>
    );
  }

  return (
    <div className="mx-auto w-full max-w-[48rem] flex-1 flex flex-col">
      <h1 className="sr-only">Ask the data</h1>
      <div className="flex-1 flex flex-col gap-10 pt-8 pb-10" aria-live="polite" aria-busy={busy}>
        {turns.map((t, i) => <TurnView key={i} t={t} last={i === turns.length - 1} busy={busy} stage={stage} onAsk={(x) => send(x)} onRetry={() => send(t.q, t.from, true)} />)}
        <div ref={end} />
      </div>
      <div className="sticky bottom-0 bg-background pt-2 pb-4">{composer}</div>
    </div>
  );
}

function TurnView({ t, last, busy, stage, onAsk, onRetry }: { t: Turn; last: boolean; busy: boolean; stage: number; onAsk: (q: string) => void; onRetry: () => void }) {
  const [copied, setCopied] = useState(false);
  const a = t.a;
  const cites = a ? citeOrder(a.answer, a.citations) : [];
  return (
    <section className="flex flex-col gap-5">
      <p className="self-end max-w-[80%] rounded-2xl bg-surface-2 px-4 py-2.5 text-ink leading-relaxed whitespace-pre-wrap">{t.q}</p>
      {last && busy && !a && !t.error ? (
        <p className="flex items-center gap-2.5 text-sm text-muted"><span className="size-2.5 rounded-full bg-ink animate-pulse" aria-hidden />{STAGES[stage]}</p>
      ) : null}
      {t.error ? (
        <div className="flex items-center gap-2 text-sm text-error">
          <span>{t.error}</span>
          {last && !busy ? <button type="button" onClick={onRetry} className={icon} aria-label="Retry"><RotateCcw className="size-4" /></button> : null}
        </div>
      ) : null}
      {a ? (
        <div className="flex flex-col gap-3">
          {a.status === "blocked" ? <p className="text-xs text-error">This answer failed the citation check after a revision and a fresh attempt; the unverified numbers are marked and should not be relied on.</p> : null}
          <AnswerBody text={a.answer} cites={a.citations} className="font-serif text-[1.0625rem] leading-[1.7]" />
          <div className="flex flex-wrap items-center gap-1 -ml-1.5 text-xs text-muted">
            <button type="button" aria-label={copied ? "Copied" : "Copy"} title="Copy" className={icon} onClick={() => { void navigator.clipboard.writeText(a.answer.replace(/\s*\[[a-z]+:[A-Za-z0-9_.-]+\]/g, "")).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); }); }}>
              {copied ? <Check className="size-4" /> : <Copy className="size-4" />}
            </button>
            {last ? <button type="button" aria-label="Retry" title="Retry" disabled={busy} onClick={onRetry} className={icon}><RotateCcw className="size-4" /></button> : null}
            {a.status === "revised" ? <span className="ml-2">Revised once after the citation check</span> : null}
            {a.status === "retried" ? <span className="ml-2">Asked afresh after the first answer failed the citation check twice</span> : null}
          </div>
          {cites.length ? (
            <details className="text-xs text-ink-2">
              <summary className="cursor-pointer text-muted hover:text-ink w-fit">{cites.length} source{cites.length === 1 ? "" : "s"}</summary>
              <ol className="mt-2 flex flex-col gap-1.5 list-decimal pl-5">
                {cites.map((c) => <li key={`${c.kind}:${c.id}`}>{c.href ? <Link href={c.href} className="underline decoration-grid underline-offset-2 hover:text-ink break-words">{c.label ?? c.id}</Link> : <span className="break-words">{c.label ?? c.id}</span>}{c.value || c.date ? <span className="num text-muted"> · {[c.value, c.date].filter(Boolean).join(" · ")}</span> : null}</li>)}
              </ol>
            </details>
          ) : null}
          {last && a.followups?.length ? (
            <ul className="flex flex-wrap gap-2 pt-1" aria-label="Follow-up questions">
              {a.followups.map((f) => <li key={f}><button type="button" disabled={busy} onClick={() => onAsk(f)} className={pill}>{f}</button></li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
