import Link from "next/link";
import type { Doc, Point } from "@/lib/data";
import { fmt, words } from "@/lib/format";
import { ChartSources } from "./ChartSources";
import { Figure, Key } from "./Figure";
import { Mark, Marks, Plot } from "./chart";

const who = (p: Point) => (p.subject ?? Object.values(p.dims ?? {}).join(" ")).replace(/_/g, " ");
const range = (p: Point, unit: string) => (p.low != null && p.high != null ? ` (${fmt(p.low, unit)}–${fmt(p.high, unit)})` : "");
const tip = (p: Point, unit: string) =>
  [who(p), fmt(p.value, unit) + range(p, unit), p.as_of, p.stamp, p.disputed ? "disputed" : null].filter(Boolean).join(" · ");

const Dot = ({ hollow = false, faint = false }) => (
  <svg width="10" height="10" aria-hidden><circle cx="5" cy="5" r="3.5" fill={hollow ? "var(--surface)" : "var(--s1)"} stroke="var(--s1)" strokeWidth="1.5" opacity={faint ? 0.35 : 1} /></svg>
);
const Swatch = ({ className }: { className: string }) => <span aria-hidden className={`inline-block h-2.5 w-4 ${className}`} />;

// An indicator's readings over time. Band indicators show the normal and fast ranges when the rule reads the drawn
// series; direction indicators show the rule's window, its dead band and the change across it.
export function TimeChart({ d }: { d: Doc }) {
  const c = d.chart;
  if (!c) return <p className="text-sm text-muted">No approved observations yet.</p>;
  const pts = d.points.filter((p) => p.x != null && p.y != null);
  const rule = d.direction_rule;
  const disputed = pts.some((p) => p.disputed);
  const intervals = pts.some((p) => p.y_low != null);
  const earlier = pts.some((p) => p.faint);
  const drawn = c.drawn.metric ? <>the derived metric <code className="text-[11px]">{c.drawn.metric}</code></> : <><code className="text-[11px]">{c.drawn.series}</code>{c.drawn.others ? `, one of ${c.drawn.total} series listed under How it is measured` : ""}</>;
  return (
    <Figure
      title={rule ? `Direction over the last ${rule.periods} periods` : "Every reading"}
      note={[c.y.log ? "log scale" : null, "each dot links to its record"].filter(Boolean).join(" · ")}
      stamps={c.stamps}
      keys={<>
        <Key swatch={<Dot />}>{c.dead ? "in the rule's window" : "a reading"}</Key>
        {earlier ? <Key swatch={<Dot faint />}>earlier</Key> : null}
        {disputed ? <Key swatch={<Dot hollow />}>disputed</Key> : null}
        {intervals ? <Key swatch={<span aria-hidden className="inline-block h-3 w-px bg-s1/40" />}>interval</Key> : null}
        {c.bands.map((b) => <Key key={b.name} swatch={<Swatch className={b.name === "fast" ? "bg-fast/15" : "bg-surface-2 ring-1 ring-grid"} />}>{b.name === "fast" ? "fast range" : "normal range"}</Key>)}
        {c.dead && c.change ? <Key swatch={<Swatch className="bg-ink/5 border border-dashed border-axis" />}>moves within {c.change.dead_band} read as stable; this window moved {c.change.label}, and higher reads {words(rule?.higher_is)}</Key> : null}
        {rule && !c.dead ? <span>the rule needs {c.needs} readings; {c.n_drawn} so far</span> : null}
      </>}
      foot={<>
        <p>{c.n_drawn} {c.n_drawn === 1 ? "reading" : "readings"} drawn from {drawn}; {d.n_observations} {d.n_observations === 1 ? "observation" : "observations"} in the evidence.</p>
        <ChartSources cs={d.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">as of</th><th scope="col">reading</th><th scope="col">value</th><th scope="col">record</th></tr></thead>
          <tbody>
            {pts.slice().reverse().map((p, i) => (
              <tr key={i}>
                <td className="num whitespace-nowrap">{p.as_of}</td>
                <td>{who(p) || "—"}{p.disputed ? " (disputed)" : ""}</td>
                <td className="num whitespace-nowrap">{fmt(p.value, d.unit)}{range(p, d.unit)}</td>
                <td>{p.href ? <Link href={p.href} prefetch={false} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{p.stamp ?? "record"}</Link> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      }
    >
      <Plot x={c.x.ticks} y={c.y} label={`${d.name}: ${c.n_drawn} readings; each dot links to its record`}>
        {c.bands.map((b) => <rect key={b.name} x="0" y={`${b.y}%`} width="100%" height={`${b.height}%`} fill={b.name === "fast" ? "var(--fast)" : "var(--surface-2)"} fillOpacity={b.name === "fast" ? 0.1 : 0.9} />)}
        {c.dead ? <rect x={`${c.dead.x}%`} y={`${c.dead.y}%`} width={`${c.dead.width}%`} height={`${c.dead.height}%`} fill="var(--ink)" fillOpacity={0.05} stroke="var(--axis)" strokeDasharray="3 3" /> : null}
        {c.line ? pts.slice(1).map((p, i) => <line key={i} x1={`${pts[i].x}%`} y1={`${pts[i].y}%`} x2={`${p.x}%`} y2={`${p.y}%`} stroke="var(--s1)" strokeWidth="1.5" opacity={pts[i].faint ? 0.35 : 1} />) : null}
        {pts.map((p, i) => p.y_low != null && p.y_high != null ? <line key={i} x1={`${p.x}%`} x2={`${p.x}%`} y1={`${p.y_low}%`} y2={`${p.y_high}%`} stroke="var(--s1)" strokeOpacity={0.35} strokeWidth="1.5" /> : null)}
        <Marks>{pts.map((p, i) => <Mark key={i} p={p} tip={tip(p, d.unit)} stop={i === pts.length - 1} hollow={!!p.disputed} faint={!!p.faint} />)}</Marks>
      </Plot>
    </Figure>
  );
}
