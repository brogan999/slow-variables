import Link from "next/link";

// Parts for the figures on /capture. Every position and width arrives from the export as a percentage, so nothing
// here works out a number.

const DOT: Record<string, string> = {
  concentrating: "bg-fast border-fast", dispersing: "bg-slow border-slow", stable: "bg-s1 border-s1",
  open: "bg-surface border-muted",
};

// One gauge: a square in the colour of the word it reads tonight, linked to its page.
export function GaugeDot({ word, href, tip }: { word: string; href?: string; tip?: string }) {
  const cls = `inline-block h-3.5 w-3.5 rounded-[2px] border-[1.5px] ${DOT[word] ?? DOT.open}`;
  return href ? <Link href={href} prefetch={false} title={tip} aria-label={tip} className={`${cls} hover:outline hover:outline-offset-1 hover:outline-ink`} /> : <span aria-hidden className={cls} />;
}

// A horizontal scale from nothing to the whole, with faint rules at the ticks; children are placed by `left`.
export function Track({ ticks, children, label }: { ticks?: { x: number }[]; children: React.ReactNode; label: string }) {
  return (
    <div role="img" aria-label={label} className="relative h-6 w-full">
      <span aria-hidden className="absolute inset-x-0 top-1/2 h-px bg-axis" />
      {ticks?.map((t) => <span key={t.x} aria-hidden className="absolute top-1 bottom-1 w-px bg-grid" style={{ left: `${t.x}%` }} />)}
      {children}
    </div>
  );
}

// A dot: solid for a reading, hollow for the earlier one; an estimate is hatched (a hatched ring when it is the earlier one).
export function Dot({ hollow = false, hatched = false }: { hollow?: boolean; hatched?: boolean }) {
  return (
    <span className={`relative inline-block rounded-full border-[1.5px] border-s1 text-s1 ${hatched ? "h-4 w-4 hatch bg-surface" : `h-3 w-3 ${hollow ? "bg-surface" : "bg-s1"}`}`}>
      {hatched && hollow ? <span className="absolute inset-[3px] rounded-full bg-surface" /> : null}
    </span>
  );
}

// A dot placed on a track.
export function TrackDot({ x, hollow = false, hatched = false, tip }: { x: number; hollow?: boolean; hatched?: boolean; tip: string }) {
  return <span title={tip} className="absolute top-1/2 flex -translate-x-1/2 -translate-y-1/2" style={{ left: `${x}%` }}><Dot hollow={hollow} hatched={hatched} /></span>;
}

// The part of a track an index cannot reach: a solid block from nothing to the floor, closed by a tick.
export function Unreachable({ x }: { x: number }) {
  return <span aria-hidden className="absolute inset-y-1 left-0 border-r-2 border-ink-2 bg-grid" style={{ width: `${x}%` }} />;
}

// One horizontal bar on a shared scale. The export flags a bar too thin to read, and the figure says so in words.
export function Bar({ w, fill, hatched = false, tip }: { w: number; fill: string; hatched?: boolean; tip: string }) {
  return <div title={tip} className={`h-3.5 ${hatched ? "hatch" : ""}`} style={{ width: `${w}%`, background: hatched ? undefined : fill, color: fill, boxShadow: hatched ? `inset 0 0 0 1px ${fill}` : undefined }} />;
}

// Bands between two columns of nodes, drawn in a square of percentages stretched to the box.
export function Flow({ bands, left, right, label }: {
  bands: { key: string; d: string; fill: string; tip: string; broken?: boolean }[]; left: { id: string; y: number; h: number }[]; right: { id: string; y: number; h: number }[]; label: string;
}) {
  return (
    <svg viewBox="0 0 100 100" preserveAspectRatio="none" role="img" aria-label={label} className="absolute inset-0 h-full w-full">
      {bands.map((b) => b.broken
        ? <path key={b.key} d={b.d} fill={b.fill} fillOpacity="0.45" stroke={b.fill} strokeWidth="2" strokeDasharray="6 4" vectorEffect="non-scaling-stroke"><title>{b.tip}</title></path>
        : <path key={b.key} d={b.d} fill={b.fill} fillOpacity="0.72" stroke="var(--surface)" strokeWidth="0.5" vectorEffect="non-scaling-stroke"><title>{b.tip}</title></path>)}
      {left.map((n) => <rect key={n.id} x="0" y={n.y} width="1.6" height={n.h} fill="var(--s1)" />)}
      {right.map((n) => <rect key={n.id} x="98.4" y={n.y} width="1.6" height={n.h} fill="var(--s1)" />)}
    </svg>
  );
}
