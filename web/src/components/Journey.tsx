"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ACTS, STOPS, STOP_OF } from "@/lib/nav";
import { SITE } from "@/lib/site";

// the end of the path hands over to Ask when it is running, otherwise to the evidence
const END = SITE.askOnline
  ? { href: "/ask", name: "Your turn: ask the data", line: "Every number on the path is in the data. Put your own question to it.", short: "Put your own question to the data." }
  : { href: "/indicators", name: "Your turn: all the evidence", line: "Every number on the path traces to a dated record. The evidence pages hold them all.", short: "Every gauge, with what it tells you." };

const under = (path: string, href: string) => path === href || path.startsWith(`${href}/`);
const stopAt = (path: string) => STOP_OF.find(([href]) => under(path, href))?.[1];

/** The path across the top of every stop and deep dive: done, here and ahead, by position in the list. */
export function JourneyRail() {
  const n = stopAt(usePathname());
  if (!n) return null;
  const here = STOPS.findIndex((s) => s.n === n);
  const stop = STOPS[here];
  return (
    <nav aria-label="The reading path" className="mb-8 md:mb-10 border-b border-grid pb-4">
      <div className="xl:hidden flex flex-col gap-2">
        <span className="eyebrow">Stop {stop.n} · Act {stop.act} · {stop.name}</span>
        <div className="flex gap-1" aria-hidden>
          {STOPS.map((s, i) => <span key={s.n} className={`h-1 flex-1 rounded-full ${i <= here ? "bg-ink" : "bg-grid"}`} />)}
        </div>
      </div>
      <ol className="hidden xl:flex gap-x-6 text-sm">
        {ACTS.map((a) => (
          <li key={a.act} className="flex flex-col gap-2">
            <span className="eyebrow">Act {a.act} · {a.title}</span>
            <ol className="flex gap-x-3">
              {a.stops.map((s) => {
                const i = STOPS.findIndex((x) => x.n === s.n);
                const state = i < here ? "done" : i === here ? "here" : "ahead";
                return (
                  <li key={s.n}>
                    <Link href={s.href} aria-current={state === "here" ? "step" : undefined} className="group inline-flex items-center gap-1.5 whitespace-nowrap">
                      <span className={`num inline-flex h-6 min-w-6 items-center justify-center rounded-full border px-1 text-[11px] ${state === "ahead" ? "border-axis bg-surface text-muted" : "border-ink bg-ink text-background"}`}>{state === "done" ? "✓" : s.n}</span>
                      <span className={`${state === "here" ? "font-semibold text-ink" : "text-ink-2 group-hover:text-ink"}`}>{s.name}</span>
                    </Link>
                  </li>
                );
              })}
            </ol>
          </li>
        ))}
      </ol>
    </nav>
  );
}

const card = "group block rounded-[4px] p-5 md:p-6";

/** The foot of every page: a stop hands on to the next; a deep dive offers the way back or ahead; an evidence page
 * returns to the path. The home page, Ask and the legal notice carry none. */
export function NextStop() {
  const path = usePathname();
  const here = STOPS.findIndex((s) => s.href === path);
  if (here >= 0) {
    const next = STOPS[here + 1];
    return (
      <nav aria-label="Next stop" className="mt-16">
        <Link href={next ? next.href : END.href} className={`${card} max-w-3xl bg-ink text-background md:p-8`}>
          <span className="eyebrow text-background/70">{next ? `Next stop · ${next.n} · Act ${next.act}` : "The end of the path"}</span>
          <span className="mt-2 block display text-2xl md:text-3xl">{next ? next.name : END.name} <span aria-hidden className="inline-block transition-transform group-hover:translate-x-1">→</span></span>
          <span className="mt-2 block font-serif text-lg text-background/80">{next ? next.question : END.line}</span>
        </Link>
      </nav>
    );
  }
  const parent = stopAt(path);
  if (parent) {
    const i = STOPS.findIndex((s) => s.n === parent);
    const stop = STOPS[i];
    const next = STOPS[i + 1];
    return (
      <nav aria-label="Back to the path" className="mt-16 grid max-w-4xl gap-3 md:grid-cols-2">
        <Link href={stop.href} className={`${card} border border-grid bg-surface`}>
          <span className="eyebrow">Back to stop {stop.n} · Act {stop.act}</span>
          <span className="mt-2 block display text-xl"><span aria-hidden>← </span>{stop.name}</span>
          <span className="mt-1 block font-serif text-[15px] text-ink-2">{stop.question}</span>
        </Link>
        <Link href={next ? next.href : END.href} className={`${card} bg-ink text-background`}>
          <span className="eyebrow text-background/70">{next ? `Or skip ahead · stop ${next.n}` : "The end of the path"}</span>
          <span className="mt-2 block display text-xl">{next ? next.name : END.name} <span aria-hidden>→</span></span>
          <span className="mt-1 block font-serif text-[15px] text-background/80">{next ? next.question : END.short}</span>
        </Link>
      </nav>
    );
  }
  if (path === "/" || ["/ask", "/legal"].some((h) => under(path, h))) return null;
  return (
    <nav aria-label="Back to the path" className="mt-16">
      <Link href="/" className={`${card} max-w-3xl border border-grid bg-surface`}>
        <span className="eyebrow">You are in the evidence</span>
        <span className="mt-2 block display text-xl">Return to the path <span aria-hidden>→</span></span>
        <span className="mt-1 block font-serif text-[15px] text-ink-2">Three acts, nine stops, from the argument to the long run.</span>
      </Link>
    </nav>
  );
}
