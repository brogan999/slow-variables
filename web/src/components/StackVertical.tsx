import Link from "next/link";
import type { Card, Layer, MarginShare } from "@/lib/data";
import { fmt, summarise, words } from "@/lib/format";
import { StatusChip } from "./StatusChip";

// The stack as one vertical: bar width = the layer's share of filed segment operating income (where a filed series
// exists), unmeasured layers at a fixed hairline width. Icon + text carry the status; colour never does alone.
export function StackVertical({ layers, shares, obsIndex }: { layers: (Layer & { indicators: Card[] })[]; shares: Record<string, MarginShare>; obsIndex: Record<string, string> }) {
  const share = (id: string) => (id === "compute_physical" ? (shares.compute_semis?.value ?? 0) + (shares.compute_cloud?.value ?? 0) : undefined);
  const asOf = Object.values(shares)[0]?.as_of;
  return (
    <div className="flex flex-col gap-2">
      {layers.map((l) => {
        const published = l.indicators.filter((i) => i.published);
        const statuses = published.map((i) => i.status).filter(Boolean) as string[];
        const summary = summarise(statuses);
        const s = share(l.id);
        const width = s !== undefined ? Math.max(12, s * 100) : 6;
        return (
          <div key={l.id} className="grid grid-cols-1 sm:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)] items-center gap-2 sm:gap-3">
            <div className="min-w-0">
              <h2 className="font-medium"><Link href={`/layers/${l.id}`} className="hover:underline">{l.order}. {l.name}</Link></h2>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-2">
                <StatusChip status={summary} />
                {published.length ? <span>{published.length} indicator{published.length === 1 ? "" : "s"}</span> : null}
                {l.id === "training_input" ? <Link href="/buckets/return_arrow" className="hover:text-ink">⇄ return arrow</Link> : null}
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-7 rounded-sm" style={{ width: `${width}%`, background: s !== undefined ? "var(--s1)" : "transparent", border: s === undefined ? "1px dashed var(--axis)" : "none" }} title={s !== undefined ? `${fmt(s, "share")} of filed segment operating income` : "no filed margin series yet"} />
              <span className="text-xs tabular-nums text-ink-2">
                {s !== undefined ? (
                  <>
                    {shares.compute_semis ? <Link href={`/series/${obsIndex[shares.compute_semis.obs_ids[0]] ?? ""}`} className="underline decoration-grid underline-offset-4">semis {fmt(shares.compute_semis.value, "share")}</Link> : null}
                    {shares.compute_cloud ? <> · cloud {fmt(shares.compute_cloud.value, "share")}</> : null}
                    {asOf ? <span className="text-muted"> as of {asOf}</span> : null}
                  </>
                ) : <span className="text-muted">{words("unmeasured")}</span>}
              </span>
            </div>
          </div>
        );
      })}
      <p className="text-xs text-muted mt-1">Bar = share of filed segment operating income across NVIDIA, AMD, AWS, Google Cloud and Microsoft Intelligent Cloud, the one layer group with segment filings. A layer without a filed or estimated margin series shows a hairline.</p>
    </div>
  );
}
