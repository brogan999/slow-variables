import Link from "next/link";
import type { VentureDoc } from "@/lib/data";
import { fmt } from "@/lib/format";

// Quarterly primary-round dollars for one sub-layer: filed (Form D) and reported (Epoch) rows share the bar; every bar
// links to the observations behind it through the series index. Server component; no chart library.
export function VentureFlowStrip({ doc, obsIndex }: { doc: VentureDoc; obsIndex: Record<string, string> }) {
  const qs = doc.quarters.filter((q) => q.venture_dollars);
  if (!qs.length) return <p className="text-sm text-muted">No primary rounds on file for this sub-layer&apos;s entities.</p>;
  const max = Math.max(...qs.map((q) => q.venture_dollars!.value));
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-1 h-28 overflow-x-auto">
        {qs.map((q) => {
          const v = q.venture_dollars!.value;
          const id = q.venture_dollars!.obs_ids[0];
          const href = obsIndex[id] ? `/series/${obsIndex[id]}#${id}` : undefined;
          const bar = <div className="w-full rounded-sm bg-s1" style={{ height: `${Math.max(3, (v / max) * 100)}%` }} />;
          return (
            <div key={q.as_of} className="flex flex-col items-center justify-end gap-1 min-w-[44px] h-full" title={`${q.as_of}: ${fmt(v, "USD")} across ${q.round_count?.value ?? "?"} rounds`}>
              <span className="text-[10px] tabular-nums text-ink-2">{fmt(v, "USD")}</span>
              {href ? <Link href={href} className="w-full h-full flex items-end" aria-label={`${q.as_of}: ${fmt(v, "USD")}`}>{bar}</Link> : <div className="w-full h-full flex items-end">{bar}</div>}
              <span className="text-[10px] text-muted tabular-nums">{q.as_of.slice(2, 7)}</span>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-muted">Primary-round dollars per calendar quarter: Form D amount sold where the entity files, Epoch&apos;s press-compiled rounds otherwise. Amendments replace their originals; SPVs, secondaries and debt are excluded.</p>
    </div>
  );
}
