"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { AlignLeft, ArrowUp, FileText, History, Maximize2, MessageCircleQuestion, Plus, Scale, Square, SquarePen, X } from "lucide-react";
import { useEffect, useRef, useState, useSyncExternalStore } from "react";
import { AnswerView, STAGES, useAsk, type Turn } from "@/components/AskShared";
import { PAGES } from "@/lib/contents";
import { SITE } from "@/lib/site";

const KEY = "ask-panel";
const SECTIONS = "main h2[id], main section[id] > h2, main [id] > h2";
const ALWAYS = [
  [AlignLeft, "Summarise this page"],
  [Scale, "What is the evidence against this?"],
  [History, "What changed here recently?"],
] as const;
const iconBtn = "inline-flex items-center justify-center size-7 rounded-[6px] text-muted hover:bg-ink/6 hover:text-ink transition-colors";

function stored(): Turn[] {
  try {
    const v: unknown = JSON.parse(sessionStorage.getItem(KEY) ?? "[]");
    return Array.isArray(v) ? v : [];
  } catch { return []; }  // the server, a private window, or a blocked store: start empty
}

const watchTitle = (cb: () => void) => {
  const o = new MutationObserver(cb);
  o.observe(document.head, { childList: true, subtree: true, characterData: true });
  return () => o.disconnect();
};

function Glyph({ className = "size-3.5" }: { className?: string }) {
  return <svg viewBox="0 0 24 24" className={className} fill="currentColor" aria-hidden><path d="M12 3c.6 4.6 3.4 7.4 9 9-5.6 1.6-8.4 4.4-9 9-.6-4.6-3.4-7.4-9-9 5.6-1.6 8.4-4.4 9-9z" /></svg>;
}

/** The Ask side panel, mounted once in the root layout so the conversation and its open state survive a route change.
    A question costs money: nothing is sent on open or on a page change, only when the reader submits or picks a row. */
