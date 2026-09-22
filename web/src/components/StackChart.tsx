import Link from "next/link";
import { ChartSources } from "@/components/ChartSources";
import { Figure, Key } from "@/components/Figure";
import { Marks, Plot, RectMark } from "@/components/chart";
import type { Stack } from "@/lib/data";
import { fmt } from "@/lib/format";

// Chips at the bottom in ink, cloud above in the light slate, the labs' estimate hatched: an estimate is a texture,
// never a hue of its own, and every label says "estimate" too.
const FILL: Record<string, string> = { compute_semis: "var(--s1)", compute_cloud: "var(--s3)", model: "url(#hatch-s1)" };
const Swatch = ({ id }: { id: string }) => (
  <svg width="16" height="10" aria-hidden><rect width="16" height="10" fill={FILL[id] ?? "var(--s2)"} stroke="var(--grid)" /></svg>
);

// Shares of one quarter's total, one column per quarter, laid out by the export. A quarter with no row is drawn as
// an empty outline, so a gap in the filings shows instead of closing up.
export function StackChart({ stack, title, what, unmeasured, caption }: { stack: Stack; title: string; what: string; unmeasured: string; caption?: React.ReactNode }) {
  if (!stack.axis || !stack.quarters.length) return <p className="text-sm text-muted">No series yet.</p>;
  const newest = stack.quarters.filter((q) => q.parts.length).at(-1);
  return (
    <Figure
      title={title}
      note={`share of ${what} · each segment links to its record`}
      stamps={stack.stamps}
      keys={<>
        {stack.keys.map((k) => <Key key={k.id} swatch={<Swatch id={k.id} />}>{k.name}{k.estimate ? " (estimated)" : ""}</Key>)}
        {stack.quarters.some((q) => !q.parts.length) ? <Key swatch={<svg width="16" height="10" aria-hidden><rect x="0.5" y="0.5" width="15" height="9" fill="none" stroke="var(--axis)" strokeDasharray="3 2" /></svg>}>no complete quarter on file</Key> : null}
        <span className="text-muted">{unmeasured}</span>
      </>}
      foot={<>{caption ? <p>{caption}</p> : null}<ChartSources cs={stack.sources} /></>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">quarter</th><th scope="col">part</th><th scope="col">share</th><th scope="col">record</th></tr></thead>
          <tbody>
            {stack.quarters.slice().reverse().flatMap((q) => q.parts.length ? q.parts.map((p) => (
              <tr key={q.as_of + p.id}>
                <td className="num whitespace-nowrap">{q.as_of}</td><td>{p.name}{p.estimated ? " (estimated)" : ""}</td>
                <td className="num">{fmt(p.value, "share")}</td>
                <td><Link href={p.href} prefetch={false} className="underline decoration-grid underline-offset-2 hover:decoration-ink">derived row</Link></td>
              </tr>
            )) : [<tr key={q.as_of}><td className="num">{q.as_of}</td><td colSpan={3} className="text-muted">no complete quarter on file</td></tr>])}
          </tbody>
        </table>
      }
    >
      <Plot x={stack.quarters.map((q) => ({ x: q.cx, label: q.label, minor: q.minor }))} y={stack.axis} label={`${title}, ${stack.quarters.length} quarters; each segment links to its record`} keepRight
        right={stack.ends.map((e) => <span key={e.id} style={{ top: `${e.y}%` }}>{e.name} <span className="num text-ink">{fmt(e.value, "share")}</span></span>)}>
        {stack.quarters.filter((q) => !q.parts.length).map((q) => <rect key={q.as_of} x={`${q.x}%`} y="0" width={`${q.width}%`} height="100%" fill="none" stroke="var(--axis)" strokeDasharray="3 3" />)}
        <Marks>
          {stack.quarters.flatMap((q) => q.parts.map((p) => (
            <RectMark key={q.as_of + p.id} x={q.x} y={p.y} width={q.width} height={p.height} fill={FILL[p.id] ?? "var(--s2)"} href={p.href}
              stop={q === newest && p === q.parts[0]} tip={`${q.name} · ${p.name}${p.estimated ? " (estimated)" : ""} · ${fmt(p.value, "share")} of ${what}`} />
          )))}
        </Marks>
      </Plot>
    </Figure>
  );
}
