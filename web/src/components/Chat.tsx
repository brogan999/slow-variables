"use client";

import Link from "next/link";
import { ArrowUp, Check, Copy, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnswerBody, citeOrder, type Cite } from "@/components/AnswerBody";
import { Button } from "@/components/ui/button";

type Answer = { answer: string; status: "ok" | "revised" | "retried" | "blocked"; citations: Cite[]; followups?: string[] };
type Turn = { q: string; from?: string; a?: Answer; error?: string };

const OFFLINE = "The query service is offline right now. Everything on the site still links to its observations.";
const STAGES = ["Looking things up…", "Checking every number against the record it cites…", "Still working: a careful answer can take up to a minute."];
const STARTERS = [
  "Which futures do tonight's readings still allow, and who argues for each?",
  "What does the tracker hold on Harvey, and what would decide whether it wins?",
  "Do labs keep their margins as open models catch up? Who says what?",
  "How fast is the length of task AI can finish growing, and how sure is that?",
];

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
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [turns, busy]);

  async function send(text: string, from?: string) {
    const question = text.trim();
    if (!question || busy) return;
    const history = turns.filter((t) => t.a && t.a.status !== "blocked").slice(-4).map((t) => ({ q: t.q, a: t.a!.answer }));
    setTurns((ts) => [...ts, { q: question, from }]);
    setQ("");
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

  return (
    <div className="mx-auto w-full max-w-[46rem] flex flex-col min-h-[calc(100dvh-14rem)]">
      <div className="flex-1 flex flex-col gap-10 pb-8" aria-live="polite" aria-busy={busy}>
        {turns.length ? <h1 className="sr-only">Ask the data</h1> : null}
        {turns.length === 0 ? (
          <div className="flex flex-col gap-5 pt-[8vh]">
            <h1 className="display text-[2.25rem] md:text-[2.75rem] leading-[1.05]">Ask the data</h1>
            <p className="text-ink-2 leading-relaxed max-w-[56ch]">Answers come from the same store as the site: its readings, the claims named writers make about what happens next, and the scenarios they argue. Every number is checked against the record it cites and every view links to whoever holds it; the reasoning between them is the model&apos;s, so read it as a draft.</p>
            <ul className="grid gap-2 sm:grid-cols-2">
              {STARTERS.map((s) => <li key={s}><button type="button" onClick={() => send(s)} className="w-full h-full text-left text-sm text-ink-2 panel px-3 py-2.5 hover:bg-surface-2 hover:text-ink">{s}</button></li>)}
            </ul>
          </div>
        ) : null}
        {turns.map((t, i) => <TurnView key={i} t={t} last={i === turns.length - 1} busy={busy} stage={stage} onAsk={(x) => send(x)} />)}
        <div ref={end} />
      </div>
      <form onSubmit={(e) => { e.preventDefault(); void send(q); }} className="sticky bottom-0 bg-background pt-2 pb-4">
        <div className="panel flex items-end gap-2 p-2 focus-within:ring-2 focus-within:ring-ink">
          <label htmlFor="ask-q" className="sr-only">Your question</label>
          <textarea
            id="ask-q" ref={box} value={q} rows={1} aria-describedby="ask-note"
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void send(q); } }}
            placeholder={turns.length ? "Ask a follow-up…" : "Ask about AI's pace, who profits, or what happens next…"}
            className="flex-1 resize-none field-sizing-content max-h-[200px] bg-transparent px-2 py-1.5 text-[1rem] leading-relaxed outline-none placeholder:text-muted"
          />
          {busy
            ? <Button type="button" size="icon" variant="outline" onClick={() => abort.current?.abort()} aria-label="Stop"><Square /></Button>
            : <Button type="submit" size="icon" disabled={!q.trim()} aria-label="Send"><ArrowUp /></Button>}
        </div>
        <p id="ask-note" className="mt-2 text-[11px] text-muted text-center">Sent with this conversation&apos;s last few turns to an Anthropic model through the site&apos;s query service, which records each answer&apos;s outcome and cited ids, never your words. <Link href="/legal#privacy" className="underline decoration-grid underline-offset-2">Privacy</Link> · <Link href="/legal#ai" className="underline decoration-grid underline-offset-2">AI content</Link></p>
      </form>
    </div>
  );
}

function TurnView({ t, last, busy, stage, onAsk }: { t: Turn; last: boolean; busy: boolean; stage: number; onAsk: (q: string) => void }) {
  const [copied, setCopied] = useState(false);
  const a = t.a;
  const cites = a ? citeOrder(a.answer, a.citations) : [];
  return (
    <section className="flex flex-col gap-4">
      <p className="self-end max-w-[85%] rounded-2xl bg-surface-2 px-4 py-2.5 text-ink whitespace-pre-wrap">{t.q}</p>
      {last && busy && !a && !t.error ? <p className="text-sm text-muted animate-pulse">{STAGES[stage]}</p> : null}
      {t.error ? <p className="text-sm text-error">{t.error}</p> : null}
      {a ? (
        <div className="flex flex-col gap-3">
          {a.status === "blocked" ? <p className="text-xs text-error">This answer failed the citation check after a revision and a fresh attempt; the unverified numbers are marked and should not be relied on.</p> : null}
          <AnswerBody text={a.answer} cites={a.citations} />
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted">
            <button type="button" onClick={() => { void navigator.clipboard.writeText(a.answer.replace(/\s*\[[a-z]+:[A-Za-z0-9_.-]+\]/g, "")).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1500); }); }} className="inline-flex items-center gap-1 hover:text-ink">
              {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}{copied ? "Copied" : "Copy"}
            </button>
            {a.status === "revised" ? <span>Revised once after the citation check</span> : null}
            {a.status === "retried" ? <span>Asked afresh after the first answer failed the citation check twice</span> : null}
          </div>
          {cites.length ? (
            <details className="text-xs text-ink-2">
              <summary className="cursor-pointer text-muted hover:text-ink">{cites.length} source{cites.length === 1 ? "" : "s"}</summary>
              <ol className="mt-2 flex flex-col gap-1.5 list-decimal pl-5">
                {cites.map((c) => <li key={`${c.kind}:${c.id}`}>{c.href ? <Link href={c.href} className="underline decoration-grid underline-offset-2 hover:text-ink break-words">{c.label ?? c.id}</Link> : <span className="break-words">{c.label ?? c.id}</span>}{c.value || c.date ? <span className="num text-muted"> · {[c.value, c.date].filter(Boolean).join(" · ")}</span> : null}</li>)}
              </ol>
            </details>
          ) : null}
          {last && a.followups?.length ? (
            <ul className="flex flex-col gap-1.5" aria-label="Follow-up questions">
              {a.followups.map((f) => <li key={f}><button type="button" disabled={busy} onClick={() => onAsk(f)} className="text-left text-sm text-ink-2 hover:text-ink underline decoration-grid underline-offset-4">{f}</button></li>)}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
