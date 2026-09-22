import Link from "next/link";
import type { Point, Tick } from "@/lib/data";

// Everything a chart draws arrives laid out by the export as percentages from the plot's top left, so this file only
// places it. Axis labels are HTML beside the SVG, so text keeps its real size at every width and one drawing serves
// phone and desktop.
export function Plot({ x, y, label, children, tall = false }: {
  x: Tick[]; y: { ticks: Tick[]; unit: string | null; chars: number }; label: string; children: React.ReactNode; tall?: boolean;
}) {
  return (
    <div className="plot" style={{ "--ychars": y.chars } as React.CSSProperties}>
      {y.unit ? <div className="plot-unit">{y.unit}</div> : null}
      <div className="plot-y" aria-hidden>
        {y.ticks.map((t) => <span key={t.y} style={{ top: `${t.y}%` }}>{t.label}</span>)}
      </div>
      <div className={`plot-area ${tall ? "h-72 md:h-96" : "h-56 md:h-72"}`}>
        <svg className="absolute inset-0 h-full w-full overflow-visible" role="group" aria-label={label}>
          {y.ticks.map((t) => <line key={t.y} x1="0" x2="100%" y1={`${t.y}%`} y2={`${t.y}%`} stroke="var(--grid)" />)}
          {children}
        </svg>
      </div>
      <div className="plot-x" aria-hidden>
        {x.map((t) => <span key={t.x} style={{ left: `${t.x}%` }} className={t.minor ? "max-sm:hidden" : undefined}>{t.label}</span>)}
      </div>
    </div>
  );
}

// A group of marks is one tab stop (the mark passed `stop`); arrows walk the rest (HoverLayer) and Enter follows.
export function Marks({ children }: { children: React.ReactNode }) {
  return <g data-marks>{children}</g>;
}

// One reading: a dot inside a hit target three times its size, linked to its record. `tip` is what the hover layer
// shows and what a screen reader hears. Every mark ships focusable with a <title>, so with JavaScript off each is
// reachable and shows its tip; HoverLayer then makes the group one tab stop (at `stop`) and draws its own tip.
export function Mark({ p, tip, stop, hollow = false, dashed = false, faint = false }: { p: Point; tip: string; stop: boolean; hollow?: boolean; dashed?: boolean; faint?: boolean }) {
  const body = (
    <>
      <circle cx={`${p.x}%`} cy={`${p.y}%`} r="12" fill="transparent" />
      <circle cx={`${p.x}%`} cy={`${p.y}%`} r="4" fill={hollow || dashed ? "var(--surface)" : "var(--s1)"} stroke="var(--s1)" strokeWidth="1.5" strokeDasharray={dashed ? "2 1.5" : undefined} opacity={faint ? 0.35 : 1} />
    </>
  );
  const common = { "data-tip": tip, "aria-label": tip, "data-stop": stop || undefined, tabIndex: 0, className: "mark" };
  const inner = <><title>{tip}</title>{body}</>;
  // an in-page anchor stays a plain link, so the browser's own fragment navigation (and HoverLayer's reveal) runs
  return !p.href ? <g role="img" {...common}>{inner}</g> : p.href.startsWith("#") ? <a href={p.href} {...common}>{inner}</a> : <Link href={p.href} prefetch={false} {...common}>{inner}</Link>;
}
