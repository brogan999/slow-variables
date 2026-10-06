import type { ChainLink } from "@/lib/data";

// Parts for the migration essay's figures. Every height, place and count arrives laid out by the export
// (src/ai_tracker/migration_figures.py); nothing here works out a number.

// the tightness words on the one-hue ramp, slack lightest: the same colours as the scorecard
export const TONE: Record<string, string> = { slack: "var(--tight-1)", easing: "var(--tight-2)", moderate: "var(--tight-3)", tight: "var(--tight-4)", severe: "var(--tight-5)" };

// Inputs as posts of different heights, with a line at the height of the shortest: the pace. What stands above the
// line is spare. A model: the heights are words on a fixed scale from the seed, never readings.
export function Staves({ links, level, label }: { links: ChainLink[]; level: number; label: string }) {
  return (
    <div role="img" aria-label={label}>
      <div className="relative h-40 border-b border-ink">
        <div className="absolute inset-0 flex items-end gap-1">
          {links.map((x) => (
            <div key={x.id} className="relative h-full flex-1">
              <div className="absolute inset-x-0 bottom-0 bg-surface-2 ring-1 ring-inset ring-grid" style={{ height: `${x.h}%` }} />
              <div className={`absolute inset-x-0 bottom-0 ${x.shortest ? "bg-tight-5" : "bg-s3"}`} style={{ height: `${level}%` }} />
              {x.was !== null ? <div className="absolute inset-x-0 border-t-2 border-dotted border-tight-5" style={{ bottom: `${x.was}%` }} /> : null}
              {x.shortest ? <div className="absolute inset-x-0 pb-1 text-center font-mono text-[10px] uppercase tracking-[0.08em] text-tight-5" style={{ bottom: `${x.h}%` }}>rent</div> : null}
            </div>
          ))}
        </div>
        <div className="absolute inset-x-0 border-t border-dashed border-ink" style={{ bottom: `${level}%` }} />
        <div className="absolute right-0 pb-0.5 font-mono text-[10px] uppercase tracking-[0.08em] text-ink bg-surface/80 px-1" style={{ bottom: `${level}%` }}>the pace</div>
      </div>
      <div className="mt-1 flex gap-1" aria-hidden>
        {links.map((x) => <div key={x.id} className={`flex-1 min-w-0 flex justify-center whitespace-nowrap font-sans text-[10px] leading-tight ${x.shortest ? "font-semibold text-ink" : "text-ink-2"}`}>{x.label}</div>)}
      </div>
    </div>
  );
}

// A round mark for a key or a row: solid, hatched (low confidence) or hollow (no score).
export function Dot({ fill, hatched = false, hollow = false, small = false }: { fill?: string; hatched?: boolean; hollow?: boolean; small?: boolean }) {
  const size = small ? "h-2.5 w-2.5" : "h-3 w-3";
  if (hollow) return <span aria-hidden className={`inline-block ${size} rounded-full bg-surface ring-1 ring-inset ring-ink-2`} />;
  return <span aria-hidden className={`inline-block ${size} rounded-full ${hatched ? "hatch" : ""}`} style={{ background: hatched ? undefined : fill, color: fill, boxShadow: hatched ? "inset 0 0 0 1px currentColor" : undefined }} />;
}

// One scale, end to end, with a faint line where each word begins.
export function Track({ lines, children, tall = false }: { lines: number[]; children: React.ReactNode; tall?: boolean }) {
  return (
    <div className={`relative ${tall ? "h-6" : "h-4"} w-full`}>
      <div className="absolute inset-x-0 top-1/2 h-px bg-grid" aria-hidden />
      {lines.map((x) => <div key={x} className="absolute inset-y-0 w-px bg-grid" style={{ left: `${x}%` }} aria-hidden />)}
      {children}
    </div>
  );
}
