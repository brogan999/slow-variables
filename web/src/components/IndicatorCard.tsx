import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import type { Card } from "@/lib/data";
import { Num } from "./Provenance";
import { ConfidenceDial } from "./ConfidenceDial";
import { Grade, PendingNote, StatusChip } from "./StatusChip";

export function IndicatorCard({ c, obsIndex }: { c: Card; obsIndex: Record<string, string> }) {
  const pts = c.sparkline.filter((p) => p.value !== null);
  return (
    <div className="panel p-4 flex flex-col gap-2.5">
      <div className="flex items-start justify-between gap-2">
        <Link href={indicatorHref(c.id, c.published)} className="font-medium leading-snug hover:underline underline-offset-4 decoration-grid">{c.name}</Link>
        <Grade grade={c.grade} />
      </div>
      <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
        <StatusChip status={c.published ? c.status : null} />
        {c.leading_lagging ? <span className="eyebrow">{c.leading_lagging}</span> : null}
        <ConfidenceDial value={c.confidence} size={30} />
        {c.stale_as_of ? <span className="text-slow">stale as of {c.stale_as_of}</span> : null}
        <PendingNote p={c.pending} />
      </div>
      {c.answers?.length ? <p className="text-xs text-muted">{c.answers.join(" · ")}</p> : null}
      {!c.published && c.unpublished_reason ? <p className="text-xs text-ink-2">Unpublished: {c.unpublished_reason}</p> : null}
      <div className="flex items-end justify-between gap-3">
        <div className="text-lg"><Num p={c.latest} unit={c.unit} obsIndex={obsIndex} /></div>
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
      <path d={d} fill="none" stroke="var(--s1)" strokeWidth="1.25" strokeLinejoin="round" />
      <circle cx={w - 1} cy={y(pts[pts.length - 1]).toFixed(1)} r="2" fill="var(--ink)" />
    </svg>
  );
}
