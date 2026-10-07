import type { CSSProperties, ReactNode } from "react";
import type { OutlookLook, OutlookReach, OutlookSettleMark } from "@/lib/data";

type Drawn = OutlookLook | OutlookReach | OutlookSettleMark;

// The outlook's drawing parts. Like the kit, they take everything counted and laid out by the export.
// One fill per reading, the predictions board's: dark for a reading against a line, orange for a failed test, grey for
// a reading both sides expect, hollow where nothing has been read (with a centre dot when a test is written and waiting).
// A dispute's dark mark is ringed when the claim that held also carries a test of what the rival expects.
const LINE = "inset 0 0 0 1px var(--muted)";
const DOT = `linear-gradient(var(--muted) 0 0) center / 6px 6px no-repeat, var(--surface)`;
export const LOOK_STYLE: Record<Drawn, CSSProperties> = {
  holding: { background: "var(--s1)" }, read: { background: "var(--s1)" }, held: { background: "var(--s1)" },
  told_apart: { background: "var(--s1)", boxShadow: "inset 0 0 0 2px var(--s1), inset 0 0 0 3.5px var(--surface)" },
  failing: { background: "var(--tight-3)" }, missed: { background: "var(--tight-3)" },
  both: { background: "var(--s3)" }, shared: { background: "var(--s3)" },
  waiting: { background: DOT, boxShadow: LINE },
  no_test: { background: "var(--surface)", boxShadow: LINE },
};
// A hollow part of a bar: the surface with a muted line round it.
const EDGE = "linear-gradient(var(--muted) 0 0)";
export const HOLLOW = `${EDGE} top / 100% 1px no-repeat, ${EDGE} bottom / 100% 1px no-repeat, ${EDGE} left / 1px 100% no-repeat, ${EDGE} right / 1px 100% no-repeat, var(--surface)`;

// A mark for a key strip, drawn as the figures draw it. `round` is a date the rival's reading runs out.
export function LookSwatch({ look, round = false }: { look: Drawn; round?: boolean }) {
  return <span className={`inline-block h-3 w-3 ${round ? "rounded-full" : ""}`} style={LOOK_STYLE[look]} />;
}

// One mark for one claim or one dispute, linked to its record on this page. The link is padded so a finger can hit it.
export function LookMark({ look, href, tip, round = false }: { look: Drawn; href: string; tip: string; round?: boolean }) {
  return (
    <a href={href} title={tip} aria-label={tip} className="block p-1 hover:opacity-70">
      <span className={`block h-4 w-4 ${round ? "rounded-full" : ""}`} style={LOOK_STYLE[look]} />
    </a>
  );
}

// Rows of marks under one name each; `tail` is what the row counts in type.
export function LookRows({ rows, label }: { rows: { key: string; name: ReactNode; marks: ReactNode; tail?: ReactNode }[]; label: string }) {
  return (
    <div role="group" aria-label={label} className="flex flex-col">
      {rows.map((r) => (
        <div key={r.key} className="grid grid-cols-1 gap-x-3 gap-y-1 border-b border-grid py-2 first:pt-0 last:border-0 last:pb-0 sm:grid-cols-[17rem_1fr] sm:items-center">
          <div className="text-[13px] leading-tight text-ink">{r.name}</div>
          <div className="-m-1 flex flex-wrap items-center">{r.marks}{r.tail ? <span className="ml-2 p-1 font-mono text-[11px] text-muted">{r.tail}</span> : null}</div>
        </div>
      ))}
    </div>
  );
}

// A question asked of a claim, and where the claim stops if the answer sends it out. `out` is the answer that leaves.
export function Gate({ ask, why, out, children }: { ask: string; why?: string; out: string; children: ReactNode }) {
  return (
    <li className="grid gap-2 md:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] md:items-stretch md:gap-3">
      <div className="flex flex-col gap-1 border border-axis bg-surface-2 p-3">
        <span className="text-[14px] font-medium leading-snug text-ink">{ask}</span>
        {why ? <span className="text-[13px] leading-snug text-ink-2">{why}</span> : null}
      </div>
      <div className="flex items-stretch gap-2 max-md:pl-4">
        <span className="w-12 shrink-0 self-center whitespace-nowrap font-mono text-[11px] uppercase tracking-wider text-muted">{out} →</span>
        <div className="flex grow flex-col justify-center gap-1.5 border border-ink bg-surface p-3">{children}</div>
      </div>
    </li>
  );
}

// Where every claim starts, and where one that passes every gate ends: the width of a gate's question.
export function Ends({ children, out = false }: { children: ReactNode; out?: boolean }) {
  return (
    <li className="grid md:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] md:gap-3">
      <div className={`flex flex-wrap items-baseline gap-x-3 gap-y-1 border p-3 ${out ? "border-ink bg-surface" : "border-axis bg-surface-2"}`}>{children}</div>
    </li>
  );
}

// The step between two gates: the answer that carries the claim on.
export function Onward({ word }: { word: string }) {
  return <li className="font-mono text-[11px] uppercase tracking-wider text-muted md:pl-6">↓ {word}</li>;
}
