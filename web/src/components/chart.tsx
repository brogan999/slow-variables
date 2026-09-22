import Link from "next/link";
import type { Point, Tick } from "@/lib/data";

// Everything a chart draws arrives laid out by the export as percentages from the plot's top left, so this file only
// places it. Axis labels are HTML beside the SVG, so text keeps its real size at every width and one drawing serves
// phone and desktop. `right` holds labels beside the plot's right edge, placed by their own `top` percentages.
export function Plot({ x, y, label, children, tall = false, right, rightWidth = "8.5rem", keepRight = false }: {
  x: Tick[]; y: { ticks: Tick[]; unit: string | null; chars: number }; label: string; children: React.ReactNode; tall?: boolean;
  right?: React.ReactNode; rightWidth?: string; keepRight?: boolean;
}) {
  return (
    <div className={`plot${right ? " plot-r" : ""}${keepRight ? " plot-keep" : ""}`} style={{ "--ychars": y.chars, "--rightw": rightWidth } as React.CSSProperties}>
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
      {right ? <div className="plot-right" aria-hidden>{right}</div> : null}
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
export function Mark({ p, tip, stop, hollow = false, dashed = false, faint = false, r = 4, stroke = "var(--s1)", fill }: {
  p: Pick<Point, "x" | "y" | "href">; tip: string; stop: boolean; hollow?: boolean; dashed?: boolean; faint?: boolean; r?: number; stroke?: string; fill?: string;
}) {
  const body = (
    <>
      <circle cx={`${p.x}%`} cy={`${p.y}%`} r={Math.max(12, r * 3)} fill="transparent" />
      <circle cx={`${p.x}%`} cy={`${p.y}%`} r={r} fill={hollow || dashed ? "var(--surface)" : (fill ?? stroke)} stroke={stroke} strokeWidth="1.5" strokeDasharray={dashed ? "2 1.5" : undefined} opacity={faint ? 0.35 : 1} />
    </>
  );
  return <Linked href={p.href} tip={tip} stop={stop}>{body}</Linked>;
}

// One segment of a stacked column, with a surface-coloured edge so neighbours read as separate fills.
export function RectMark({ x, y, width, height, fill, href, tip, stop, edge = 2 }: {
  x: number; y: number; width: number; height: number; fill: string; href: string | null; tip: string; stop: boolean; edge?: number;
}) {
  return (
    <Linked href={href} tip={tip} stop={stop}>
      <rect x={`${x}%`} y={`${y}%`} width={`${width}%`} height={`${height}%`} fill={fill} stroke="var(--surface)" strokeWidth={edge} />
    </Linked>
  );
}

function Linked({ href, tip, stop, children }: { href?: string | null; tip: string; stop: boolean; children: React.ReactNode }) {
  const common = { "data-tip": tip, "aria-label": tip, "data-stop": stop || undefined, tabIndex: 0, className: "mark" };
  const inner = <><title>{tip}</title>{children}</>;
  // an in-page anchor stays a plain link, so the browser's own fragment navigation (and HoverLayer's reveal) runs
  return !href ? <g role="img" {...common}>{inner}</g> : href.startsWith("#") ? <a href={href} {...common}>{inner}</a> : <Link href={href} prefetch={false} {...common}>{inner}</Link>;
}

// Hatching means an estimate or a projection, in the colour of the thing hatched. Mounted once in the layout, so
// any chart can fill with url(#hatch-s1).
export function HatchDefs() {
  return (
    <svg width="0" height="0" className="absolute" aria-hidden focusable="false">
      <defs>
        <pattern id="hatch-s1" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="5" height="5" fill="var(--surface)" />
          <rect width="1.6" height="5" fill="var(--s1)" />
        </pattern>
      </defs>
    </svg>
  );
}
