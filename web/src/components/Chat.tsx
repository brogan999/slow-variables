"use client";

import Link from "next/link";
import { ArrowUp, Square } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnswerView, STAGES, useAsk, type Turn } from "@/components/AskShared";

const STARTERS = [
  "Where is value in the stack now?",
  "Where will value be in the future?",
  "What are the biggest bottlenecks in this entire loop at the moment?",
  "What will be commoditised in the future?",
  "What would have to be true for a company to be worth $1 trillion in 2035?",
];

// The Ask page: a conversation held only in this page's memory. Each question goes out with the last few turns,
// so a follow-up can say "that" and "they"; nothing is stored in the browser or on the server.
// One tree for both states, so the composer (and its focus) survives the first question.
export function Chat({ initialQ, initialFrom }: { initialQ?: string; initialFrom?: string }) {
  const { turns, busy, stage, send, stop, status } = useAsk(initialQ ? [{ q: initialQ, from: initialFrom }] : [], Boolean(initialQ));
  const [q, setQ] = useState("");
  const box = useRef<HTMLTextAreaElement>(null);
  const newest = useRef<HTMLElement>(null);

  async function ask(text: string, from?: string, retry = false) {
    if (!text.trim() || busy) return;
    if (!retry) setQ("");
    await send(text, from, retry);
    box.current?.focus();
  }

  useEffect(() => {  // arriving from a "Reason through this" link or the series box: the question is already on screen; ask it
    if (initialQ) void send(initialQ, initialFrom, false, true).then(() => box.current?.focus());
    // eslint-disable-next-line react-hooks/exhaustive-deps -- once, on arrival
  }, []);
  // a new question is pinned near the top, so its answer reads from its first line; the answer's arrival never scrolls
  useEffect(() => { if (busy) newest.current?.scrollIntoView({ behavior: "smooth", block: "start" }); }, [busy]);

  const empty = turns.length === 0;

  return (
    <div className={`mx-auto w-full max-w-[46rem] flex-1 flex flex-col ${empty ? "justify-center gap-7 py-10" : ""}`}>
      <p role="status" className="sr-only">{status}</p>
      {empty ? (
        <div className="flex flex-col gap-3 text-center">
          <h1 className="font-serif text-[2.1rem] md:text-[2.6rem] leading-[1.1] text-ink">What do you want to know about AI&apos;s economy?</h1>
          <p className="text-ink-2 leading-relaxed mx-auto">Answers come from the site&apos;s readings and the views of named writers. The reasoning between them is the model&apos;s, so read it as a draft.</p>
        </div>
      ) : (
        <div className="flex-1 flex flex-col gap-10 pt-8 pb-10">
          <h1 className="sr-only">Ask the data</h1>
          {turns.map((t, i) => {
            const isLast = i === turns.length - 1;
            return <TurnView key={i} ref={isLast ? newest : undefined} t={t} last={isLast} busy={busy} stage={stage} onAsk={(x) => ask(x)} onRetry={() => ask(t.q, t.from, true)} />;
          })}
          <div className="min-h-[40vh]" aria-hidden />
        </div>
      )}
      <form onSubmit={(e) => { e.preventDefault(); void ask(q); }} className={empty ? "" : "sticky bottom-0 bg-background pb-4 before:absolute before:inset-x-0 before:-top-6 before:h-6 before:bg-gradient-to-t before:from-background before:to-transparent before:pointer-events-none"}>
        <div className="flex items-end gap-2 rounded-2xl bg-surface p-2 pl-4 ring-1 ring-grid shadow-[0_1px_2px_rgba(22,29,34,0.04),0_6px_24px_-8px_rgba(22,29,34,0.14)] focus-within:ring-ink/45 focus-within:shadow-[0_1px_2px_rgba(22,29,34,0.06),0_8px_28px_-8px_rgba(22,29,34,0.2)] transition-shadow">
          <label htmlFor="ask-q" className="sr-only">Your question</label>
          <textarea
            id="ask-q" ref={box} value={q} rows={1} aria-describedby="ask-note" autoFocus
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void ask(q); } }}
            placeholder={empty ? "Ask about AI's pace, who profits, or what happens next…" : "Reply…"}
            className={`flex-1 resize-none field-sizing-content max-h-[240px] bg-transparent py-2 text-[1rem] leading-relaxed outline-none placeholder:text-muted ${empty ? "min-h-[4.5rem]" : ""}`}
          />
          {busy
            ? <button type="button" onClick={stop} aria-label="Stop" className="shrink-0 inline-flex items-center justify-center size-9 rounded-full bg-ink text-background hover:bg-ink-2"><Square className="size-3.5 fill-current" /></button>
            : <button type="submit" disabled={!q.trim()} aria-label="Send" className="shrink-0 inline-flex items-center justify-center size-9 rounded-full bg-ink text-background hover:bg-ink-2 disabled:bg-grid disabled:text-muted transition-colors"><ArrowUp className="size-4" /></button>}
        </div>
        <p id="ask-note" className="mt-2 text-[11px] text-muted text-center">Answers are drafts from an Anthropic model; every number is checked against the record it cites. Your words are never stored. <Link href="/legal#privacy" className="underline decoration-grid underline-offset-2">Privacy</Link> · <Link href="/legal#ai" className="underline decoration-grid underline-offset-2">AI content</Link> · <Link href="/sources" className="underline decoration-grid underline-offset-2">Sources</Link></p>
      </form>
      {empty ? (
        <ul className="flex flex-col sm:flex-row sm:flex-wrap sm:justify-center gap-2" aria-label="Questions to start with">
          {STARTERS.map((s) => <li key={s}><button type="button" onClick={() => ask(s)} className="w-full sm:w-auto rounded-xl sm:rounded-full border border-grid bg-surface px-3.5 py-2 sm:py-1.5 text-sm text-ink-2 hover:bg-surface-2 hover:text-ink transition-colors text-left">{s}</button></li>)}
        </ul>
      ) : null}
    </div>
  );
}

function TurnView({ t, last, busy, stage, onAsk, onRetry, ref }: { t: Turn; last: boolean; busy: boolean; stage: number; onAsk: (q: string) => void; onRetry: () => void; ref?: React.Ref<HTMLElement> }) {
  return (
    <section ref={ref} className="flex flex-col gap-5 scroll-mt-6">
      <p className="self-end max-w-[80%] rounded-2xl bg-surface-2 ring-1 ring-grid/70 px-4 py-2.5 text-ink leading-relaxed whitespace-pre-wrap">{t.q}</p>
      {last && busy && !t.a && !t.error ? (
        <p className="flex items-center gap-2.5 text-sm text-muted" aria-hidden><span className="size-2.5 rounded-full bg-ink animate-pulse" />{STAGES[stage]}</p>
      ) : null}
      <AnswerView t={t} last={last} busy={busy} onAsk={onAsk} onRetry={onRetry} />
    </section>
  );
}
