import Link from "next/link";
import type { GaugeDot, GaugeGroup, StageStrip, StripDot, Tick } from "@/lib/data";

// Parts for the /diffusion figures. Every place (x, y, a row's height) arrives from the export, so nothing here works
// out a number. One mark means one gauge everywhere on the page: its shape says what it reads, so no meaning rides on
// colour alone, and an outline says the gauge is scored but casts no vote of its own.
export const GROUP_WORDS: Record<GaugeGroup, string> = {
  fast: "reads fast", normal: "reads normal", slow: "reads slow", unscored: "too early to score", other: "reads who keeps the money, not speed",
};
const HUE: Record<GaugeGroup, string> = { fast: "var(--fast)", normal: "var(--ink)", slow: "var(--slow)", unscored: "var(--muted)", other: "var(--muted)" };

export function Glyph({ group, votes = true, size = 14 }: { group: GaugeGroup; votes?: boolean; size?: number }) {
  const hue = HUE[group];
  const fill = votes ? hue : "var(--surface)";
  return (
    <svg width={size} height={size} viewBox="0 0 14 14" aria-hidden>
      {group === "fast" ? <path d="M7 1.5 L12.8 12 H1.2 Z" fill={fill} stroke={hue} strokeWidth="1.5" strokeLinejoin="round" /> : null}
      {group === "slow" ? <path d="M7 12.5 L12.8 2 H1.2 Z" fill={fill} stroke={hue} strokeWidth="1.5" strokeLinejoin="round" /> : null}
      {group === "normal" ? <circle cx="7" cy="7" r="5.2" fill={fill} stroke={hue} strokeWidth="1.5" /> : null}
      {group === "unscored" ? <><circle cx="7" cy="7" r="5.2" fill="var(--surface)" stroke={hue} strokeWidth="1.5" /><path d="M7 1.8 A5.2 5.2 0 0 0 7 12.2 Z" fill={hue} /></> : null}
      {group === "other" ? <rect x="2.5" y="2.5" width="9" height="9" fill="var(--surface)" stroke={hue} strokeWidth="1.5" strokeDasharray="2 1.5" /> : null}
    </svg>
  );
}

// One gauge as a link to its page. `box` draws a frame round it (a solid frame, a dotted one), for a second fact.
export function GaugeLink({ d, tip, stop = false, box, style, className = "" }: { d: GaugeDot; tip: string; stop?: boolean; box?: "solid" | "dotted"; style?: React.CSSProperties; className?: string }) {
  return (
    <Link href={d.href} prefetch={false} data-tip={tip} aria-label={tip} title={tip} data-stop={stop || undefined} className={`mark ${className}`} style={style}>
      <span className={`flex rounded-[2px] ${box === "solid" ? "p-0.5 ring-1 ring-ink" : box === "dotted" ? "p-0.5 outline-dotted outline-1 outline-muted" : ""}`}><Glyph group={d.group} votes={d.votes || d.group === "unscored" || d.group === "other"} /></span>
    </Link>
  );
}

export type Zone = { key: string; x: number; w: number; label?: string; tint: string };

// One strip per stage on a shared scale: marks stacked where they would collide, shaded zones behind them, tick
// labels beneath. `side` is the small line under a stage's name; `extra` draws anything more on a strip.
export function Strips<D extends StripDot, R extends StageStrip<D>>({ rows, zones = [], ticks = [], label, tip, side, extra, box }: {
  rows: R[]; zones?: Zone[]; ticks?: Tick[]; label: string; tip: (d: R["dots"][number]) => string;
  side?: (row: R) => React.ReactNode; extra?: (row: R) => React.ReactNode; box?: (d: R["dots"][number]) => "solid" | "dotted" | undefined;
}) {
  const grid = "grid grid-cols-1 gap-1 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-3";
  const edge = (i: number, n: number) => (i === 0 ? "" : i === n - 1 ? "-translate-x-full" : "-translate-x-1/2");
  return (
    <div role="group" aria-label={label} className="flex flex-col gap-4">
      {zones.some((z) => z.label) ? (
        <div className={grid} aria-hidden>
          <div className="max-sm:hidden" />
          <div className="relative mx-3 h-4 font-mono text-[11px] text-muted">
            {zones.map((z) => <span key={z.key} className="absolute top-0 overflow-hidden text-center whitespace-nowrap" style={{ left: `${z.x}%`, width: `${z.w}%` }}>{z.label}</span>)}
          </div>
        </div>
      ) : null}
      {rows.map((r) => (
        <div key={r.stage} className={`${grid} sm:items-end`}>
          <div className="text-[13px] leading-tight text-ink">{r.order}. {r.name}{side ? <span className="mt-0.5 block font-mono text-[11px] leading-snug text-muted">{side(r)}</span> : null}</div>
          <div className="relative mx-3 border-b border-axis" style={{ height: `${r.h}px` }} data-marks>
            {zones.map((z) => <div key={z.key} aria-hidden className="absolute inset-y-0" style={{ left: `${z.x}%`, width: `${z.w}%`, background: z.tint, boxShadow: "inset -1px 0 0 var(--surface)" }} />)}
            {ticks.map((t) => <div key={t.label} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.x}%` }} />)}
            {extra ? extra(r) : null}
            {r.dots.map((d, i) => <GaugeLink key={d.id} d={d} tip={tip(d)} stop={i === 0} box={box ? box(d) : undefined} className="absolute -translate-x-1/2 -translate-y-1/2" style={{ left: `${d.x}%`, top: `${d.y}%` }} />)}
          </div>
        </div>
      ))}
      {ticks.length ? (
        <div className={grid} aria-hidden>
          <div className="max-sm:hidden" />
          <div className="relative mx-3 -mt-3 h-4 font-mono text-[11px] text-muted">
            {ticks.map((t, i) => <span key={t.label} className={`absolute top-0 whitespace-nowrap ${edge(i, ticks.length)} ${t.minor ? "max-sm:hidden" : ""}`} style={{ left: `${t.x}%` }}>{t.label}</span>)}
          </div>
        </div>
      ) : null}
    </div>
  );
}

// A line swatch for a key strip.
export const LineSwatch = ({ dashed = false }: { dashed?: boolean }) => (
  <svg width="18" height="10" aria-hidden><line x1="0" x2="18" y1="5" y2="5" stroke={dashed ? "var(--axis)" : "var(--s2)"} strokeWidth="2" strokeDasharray={dashed ? "4 3" : undefined} /></svg>
);
