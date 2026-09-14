import Link from "next/link";
import { Fact } from "@/components/Fact";
import { StatusChip } from "@/components/StatusChip";
import type { ArgumentDoc, Card } from "@/lib/data";
import { fmt } from "@/lib/format";

// One shared log axis: each series as a multiple of its first reading since the start date. One measure, so the
// steepness is the data's, not the layout's. Lines are told apart by weight and dash, and named in the legend.
const STROKE = [{ w: 2.4, dash: "" }, { w: 1.6, dash: "" }, { w: 1.6, dash: "5 4" }];

// Two renderings of one chart: a compact one with larger type below the sm breakpoint, where the plate is narrow.
function Chart({ clocks, compact }: { clocks: ArgumentDoc["clocks"]; compact: boolean }) {
  const W = 660, H = compact ? 440 : 280, L = compact ? 76 : 44, R = 16, T = 14, B = compact ? 48 : 30, fs = compact ? 24 : 12, k = compact ? 1.8 : 1;
  const all = clocks.drawn.flatMap((d) => d.series.map((p) => p.as_of));
  const t0 = Date.parse(clocks.start), t1 = Math.max(...all.map(Date.parse));
  const ratios = clocks.drawn.flatMap((d) => d.series.map((p) => p.value / d.series[0].value));
  const top = Math.max(2, ...ratios), bottom = Math.min(1, ...ratios);
  const x = (d: string) => L + ((Date.parse(d) - t0) / (t1 - t0)) * (W - L - R);
  const y = (m: number) => T + (1 - Math.log(m / bottom) / Math.log(top / bottom)) * (H - T - B);
  const ticks = [0.5, 1, 2, 5, 10, 20, 50, 100].filter((v) => v >= bottom * 0.95 && v <= top * 1.05);
  const years = [...new Set(all.map((d) => d.slice(0, 4)))].sort();
  const id = compact ? "clocks-c" : "clocks";
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={`w-full h-auto ${compact ? "sm:hidden" : "hidden sm:block"}`} role="img" aria-labelledby={`${id}-title ${id}-desc`}>
      <title id={`${id}-title`}>{`How much each link of the chain has grown since ${clocks.start}`}</title>
      <desc id={`${id}-desc`}>{clocks.drawn.map((d) => `${d.name}: ${fmt(d.multiple.value, "ratio")} its reading on ${d.from}`).join("; ")}.</desc>
      {ticks.map((v) => (
        <g key={v}>
          <line x1={L} x2={W - R} y1={y(v)} y2={y(v)} stroke="var(--grid)" strokeWidth={k} />
          <text x={L - 10} y={y(v) + fs / 3} textAnchor="end" className="font-mono" fontSize={fs} fill="var(--muted)">×{v}</text>
        </g>
      ))}
      {years.map((yr) => (Date.parse(`${yr}-01-01`) >= t0 ? <text key={yr} x={x(`${yr}-01-01`)} y={H - fs * 0.6} textAnchor="middle" className="font-mono" fontSize={fs} fill="var(--muted)">{yr}</text> : null))}
      {clocks.drawn.map((d, i) => (
        <g key={d.id}>
          <polyline fill="none" stroke={i ? "var(--s2)" : "var(--s1)"} strokeWidth={STROKE[i % 3].w * k} strokeDasharray={STROKE[i % 3].dash} strokeLinejoin="round"
            points={d.series.map((p) => `${x(p.as_of).toFixed(1)},${y(p.value / d.series[0].value).toFixed(1)}`).join(" ")} />
          <circle cx={x(d.series.at(-1)!.as_of)} cy={y(d.multiple.value)} r={4 * k} fill={i ? "var(--s2)" : "var(--s1)"} stroke="var(--surface)" strokeWidth={2 * k} />
        </g>
      ))}
    </svg>
  );
}

export function FourClocks({ clocks, cards }: { clocks: ArgumentDoc["clocks"]; cards: Record<string, Card> }) {
  return (
    <figure className="plate">
      <Chart clocks={clocks} compact={false} />
      <Chart clocks={clocks} compact />
      <ul className="mt-4 grid gap-3 sm:grid-cols-3 text-sm">
        {clocks.drawn.map((d, i) => (
          <li key={d.id} className="flex flex-col gap-1 font-sans">
            <span className="eyebrow flex items-center gap-2">
              <svg aria-hidden width="22" height="6"><line x1="0" x2="22" y1="3" y2="3" stroke={i ? "var(--s2)" : "var(--s1)"} strokeWidth={STROKE[i % 3].w} strokeDasharray={STROKE[i % 3].dash} /></svg>
              {d.label}
            </span>
            <Link href={`/indicators/${d.id}`} className="text-ink hover:underline underline-offset-2 decoration-axis">{d.name}</Link>
            <span className="text-ink-2"><Fact f={d.multiple} /> its level on {d.from}</span>
            <span className="self-start"><StatusChip status={cards[d.id]?.status} /></span>
          </li>
        ))}
      </ul>
      {clocks.listed.length ? <p className="mt-3 text-xs text-muted">Too few readings to draw: {clocks.listed.map((id) => cards[id]?.name ?? id).join(", ")}.</p> : null}
      <figcaption className="mt-4 text-sm text-ink-2 leading-relaxed">Each line is a reading divided by its own first value, all on one scale. The methods line follows the best model so far, leaving out readings METR flags as beyond what its tests can measure. The steep one is what models can do; the flat ones are firms and working hours catching up.{clocks.holds === false ? " (That is no longer what the latest data shows; the sentence is flagged for rewriting.)" : ""}</figcaption>
    </figure>
  );
}
