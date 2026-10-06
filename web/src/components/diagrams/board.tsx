import Link from "next/link";
import type { Word } from "@/lib/data";

// The predictions board's drawing parts. Like the kit, they take everything counted and laid out by the export.
// One fill per status word. Too early is hollow: nothing has been read yet.
export const WORD_FILL: Record<Word, string> = {
  happening: "var(--s1)", not_happening: "var(--tight-3)", slower: "var(--slow)", both: "var(--s3)", too_early: "var(--surface)",
};
// A lean is a model's judgement, so every lean is hatched; the colour says which way.
export const LEAN_FILL: Record<string, string> = {
  likely_true: "var(--s1)", leans_true: "var(--s3)", toss_up: "var(--axis)", leans_false: "var(--tight-1)", likely_false: "var(--tight-3)",
};

const square = (word: Word) => ({ background: WORD_FILL[word], boxShadow: word === "too_early" ? "inset 0 0 0 1px var(--muted)" : undefined });

// One forecast's mark for a key strip, drawn as the figures draw it.
export function WordSwatch({ word }: { word: Word }) {
  return <span className="inline-block h-3 w-3" style={square(word)} />;
}

export type RowMark = { key: string; word: Word; tip: string; href: string; framed?: boolean };

// Rows of marks, one mark for one forecast, each linked to its record. `tail` is what the row counts but does not draw.
export function MarkRows({ rows, label, wide = false, columns = false }: { rows: { key: string; name: string; note?: React.ReactNode; marks: RowMark[]; tail?: React.ReactNode }[]; label: string; wide?: boolean; columns?: boolean }) {
  return (
    <div role="group" aria-label={label} className={columns ? "lg:columns-2 lg:gap-x-10" : "flex flex-col"}>
      {rows.map((r) => (
        <div key={r.key} className={`grid grid-cols-1 gap-x-3 gap-y-1 break-inside-avoid border-b border-grid py-2 sm:items-center ${columns ? "sm:grid-cols-[15rem_1fr]" : "last:border-0 last:pb-0 first:pt-0"} ${columns ? "" : wide ? "sm:grid-cols-[17rem_1fr]" : "sm:grid-cols-[8.5rem_1fr]"}`}>
          <div className="text-[13px] leading-tight text-ink">{r.name}{r.note ? <span className="ml-1.5 font-mono text-[11px] text-muted">{r.note}</span> : null}</div>
          <div className="flex flex-wrap items-center gap-1.5">
            {r.marks.map((m) => (
              <Link key={m.key} href={m.href} prefetch={false} title={m.tip} aria-label={m.tip} className={`block h-3.5 w-3.5 hover:opacity-70 ${m.framed ? "outline outline-1 outline-offset-2 outline-ink" : ""}`} style={square(m.word)} />
            ))}
            {r.tail ? <span className="ml-1 font-mono text-[11px] text-muted">{r.tail}</span> : null}
          </div>
        </div>
      ))}
    </div>
  );
}

export type LeanSeg = { key: string; x: number; w: number; tip: string };

// Rows of bars set either side of a centre line: one way to its left, the other to its right. Always hatched,
// because what it draws is a judgement. `left` and `right` are the counts on each side, printed at the bar's ends.
export function LeanSplit({ rows, centre, label, ends }: { rows: { key: string; name: string; note?: React.ReactNode; segs: LeanSeg[]; left: React.ReactNode; right: React.ReactNode }[]; centre: number; label: string; ends: [string, string] }) {
  return (
    <div role="group" aria-label={label} className="flex flex-col gap-3">
      <div aria-hidden className="grid grid-cols-1 sm:grid-cols-[13rem_1fr] sm:gap-3"><span className="max-sm:hidden" /><span className="flex justify-between font-mono text-[11px] text-muted"><span>← {ends[0]}</span><span>{ends[1]} →</span></span></div>
      {rows.map((r) => (
        <div key={r.key} className="grid grid-cols-1 gap-1 sm:grid-cols-[13rem_1fr] sm:items-center sm:gap-3">
          <div className="text-[13px] leading-tight text-ink">{r.name}{r.note ? <span className="ml-1.5 font-mono text-[11px] text-muted">{r.note}</span> : null}</div>
          <div className="grid grid-cols-[1.75rem_1fr_1.75rem] items-center gap-1.5">
            <span className="num text-right text-[11px] text-ink-2">{r.left}</span>
            <div className="relative h-5 w-full">
              {r.segs.map((s) => (
                <div key={s.key} title={s.tip} className="hatch absolute inset-y-0" style={{ left: `${s.x}%`, width: `${s.w}%`, color: LEAN_FILL[s.key], boxShadow: "inset 0 0 0 1px currentColor" }} />
              ))}
              <span aria-hidden className="absolute -inset-y-1 w-px bg-ink" style={{ left: `${centre}%` }} />
            </div>
            <span className="num text-[11px] text-ink-2">{r.right}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
