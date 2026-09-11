import Link from "next/link";
import type { Card, Layer, StackBar } from "@/lib/data";
import { fmt, words } from "@/lib/format";
import { HATCH } from "./MarginStackChart";
import { Grade, StatusChip } from "./StatusChip";

// The stack as one vertical: bar width = the layer's share of stack gross profit, summed by the export; an estimated
// layer is hatched and labelled "est."; a layer with no series is a dashed hairline. Icon + text carry the status.
export function StackVertical({ layers, bars }: { layers: (Layer & { indicators: Card[]; status: string | null })[]; bars: Record<string, StackBar> }) {
  const asOf = Object.values(bars)[0]?.as_of;
  return (
    <div className="flex flex-col gap-2">
      {layers.map((l) => {
        const published = l.indicators.filter((i) => i.published);
        const b = bars[l.id];
        const width = b ? Math.max(2, b.value * 100) : 6;
        return (
          <div key={l.id} className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-2 sm:gap-3">
            <div className="min-w-0">
              <h2 className="font-medium"><Link href={`/layers/${l.id}`} className="hover:underline">{l.order}. {l.name}</Link></h2>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-2">
                <StatusChip status={l.status} />
                {published.length ? <span>{published.length} indicator{published.length === 1 ? "" : "s"}</span> : null}
                {l.id === "training_input" ? <Link href="/buckets/return_arrow" className="hover:text-ink">⇄ return arrow</Link> : null}
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="h-7 rounded-sm ring-hair" style={{ width: `${width}%`, background: b ? (b.estimated ? HATCH : "var(--s1)") : "transparent", border: b ? "none" : "1px dashed var(--axis)" }} title={b ? `${fmt(b.value, "share")} of stack gross profit${b.estimated ? " (estimated)" : ""}` : "no gross-profit series"} />
              <span className="text-xs tabular-nums text-ink-2">
                {b ? (
                  <>
                    {b.parts.map((p, i) => (
                      <span key={p.label}>{i ? " · " : ""}<Link href={p.href} className="underline decoration-grid underline-offset-4">{p.label} {fmt(p.value, "share")}{p.estimated ? " est." : ""}</Link>{p.grade ? <> <Grade grade={p.grade} /></> : null}</span>
                    ))}
                    {asOf ? <span className="text-muted"> as of {asOf}</span> : null}
                  </>
                ) : <span className="text-muted">{words("unmeasured")}</span>}
              </span>
            </div>
          </div>
        );
      })}
      <p className="text-xs text-muted mt-1">Bar = share of the stack&apos;s gross profit in the latest complete quarter: chips are NVIDIA and AMD (filed), cloud is Microsoft Intelligent Cloud (the one cloud segment that files its cost), labs are OpenAI and Anthropic estimated from Epoch&apos;s figures (hatched, grade C). Apps have no gross-profit series, so they are not drawn.</p>
    </div>
  );
}
