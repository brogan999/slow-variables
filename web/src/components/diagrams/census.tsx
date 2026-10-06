// Diagram parts for the census page. As in the kit, every width and position arrives from the export as a percentage,
// so nothing here works out a number.

type ScaleTick = { left: number; label: string };
const GRID = "grid grid-cols-1 gap-x-3 gap-y-1 md:grid-cols-[var(--namew)_minmax(0,1fr)_var(--valuew)] md:items-center";

// Tick labels under a scale: the first and last sit inside its ends, so nothing runs off a phone.
function Scale({ ticks }: { ticks: ScaleTick[] }) {
  return (
    <div className={GRID} aria-hidden>
      <div className="relative h-4 md:col-start-2">
        {ticks.map((t) => (
          <span key={t.label} className={`absolute top-0 font-mono text-[11px] leading-none text-muted ${t.left === 0 ? "" : t.left === 100 ? "-translate-x-full" : "-translate-x-1/2"}`} style={{ left: `${t.left}%` }}>{t.label}</span>
        ))}
      </div>
    </div>
  );
}

function Rules({ ticks }: { ticks: ScaleTick[] }) {
  return <>{ticks.map((t) => <span key={t.label} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: `${t.left}%` }} />)}</>;
}

export type ScaleRow = { key: string; name: React.ReactNode; w: number; tick?: number | null; tickTip?: string; value: React.ReactNode; tip: string; strong?: boolean; fill?: string; title?: string };

// Rows of bars on one scale from zero: a name, the bar, and its value in type. `tick` cuts the bar where a firmer
// part of it ends (to its left, all three models pass).
export function ScaleBars({ rows, ticks, label, nameWidth = "15rem", valueWidth = "10.5rem" }: { rows: ScaleRow[]; ticks?: ScaleTick[]; label: string; nameWidth?: string; valueWidth?: string }) {
  return (
    <div role="group" aria-label={label} className="flex flex-col gap-3 md:gap-2.5" style={{ "--namew": nameWidth, "--valuew": valueWidth } as React.CSSProperties}>
      {rows.map((r) => (
        <div key={r.key} className={GRID} title={r.title}>
          <div className={`text-[13px] leading-snug ${r.strong ? "font-semibold text-ink" : "text-ink-2"}`}>{r.name}</div>
          <div className="relative h-4 bg-surface-2">
            {ticks ? <Rules ticks={ticks} /> : null}
            <div title={r.tip} className="absolute inset-y-0 left-0" style={{ width: `${r.w}%`, background: r.fill ?? "var(--s1)" }} />
            {r.tick != null ? <div title={r.tickTip} className="absolute -inset-y-0.5 w-0.5 bg-surface" style={{ left: `${r.tick}%` }} /> : null}
          </div>
          <div className="font-mono text-[11.5px] leading-snug text-ink-2 tabular-nums">{r.value}</div>
        </div>
      ))}
      {ticks ? <Scale ticks={ticks} /> : null}
    </div>
  );
}

// The three ways a dot is drawn, so three judges read apart without a hue.
const DOT = ["rounded-full bg-ink", "rounded-full border-2 border-ink bg-surface", "rotate-45 scale-[0.8] bg-s3 outline outline-1 outline-ink"] as const;
export function Dot({ i }: { i: number }) {
  return <span className={`inline-block h-2.5 w-2.5 ${DOT[i] ?? DOT[0]}`} />;
}
export const VoteMark = () => <span className="inline-block h-4 w-[3px] bg-ink" />;
export const AllThreeMark = () => <span className="inline-block h-2 w-2 border-[1.5px] border-ink bg-surface" />;

export type DotRow = { key: string; name: string; strong?: boolean; title?: string; lo: number; spread: number; dots: { x: number; tip: string }[]; vote: { x: number; tip: string }; allThree: { x: number; tip: string } };

// One line per row on a shared scale: each judge's own reading as a dot, the span between them, the vote and the
// part all three pass as ticks.
export function DotRows({ rows, ticks, label }: { rows: DotRow[]; ticks: ScaleTick[]; label: string }) {
  return (
    <div role="group" aria-label={label} className="flex flex-col gap-2 md:gap-1" style={{ "--namew": "11rem", "--valuew": "0rem" } as React.CSSProperties}>
      {rows.map((r) => (
        <div key={r.key} className={GRID} title={r.title}>
          <div className={`text-[13px] leading-snug ${r.strong ? "font-semibold text-ink" : "text-ink-2"}`}>{r.name}</div>
          <div className="relative mx-1.5 h-5">
            <Rules ticks={ticks} />
            <span aria-hidden className="absolute top-1/2 h-px -translate-y-1/2 bg-ink-2" style={{ left: `${r.lo}%`, width: `${r.spread}%` }} />
            <span title={r.allThree.tip} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 leading-[0]" style={{ left: `${r.allThree.x}%` }}><AllThreeMark /></span>
            {r.dots.map((d, i) => <span key={i} title={d.tip} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 leading-[0]" style={{ left: `${d.x}%` }}><Dot i={i} /></span>)}
            <span title={r.vote.tip} className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 leading-[0]" style={{ left: `${r.vote.x}%` }}><VoteMark /></span>
          </div>
          <div className="max-md:hidden" />
        </div>
      ))}
      <div className={GRID} aria-hidden>
        <div className="relative mx-1.5 h-4 md:col-start-2">
          {ticks.map((t) => <span key={t.label} className="absolute top-0 -translate-x-1/2 font-mono text-[11px] leading-none text-muted" style={{ left: `${t.left}%` }}>{t.label}</span>)}
        </div>
      </div>
    </div>
  );
}

// A threshold drawn through a Plot: the export's points, in percent of the plot, as one dashed line.
export function PlotLine({ points }: { points: string }) {
  return (
    <svg x="0" y="0" width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden>
      <polyline points={points} fill="none" stroke="var(--ink-2)" strokeWidth="1.25" strokeDasharray="5 4" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
