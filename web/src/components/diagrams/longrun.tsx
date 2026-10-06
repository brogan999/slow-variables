import type { OutlookState } from "@/lib/data";

// The long-run page's drawing parts. Like the kit, they take every position from the export as a percentage, so
// nothing here works out a number. Data keeps the site's ordinary palette; the page's gilt is ornament only.

// How each milestone's mark is drawn where forecasts of several share one plot: told apart by fill, not by hue.
export const LANE_MARK: Record<string, { hollow?: boolean; dashed?: boolean; fill?: string }> = {
  agi: {}, superintelligence: { fill: "var(--s3)" }, automated_researcher: { hollow: true }, superhuman_coder: { dashed: true },
};

// A milestone's mark for a key strip, drawn as the plot draws it.
const LANE_KEY: Record<string, string> = {
  agi: "bg-s1", superintelligence: "bg-s3", automated_researcher: "bg-surface", superhuman_coder: "bg-surface border-dashed",
};
export function LaneDot({ lane }: { lane: string }) {
  return <span className={`inline-block h-2.5 w-2.5 rounded-full border-[1.5px] border-s1 ${LANE_KEY[lane] ?? "bg-s1"}`} />;
}

// One colour for each world: the fast story and the slow one take the site's colours for fast and slow, a stall
// takes the bottleneck orange, and loss of control the ink.
export const WORLD_FILL: Record<string, string> = {
  managed_explosion: "var(--fast)", long_diffusion: "var(--slow)", loss_of_control: "var(--s1)", brake: "var(--tight-3)",
};
// The outlook page's glyph for each state a claim can read.
export const STATE_GLYPH: Record<OutlookState, string> = { holding: "●", failing: "×", both: "◑", untestable: "○" };

export type YearTick = { year: number; x: number };

// One row's strip on a scale of years: a rule at each tick, and the years still to come shaded as the timeline shades them.
export function YearTrack({ ticks, today, breaks = [], className = "h-6", children }: { ticks: YearTick[]; today?: number; breaks?: number[]; className?: string; children: React.ReactNode }) {
  return (
    <div className={`relative ${className}`}>
      {ticks.map((t) => <span key={t.year} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.x}%` }} />)}
      {breaks.map((b) => <span key={b} aria-hidden className="absolute inset-y-0 border-l border-dashed border-axis" style={{ left: `${b}%` }} />)}
      {today !== undefined ? <span aria-hidden className="absolute inset-y-0 right-0 bg-surface-2/60" style={{ left: `${today}%` }} /> : null}
      {children}
    </div>
  );
}

// The years under a strip. `hide` names the ticks a phone has no room for.
export function YearScale({ ticks, hide = [] }: { ticks: YearTick[]; hide?: number[] }) {
  return (
    <div className="relative h-4" aria-hidden>
      {ticks.map((t) => <span key={t.year} className={`absolute top-0.5 -translate-x-1/2 font-mono text-[10px] leading-none text-muted ${hide.includes(t.year) ? "max-sm:hidden" : ""}`} style={{ left: `${t.x}%` }}>{t.year}</span>)}
    </div>
  );
}
