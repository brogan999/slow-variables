import Link from "next/link";
import type { VentureDoc } from "@/lib/data";
import { fmt } from "@/lib/format";

// Quarterly primary-round dollars for one sub-layer: filed (Form D) and reported (Epoch) rows share the bar; every bar
// links to the observations behind it through the series index. Server component; no chart library.
export function VentureFlowStrip({ doc, obsIndex, note = true }: { doc: VentureDoc; obsIndex: Record<string, string>; note?: boolean }) {
  const qs = doc.quarters.filter((q) => q.venture_dollars || q.venture_dollars_incl_debt);  // a debt-only quarter shows its debt alone
  if (!qs.length) return <p className="text-sm text-muted">No primary rounds on file for this sub-layer&apos;s entities.</p>;
  const max = Math.max(1, ...qs.map((q) => q.venture_dollars?.value ?? 0));
  const debt = (q: (typeof qs)[number]) => {
    const d = q.venture_dollars_incl_debt;
    if (!d || d.obs_ids.length <= (q.venture_dollars?.obs_ids.length ?? 0)) return null;
    const id = d.obs_ids.find((i) => !q.venture_dollars?.obs_ids.includes(i))!;
    return { value: d.value, href: obsIndex[id] ? `/series/${obsIndex[id]}#${id}` : "#" };
  };
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-1 h-28 overflow-x-auto">
        {qs.map((q) => {
          const v = q.venture_dollars?.value ?? 0;
          const id = q.venture_dollars?.obs_ids[0] ?? "";
          const href = obsIndex[id] ? `/series/${obsIndex[id]}#${id}` : undefined;
          const bar = v ? <div className="w-full rounded-sm bg-s1" style={{ height: `${Math.max(3, (v / max) * 100)}%` }} /> : null;
          return (
            <div key={q.as_of} className="flex flex-col items-center justify-end gap-1 min-w-[44px] h-full" title={`${q.as_of}: ${fmt(v, "USD")} across ${q.round_count?.value ?? "?"} rounds`}>
              {debt(q) ? <Link href={debt(q)!.href} className="text-[10px] tabular-nums text-ink-2 underline decoration-grid underline-offset-2" title="Including Form D offerings filed as debt">incl. debt {fmt(debt(q)!.value, "USD")}</Link> : null}
              <span className="text-[10px] tabular-nums text-ink-2">{v ? fmt(v, "USD") : "—"}</span>
              {href ? <Link href={href} className="w-full h-full flex items-end" aria-label={`${q.as_of}: ${fmt(v, "USD")}`}>{bar}</Link> : <div className="w-full h-full flex items-end">{bar}</div>}
              <span className="text-[10px] text-muted tabular-nums">{q.as_of.slice(2, 7)}</span>
            </div>
          );
        })}
      </div>
      {note ? <p className="text-xs text-muted">Primary-round dollars per calendar quarter: Form D amount sold where the entity files, Epoch&apos;s press-compiled rounds otherwise. Amendments replace their originals; SPVs, secondaries and debt are excluded, except where a quarter shows its total including Form D debt above the bar.</p> : null}
    </div>
  );
}