export function AskPanel() {
  const pathname = usePathname();
  const { turns, busy, stage, send, stop, reset, status } = useAsk(stored);
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [withPage, setWithPage] = useState(true);
  const [section, setSection] = useState("");
  const title = useSyncExternalStore(watchTitle, () => document.title, () => "").replace(` · ${SITE.name}`, "");
  const box = useRef<HTMLTextAreaElement>(null);
  const launcher = useRef<HTMLButtonElement>(null);
  const newest = useRef<HTMLElement>(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    if (busy) return;  // a reload keeps the conversation; only finished turns are kept
    try { sessionStorage.setItem(KEY, JSON.stringify(turns)); } catch { /* no store: the conversation lives in memory only */ }
  }, [turns, busy]);

  useEffect(() => {
    if (pathname === "/ask") return;
    const onKey = (e: KeyboardEvent) => {
      const mod = /Mac|iP/.test(navigator.platform) ? e.metaKey : e.ctrlKey;
      if (mod && !e.shiftKey && !e.altKey && e.key?.toLowerCase() === "j") { e.preventDefault(); setOpen((o) => !o); }
      // Escape closes the panel unless something above it (a source card, the search sheet) took the key first
      else if (e.key === "Escape" && !e.defaultPrevented && !document.querySelector(":popover-open")) setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [pathname]);

  useEffect(() => {  // focus goes to the composer on open and back to the launcher on close
    if (open) box.current?.focus(); else if (wasOpen.current) launcher.current?.focus();
    wasOpen.current = open;
  }, [open]);

  useEffect(() => {  // the section being read: the last named heading above a line a third of the way down the window
    if (!open) return;
    const read = () => {
      let name = "";
      for (const h of document.querySelectorAll(SECTIONS)) {
        if (h.getClientRects().length && h.getBoundingClientRect().top < window.innerHeight / 3) name = h.textContent?.trim() ?? "";
      }
      setSection(name);
    };
    const first = requestAnimationFrame(read);
    window.addEventListener("scroll", read, { passive: true });
    return () => { cancelAnimationFrame(first); window.removeEventListener("scroll", read); };
  }, [open, pathname]);

  useEffect(() => {  // the composer grows with its text
    const el = box.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [q, open]);

  // a new question is pinned to the top of the panel, so its answer reads from its first line
  useEffect(() => { if (busy) newest.current?.scrollIntoView({ block: "start" }); }, [busy]);

  if (pathname === "/ask") return null;  // the full page is the same conversation tool; no second one beside it

  const from = `${pathname} — ${title}${section ? `, section "${section}"` : ""}`;
  async function ask(text: string, page = withPage) {
    if (!text.trim() || busy) return;
    setQ("");
    setWithPage(true);  // leaving the page out lasts one question
    await send(text, page ? from : undefined);
    box.current?.focus();
  }

  if (!open) {
    return (
      <button ref={launcher} type="button" onClick={() => setOpen(true)} aria-label="Ask about this page" title="Ask about this page" aria-keyshortcuts="Meta+J Control+J" aria-expanded={false}
        className="ask-launcher fixed bottom-4 right-4 z-40 inline-flex size-10 sm:size-11 items-center justify-center rounded-full border border-ink/12 bg-surface text-ink shadow-[0_2px_10px_rgba(22,29,34,0.14)] hover:bg-surface-2 transition-colors print:hidden">
        <Glyph className="size-5" />
      </button>
    );
  }

  const own = PAGES[pathname]?.question;
  return (
    <div role="dialog" aria-label="Ask about this page" className="ask-panel fixed inset-y-0 right-0 z-50 flex w-full sm:w-[400px] flex-col border-l border-ink/10 bg-surface font-sans text-[14px] leading-[1.6] text-ink shadow-[-10px_0_30px_-18px_rgba(22,29,34,0.3)] animate-in slide-in-from-right duration-[180ms] motion-reduce:animate-none print:hidden">
      <p role="status" className="sr-only">{status}</p>
      <header className="flex h-11 shrink-0 items-center gap-1 pl-4 pr-2">
        <span className="flex items-center gap-1.5 font-medium"><Glyph />Ask</span>
        <span className="flex-1" />
        <button type="button" onClick={() => { reset(); setQ(""); box.current?.focus(); }} aria-label="New chat" title="New chat" className={iconBtn}><SquarePen className="size-4" /></button>
        <Link href="/ask" onClick={() => setOpen(false)} aria-label="Open in full page" title="Open in full page" className={iconBtn}><Maximize2 className="size-4" /></Link>
        <button type="button" onClick={() => setOpen(false)} aria-label="Close" title="Close" className={iconBtn}><X className="size-4" /></button>
      </header>

      <div className="flex-1 overflow-y-auto overscroll-contain px-4">
        {turns.length === 0 ? (
          <div className="flex flex-col gap-4 pt-8 pb-4">
            <div className="flex flex-col gap-1">
              <span className="inline-flex size-8 items-center justify-center rounded-full border border-ink/12"><Glyph className="size-4" /></span>
              <h2 className="mt-2 text-[18px] font-semibold leading-snug">What do you want to know?</h2>
              <p className="text-muted">Ask about this page or anything else on the site. Answers cite the records they rest on; the reasoning between them is a draft.</p>
            </div>
            <ul className="-mx-2 flex flex-col" aria-label="Questions to start with">
              {[...(own ? [[MessageCircleQuestion, own] as const] : []), ...ALWAYS].map(([Icon, s]) => (
                <li key={s}><button type="button" onClick={() => ask(s, true)} className="flex w-full items-start gap-2.5 rounded-[6px] px-2 py-1.5 text-left text-ink-2 hover:bg-ink/5 hover:text-ink transition-colors"><Icon className="mt-[3px] size-4 shrink-0 text-muted" />{s}</button></li>
              ))}
            </ul>
          </div>
        ) : (
          <div className="flex flex-col gap-6 pt-4">
            {turns.map((t, i) => {
              const last = i === turns.length - 1;
              return (
                <section key={i} ref={last ? newest : undefined} className="flex flex-col gap-3 scroll-mt-2">
                  <p className="max-w-[85%] self-end whitespace-pre-wrap break-words rounded-[16px] bg-ink/6 px-3.5 py-2">{t.q}</p>
                  <div className="flex items-start gap-2.5">
                    <span className="mt-px inline-flex size-6 shrink-0 items-center justify-center rounded-full border border-ink/12" aria-hidden><Glyph className="size-3" /></span>
                    <div className="flex min-w-0 flex-1 flex-col gap-3">
                      {last && busy && !t.a && !t.error ? <p className="ask-shimmer w-fit" aria-hidden>{stage ? STAGES[stage] : "Thinking…"}</p> : null}
                      <AnswerView look="panel" t={t} last={last} busy={busy} onAsk={(x) => ask(x)} onRetry={() => send(t.q, t.from, true)} />
                    </div>
                  </div>
                </section>
              );
            })}
            <div className="min-h-[45vh]" aria-hidden />
          </div>
        )}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); void ask(q); }} className="shrink-0 px-3 pb-3 pt-1">
        <div className="flex flex-col gap-1.5 rounded-[14px] border border-ink/14 bg-surface p-2.5 shadow-[0_1px_3px_rgba(22,29,34,0.06)] transition-colors focus-within:border-ink/40">
          <label htmlFor="ask-panel-q" className="sr-only">Your question</label>
          <textarea
            id="ask-panel-q" ref={box} value={q} rows={1}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); void ask(q); } }}
            placeholder="Ask anything about this page or the site…"
            className="max-h-40 min-h-[2.75rem] w-full resize-none bg-transparent px-1 text-[16px] leading-[1.5] placeholder:text-muted sm:text-[14px]"
          />
          <div className="flex items-center gap-2">
            {withPage ? (
              <span className="inline-flex min-w-0 items-center gap-1 rounded-[6px] border border-ink/12 py-0.5 pl-1.5 pr-0.5 text-[12px] text-ink-2" title={from}>
                <FileText className="size-3.5 shrink-0 text-muted" />
                <span className="truncate">{title}{section ? <span className="text-muted"> · {section}</span> : null}</span>
                <button type="button" onClick={() => setWithPage(false)} aria-label="Leave this page out of the next question" title="Ask about the whole site" className="inline-flex size-5 shrink-0 items-center justify-center rounded-[4px] text-muted hover:bg-ink/6 hover:text-ink"><X className="size-3" /></button>
              </span>
            ) : (
              <button type="button" onClick={() => setWithPage(true)} className="inline-flex items-center gap-1 rounded-[6px] px-1.5 py-0.5 text-[12px] text-muted hover:bg-ink/6 hover:text-ink"><Plus className="size-3.5" />Add this page</button>
            )}
            <span className="flex-1" />
            {busy
              ? <button type="button" onClick={stop} aria-label="Stop" className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ink text-surface hover:bg-ink-2"><Square className="size-3 fill-current" /></button>
              : <button type="submit" disabled={!q.trim()} aria-label="Send" className="inline-flex size-7 shrink-0 items-center justify-center rounded-full bg-ink text-surface transition-colors hover:bg-ink-2 disabled:bg-ink/10 disabled:text-ink/35"><ArrowUp className="size-4" /></button>}
          </div>
        </div>
        <p className="mt-1.5 text-center text-[11px] leading-snug text-muted">Drafts from an Anthropic model; every number is checked against its record. <Link href="/legal#privacy" className="underline decoration-grid underline-offset-2">Privacy</Link> · <Link href="/legal#ai" className="underline decoration-grid underline-offset-2">AI content</Link></p>
      </form>
    </div>
  );
}
