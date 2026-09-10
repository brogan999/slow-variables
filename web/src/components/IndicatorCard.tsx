import Link from "next/link";
import type { Card } from "@/lib/data";
import { Num } from "./Provenance";
import { Grade, StatusChip } from "./StatusChip";

export function IndicatorCard({ c, obsIndex }: { c: Card; obsIndex: Record<string, string> }) {
  const pts = c.sparkline.filter((p) => p.value !== null);
  return (
    <div className="rounded-lg bg-surface ring-hair p-3 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-2">
        <Link href={`/indicators/${c.id}`} className="font-medium leading-snug hover:underline">{c.name}</Link>
        <Grade grade={c.grade} />
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
        <StatusChip status={c.published ? c.status : null} />
        {c.leading_lagging ? <span className="rounded bg-grid/60 px-1.5 py-0.5">{c.leading_lagging}</span> : null}
        {c.confidence !== null ? <span title="confidence, 0–95, independent of status">conf {c.confidence}</span> : null}
        {c.stale_as_of ? <span className="text-slow">stale as of {c.stale_as_of}</span> : null}
      </div>
      <div className="flex items-end justify-between gap-3">
        <div className="text-sm"><Num p={c.latest} unit={c.unit} obsIndex={obsIndex} /></div>
        {pts.length > 1 ? <Sparkline pts={pts.map((p) => p.value as number)} /> : null}
      </div>
    </div>
  );
}

function Sparkline({ pts }: { pts: number[] }) {
  const w = 96, h = 28;
  const lo = Math.min(...pts), hi = Math.max(...pts);
  const y = (v: number) => (hi === lo ? h / 2 : h - 2 - ((v - lo) / (hi - lo)) * (h - 4));
  const d = pts.map((v, i) => `${i === 0 ? "M" : "L"}${(i / (pts.length - 1)) * (w - 2) + 1},${y(v).toFixed(1)}`).join(" ");
  return (
    <svg width={w} height={h} aria-hidden className="shrink-0">
      <path d={d} fill="none" stroke="var(--s1)" strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}
