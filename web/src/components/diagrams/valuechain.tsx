import Link from "next/link";
import type { Direction, OwnState } from "@/lib/data";

// The value-chain page's drawing parts. Everything arrives laid out by the export; nothing here works out a number.
// A judged direction is hatched in its own colour; the map's records are plain fills.
export const DIRECTION_FILL: Record<Direction, string> = { tightening: "var(--tight-3)", holding: "var(--s2)", commoditising: "var(--s3)" };
export const DIRECTION_WORD: Record<Direction, string> = { tightening: "Tightening", holding: "Holding", commoditising: "Commoditising" };
export const DIRECTION_ORDER: Direction[] = ["tightening", "holding", "commoditising"];

// One judged direction: a hatched square in the direction's colour.
export function JudgedMark({ d }: { d: Direction }) {
  return <span aria-hidden className="hatch inline-block h-3 w-3 shrink-0 ring-1 ring-inset ring-current" style={{ color: DIRECTION_FILL[d] }} />;
}

// A part of the chain the page has not judged: an empty dashed square.
export function UnjudgedMark() {
  return <span aria-hidden className="inline-block h-3 w-3 shrink-0 border border-dashed border-muted" />;
}

// A judged part of the chain, named and linked to its judgement.
export function JudgedPart({ d, name, title, href }: { d: Direction; name: string; title: string; href: string }) {
  return (
    <Link href={href} prefetch={false} title={`${DIRECTION_WORD[d]}, judged: ${title}`} className="flex items-start gap-1.5 text-[11.5px] leading-tight text-ink-2 hover:text-ink">
      <span className="mt-px flex"><JudgedMark d={d} /></span><span>{name}</span>
    </Link>
  );
}

export const OWN_FILL: Record<OwnState, string> = { independent: "var(--s3)", bought: "var(--s1)", closed: "var(--surface)" };
export const OWN_WORD: Record<OwnState, string> = { independent: "independent", bought: "bought, or being bought", closed: "closed" };

// A swatch for an ownership state, drawn as the bars draw it (closed is an empty outline).
export function OwnSwatch({ s }: { s: OwnState }) {
  return <span className="inline-block h-2.5 w-4" style={{ background: OWN_FILL[s], boxShadow: s === "closed" ? "inset 0 0 0 1px var(--ink-2)" : undefined }} />;
}

// One bar on a shared scale, split into segments, with its count printed at its end.
export function CountBar({ segs, end, count }: { segs: { key: string; x: number; w: number; fill: string; outline?: boolean; tip: string }[]; end: number; count: string }) {
  return (
    <div className="relative h-3.5 w-full pr-9">
      <div className="relative h-full w-full">
        {segs.map((s) => (
          <div key={s.key} title={s.tip} className="absolute inset-y-0" style={{ left: `${s.x}%`, width: `${s.w}%`, minWidth: s.w ? 3 : 0, background: s.fill, boxShadow: s.outline ? "inset 0 0 0 1px var(--ink-2)" : undefined }} />
        ))}
        <span className="absolute top-1/2 -translate-y-1/2 pl-1.5 font-mono text-[11px] leading-none text-ink-2" style={{ left: `${end}%` }}>{count}</span>
      </div>
    </div>
  );
}

// A part of a layer: filled when the map holds a company there, an empty ring when it holds none.
export function PartDot({ filled, tip }: { filled: boolean; tip: string }) {
  return <span title={tip} className={`inline-block h-[9px] w-[9px] rounded-full ${filled ? "bg-ink-2" : "ring-1 ring-inset ring-ink-2"}`} />;
}

// A profiled company placed by the site's own answers: a dashed outline, since the placing is a judgement.
export function JudgedChip({ name, word, tip }: { name: string; word?: string | null; tip: string }) {
  return (
    <span title={tip} className="inline-flex items-baseline gap-1 rounded-[2px] border border-dashed border-ink-2 px-1.5 py-0.5 text-[12px] leading-tight text-ink">
      {name}{word ? <span className="font-mono text-[10.5px] text-muted">{word}</span> : null}
    </span>
  );
}
