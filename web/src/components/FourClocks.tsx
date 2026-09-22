import Link from "next/link";
import { ChartSources } from "@/components/ChartSources";
import { Fact } from "@/components/Fact";
import { Figure } from "@/components/Figure";
import { StatusChip } from "@/components/StatusChip";
import { Mark, Marks, Plot } from "@/components/chart";
import type { ArgumentDoc, Card } from "@/lib/data";
import { fmt } from "@/lib/format";

// Lines are told apart by weight and dash, and named beside their ends and in the list below: never by colour alone.
const STROKE = [{ w: 2.4, dash: "", c: "var(--s1)" }, { w: 1.6, dash: "", c: "var(--s2)" }, { w: 1.6, dash: "5 4", c: "var(--s2)" }];
const style = (i: number) => STROKE[i % STROKE.length];

// One shared log axis: each series as a multiple of its first reading. One measure, so the steepness is the data's,
// not the layout's. Every position and label place comes from the export.
export function FourClocks({ clocks, cards }: { clocks: ArgumentDoc["clocks"]; cards: Record<string, Card> }) {
  const c = clocks.chart;
  if (!c) return <p className="text-sm text-muted">Too few readings to draw.</p>;
  const stamps = [...new Set(clocks.drawn.flatMap((d) => (d.stamp ? [d.stamp] : [])))];
  return (
    <Figure
      title="How much each link of the chain has grown"
      note="log scale · each line divided by its own first reading"
      stamps={stamps}
      foot={<>
        <p>The steep line is what models can do; the flatter ones are firms and working hours catching up.{clocks.holds === false ? " (That is no longer what the latest data shows; the sentence is flagged for rewriting.)" : ""} The methods line follows the best model so far, leaving out readings METR flags as beyond what its tests can measure.{clocks.listed.length ? ` Too few readings to draw: ${clocks.listed.map((id) => cards[id]?.name ?? id).join(", ")}.` : ""}</p>
        <ChartSources cs={clocks.chart_sources} />
      </>}
      table={
        <table className="data w-full">
          <thead><tr><th scope="col">link</th><th scope="col">as of</th><th scope="col">reading</th><th scope="col">multiple</th></tr></thead>
          <tbody>
            {clocks.drawn.flatMap((d) => d.series.map((p, i) => (
              <tr key={`${d.id}${i}`}>
                <td>{d.label}</td><td className="num whitespace-nowrap">{p.as_of}</td>
                <td className="num whitespace-nowrap">{p.href ? <Link href={p.href} prefetch={false} className="underline decoration-grid underline-offset-2 hover:decoration-ink">{fmt(p.value, d.unit)}</Link> : fmt(p.value, d.unit)}</td>
                <td className="num">{fmt(p.multiple, "ratio")}</td>
              </tr>
            )))}
          </tbody>
        </table>
      }
    >
      <Plot x={c.x.ticks} y={c.y} label={`How much each link has grown since its first reading: ${clocks.drawn.map((d) => `${d.label} ${fmt(d.multiple.value, "ratio")}`).join("; ")}`} rightWidth="10.5rem"
        right={clocks.drawn.map((d) => <span key={d.id} className="whitespace-nowrap" style={{ top: `${d.label_y}%` }}>{d.label} <span className="num text-ink">{fmt(d.multiple.value, "ratio")}</span></span>)}>
        {clocks.drawn.map((d, i) => {
          const s = style(i), last = d.series[d.series.length - 1];
          return (
            <g key={d.id}>
              {d.series.slice(1).map((p, j) => <line key={j} x1={`${d.series[j].x}%`} y1={`${d.series[j].y}%`} x2={`${p.x}%`} y2={`${p.y}%`} stroke={s.c} strokeWidth={s.w} strokeDasharray={s.dash} strokeLinecap="round" />)}
              <line className="plot-leader" x1={`${last.x}%`} y1={`${last.y}%`} x2="100%" y2={`${d.label_y}%`} stroke="var(--axis)" />
              <Marks>{d.series.map((p, j) => <Mark key={j} p={p} r={2.5} stroke={s.c} stop={j === d.series.length - 1} tip={`${d.label} · ${fmt(p.multiple, "ratio")} its first reading · ${fmt(p.value, d.unit)} on ${p.as_of}`} />)}</Marks>
            </g>
          );
        })}
      </Plot>
      <ul className="mt-5 grid gap-4 sm:grid-cols-3 text-sm">
        {clocks.drawn.map((d, i) => (
          <li key={d.id} className="flex flex-col gap-1">
            <span className="eyebrow flex items-center gap-2">
              <svg aria-hidden width="22" height="6"><line x1="0" x2="22" y1="3" y2="3" stroke={style(i).c} strokeWidth={style(i).w} strokeDasharray={style(i).dash} /></svg>
              {d.label}
            </span>
            <Link href={`/indicators/${d.id}`} className="text-ink hover:underline underline-offset-2 decoration-axis">{d.name}</Link>
            <span className="text-ink-2"><Fact f={d.multiple} /> its level on {d.from}</span>
            <span className="self-start"><StatusChip status={cards[d.id]?.status} /></span>
          </li>
        ))}
      </ul>
    </Figure>
  );
}
