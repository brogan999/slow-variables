import Link from "next/link";
import type { MapClaimMark, MapUnit, OutlookState } from "@/lib/data";

// Parts for the figures on /bottlenecks. Everything arrives counted and placed by the export; nothing here works out
// a number. One square is one row of the map or one barrier, so a count can be checked by eye.

// How a row is drawn when the map is counted: a scored input keeps the scorecard's ramp, an input with no score is
// an open square (as on the map), and a friction outside the chain, read on another scale, has its own grey.
export const ROW_FILL: Record<string, { fill: string; open?: boolean; label: string }> = {
  tight: { fill: "var(--tight-5)", label: "an input scored tight or severe" },
  moderate: { fill: "var(--tight-3)", label: "an input scored moderate" },
  easing: { fill: "var(--tight-1)", label: "an input scored easing or slack" },
  unscored: { fill: "var(--s1)", open: true, label: "an input with no score" },
  friction: { fill: "var(--s3)", label: "a friction outside the chain, read by indicators on their own scale" },
  friction_unread: { fill: "var(--s3)", open: true, label: "a friction nothing reads" },
};

// What is known of one barrier: an indicator reads it (a plain fill), or a model judged it in words (hatched, in a
// weight of ink for the word and never on the tightness ramp, which is kept for measured scores), or neither (open).
// The two darker inks cannot be told apart in thin lines, so the words step dark, light, and light with no outline.
export const BARRIER_FILL: Record<string, { fill: string; hatched?: boolean; open?: boolean; bare?: boolean }> = {
  read: { fill: "var(--s1)" },
  still_binds: { fill: "var(--s1)", hatched: true },
  easing: { fill: "var(--s3)", hatched: true },
  largely_lifted: { fill: "var(--s3)", hatched: true, bare: true },
  blank: { fill: "var(--s3)", open: true },
};

export function Square({ fill, open = false, hatched = false, bare = false }: { fill: string; open?: boolean; hatched?: boolean; bare?: boolean }) {
  return <span aria-hidden className={`inline-block h-3 w-3 shrink-0 ${hatched ? "hatch" : ""} ${(open || hatched) && !bare ? "ring-[1.5px] ring-inset ring-current" : ""}`} style={{ color: fill, background: open ? "var(--surface)" : hatched ? undefined : fill }} />;
}

// A row of squares under a name, with the count the export made at its end.
export function UnitRow({ name, sub, total, children }: { name: React.ReactNode; sub?: React.ReactNode; total: number; children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-1 sm:grid-cols-[14rem_1fr] sm:items-center sm:gap-3">
      <div className="text-[13px] leading-tight text-ink">{name}{sub ? <span className="block text-[11px] text-muted">{sub}</span> : null}</div>
      <div className="flex flex-wrap items-center gap-[3px]">{children}<span className="num ml-1.5 text-[11px] text-muted">{total}</span></div>
    </div>
  );
}

// A score the scorecard marks as low in confidence is hatched in its own colour, as it is there.
const LOW = ", low confidence";

export function RowSquares({ units }: { units: MapUnit[] }) {
  return <>{units.map((u) => <a key={u.id} href={u.href} title={`${u.name}: ${ROW_FILL[u.cls].label}${u.low ? LOW : ""}`} className="flex hover:opacity-70"><Square {...ROW_FILL[u.cls]} hatched={u.low} /><span className="sr-only">{u.name}: {ROW_FILL[u.cls].label}{u.low ? LOW : ""}</span></a>)}</>;
}

// The same glyphs the outlook page prints beside a claim's state.
export const STATE_GLYPH: Record<OutlookState, string> = { holding: "●", failing: "×", both: "◑", untestable: "○" };

export function ClaimMark({ m, state, words }: { m: MapClaimMark; state: OutlookState; words: string }) {
  return (
    <Link href={m.href} prefetch={false} title={`${m.who}: ${m.text} (${words})`}
      className={`inline-flex h-5 w-5 items-center justify-center text-[15px] leading-none hover:bg-surface-2 ${state === "untestable" ? "text-muted" : "text-ink"} ${m.site ? "ring-1 ring-inset ring-axis" : ""}`}>
      <span aria-hidden>{STATE_GLYPH[state]}</span><span className="sr-only">{m.who}: {words}</span>
    </Link>
  );
}

// The arrow between two stages of the path: rightward on a wide screen, downward on a phone.
export function Flow() {
  return <span aria-hidden className="flex items-center justify-center font-mono text-lg leading-none text-muted"><span className="max-md:hidden">→</span><span className="md:hidden">↓</span></span>;
}
