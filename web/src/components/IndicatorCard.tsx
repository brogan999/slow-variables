import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import type { Card } from "@/lib/data";
import { Num } from "./Provenance";
import { PendingNote, StatusChip } from "./StatusChip";

// A card says four things: what it is, how it reads, the latest number, and its recent shape. Grade, confidence and
// the rule live one click deeper, on the indicator page.
export function IndicatorCard({ c, obsIndex }: { c: Card; obsIndex: Record<string, string> }) {
  return (
    <div className="panel p-4 flex flex-col gap-3">
      <Link href={indicatorHref(c.id, c.published)} className="font-medium leading-snug hover:underline underline-offset-4 decoration-axis">{c.name}</Link>
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <StatusChip status={c.published ? c.status : "unpublished"} />
        {c.stale_as_of ? <span className="text-error">stale since {c.stale_as_of}</span> : null}
        <PendingNote p={c.pending} />
      </div>
      {!c.published && c.unpublished_reason ? <p className="text-xs text-ink-2">Unpublished: {c.unpublished_reason}</p> : null}
      <div className="flex items-end justify-between gap-3 mt-auto">
        <div className="text-lg"><Num p={c.latest} unit={c.unit} obsIndex={obsIndex} compact /></div>
        {c.spark ? <Sparkline spark={c.spark} /> : null}
      </div>
    </div>
  );
}

function Sparkline({ spark }: { spark: NonNullable<Card["spark"]> }) {
  return (
    <svg width="96" height="28" viewBox="0 0 96 28" aria-hidden className="shrink-0">
      <path d={spark.d} fill="none" stroke="var(--s1)" strokeWidth="1.25" strokeLinejoin="round" />
      <circle cx={spark.end[0]} cy={spark.end[1]} r="2" fill="var(--ink)" />
    </svg>
  );
}
