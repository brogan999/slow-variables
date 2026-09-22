import { ChartSources } from "./ChartSources";
import { Figure, Key } from "./Figure";
import { Mark, Marks, Plot } from "./chart";
import type { ContextDoc } from "@/lib/data";
import { fmt } from "@/lib/format";

const LINE = [{ c: "var(--s1)", dash: undefined }, { c: "var(--s2)", dash: "5 3" }, { c: "var(--s2)", dash: "1.5 3" }];
const style = (i: number) => LINE[i % LINE.length]; // a fourth line repeats the first style; the key and labels still name it
const link = "underline decoration-grid underline-offset-2 hover:decoration-ink";

// Official statistics read beside the claims about what happens next: no status, one axis per figure. A point computed
// from other rows (a year-on-year change, a share) links to its own row in the table below, which links those rows.
// A line is not drawn across a missing period.
export function ContextFigures({ doc }: { doc: ContextDoc }) {
  return <>{doc.figures.map((f) => <ContextFigure key={f.id} f={f} />)}</>;
}

function ContextFigure({ f }: { f: ContextDoc["figures"][number] }) {
  return (
    <Figure
      title={f.title}
      note="official statistics · each dot links to its row"
      stamps={f.stamps}
      keys={f.lines.length > 1 ? <>{f.lines.map((ln, i) => (
        <Key key={ln.label} swatch={<svg width="18" height="10" aria-hidden><line x1="0" x2="18" y1="5" y2="5" stroke={style(i).c} strokeWidth="1.75" strokeDasharray={style(i).dash} /></svg>}>{ln.label}</Key>
      ))}</> : undefined}
      foot={<>
        <p>{f.caption}</p>
        <ChartSources cs={f.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">line</th><th scope="col">as of</th><th scope="col">value</th><th scope="col">from</th></tr></thead>
          <tbody>{f.lines.flatMap((ln) => ln.points.slice().reverse().map((p) => (
            <tr key={`${ln.label}${p.as_of}`} id={p.id ? `d-${p.id}` : undefined} className="scroll-mt-24 target:bg-surface-2">
              <td>{ln.label}</td>
              <td className="num whitespace-nowrap">{p.as_of}</td>
              <td className="num">{p.inputs || !p.href ? fmt(p.value, f.unit) : <a href={p.href} className={link}>{fmt(p.value, f.unit)}</a>}</td>
              <td className="num">{p.inputs ? p.inputs.map((r, k) => <span key={k}>{k ? " · " : ""}{r.href ? <a href={r.href} className={link}>{r.label}</a> : r.label}</span>) : "the row itself"}</td>
            </tr>
          )))}</tbody>
        </table>
      }
    >
      <Plot x={f.x.ticks} y={f.y} label={`${f.title}; each dot links to its row`} rightWidth="9rem"
        right={f.lines.map((ln) => <span key={ln.label} style={{ top: `${ln.label_y}%` }}>{ln.label}<span className="block num text-ink">{fmt(ln.points[ln.points.length - 1].value, f.unit)}</span></span>)}>
        {f.lines.map((ln, i) => {
          const last = ln.points[ln.points.length - 1], s = style(i);
          return (
            <g key={ln.label}>
              {ln.points.slice(1).map((p, j) => p.joined ? <line key={j} x1={`${ln.points[j].x}%`} y1={`${ln.points[j].y}%`} x2={`${p.x}%`} y2={`${p.y}%`} stroke={s.c} strokeWidth="1.75" strokeDasharray={s.dash} strokeLinecap="round" /> : null)}
              <line className="plot-leader" x1={`${last.x}%`} y1={`${last.y}%`} x2="100%" y2={`${ln.label_y}%`} stroke="var(--axis)" />
              <Marks>{ln.points.map((p) => <Mark key={p.as_of} p={p} r={2} stroke={s.c} stop={p === last} tip={`${ln.label} · ${fmt(p.value, f.unit)} · ${p.as_of}`} />)}</Marks>
            </g>
          );
        })}
      </Plot>
    </Figure>
  );
}
