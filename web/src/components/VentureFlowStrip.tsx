"use client";
import Link from "next/link";
import { useState } from "react";
import type { VentureDoc } from "@/lib/data";
import { ChartSources } from "./ChartSources";
import { fmt } from "@/lib/format";

const SEG: Record<string, { name: string; style: React.CSSProperties }> = {
  "formd:equity": { name: "Form D equity (filed, tier 4)", style: { background: "var(--s1)" } },
  "epoch:equity": { name: "Epoch rounds (reported, tier 5)", style: { background: "var(--s2)" } },
  "formd:debt": { name: "Form D debt (filed)", style: { background: "transparent", boxShadow: "inset 0 0 0 1.5px var(--s1)" } },
};

// Quarterly primary-round dollars for one sub-layer, stacked by source; every segment links to its first round's row.
// Totals and segment values come from the export; the browser only scales heights.
export function VentureFlowStrip({ doc, note = true }: { doc: VentureDoc; note?: boolean }) {
  const hasDebt = doc.quarters.some((q) => q.by_source?.some((s) => s.kind === "debt"));
  const [debt, setDebt] = useState(false);
  const total = (q: VentureDoc["quarters"][number]) => (debt ? q.venture_dollars_incl_debt : q.venture_dollars);
  const qs = doc.quarters.filter((q) => total(q));
  if (!qs.length) return <p className="text-sm text-muted">No primary rounds on file for this sub-layer&apos;s entities.</p>;
  const max = Math.max(1, ...qs.map((q) => total(q)?.value ?? 0));
  const shown = (kind: string) => debt || kind === "equity";
  return (
    <div className="flex flex-col gap-2">
      {hasDebt ? (
        <div role="group" aria-label="Venture dollars shown" className="flex gap-1 text-xs">
          {[["Equity", false], ["Incl. debt", true]].map(([label, v]) => (
            <button key={String(label)} type="button" aria-pressed={debt === v} onClick={() => setDebt(v as boolean)} className={`rounded-sm px-2 py-0.5 ring-hair ${debt === v ? "bg-ink text-background" : "text-ink-2 hover:text-ink"}`}>{label}</button>
          ))}
        </div>
      ) : null}
      <div className="flex items-end gap-1 h-28 overflow-x-auto">
        {qs.map((q) => {
          const t = total(q)!;
          const segs = (q.by_source ?? []).filter((s) => shown(s.kind));
          return (
            <div key={q.as_of} className="flex flex-col items-center justify-end gap-1 min-w-[44px] h-full" title={`${q.as_of}: ${fmt(t.value, "USD")} across ${q.round_count?.value ?? "?"} rounds`}>
              <span className="text-[10px] tabular-nums text-ink-2">{fmt(t.value, "USD")}</span>
              <div className="w-full flex flex-col-reverse gap-[2px]" style={{ height: `${Math.max(3, (t.value / max) * 100)}%` }}>
                {segs.map((s) => {
                  const k = `${s.source}:${s.kind}`;
                  const label = `${q.as_of}: ${SEG[k]?.name ?? k} ${fmt(s.value, "USD")}`;
                  const bar = <div className="w-full h-full rounded-sm" style={SEG[k]?.style} />;
                  return s.href ? (
                    <Link key={k} href={s.href} className="w-full flex" style={{ height: `${(s.value / t.value) * 100}%` }} aria-label={label} title={label}>{bar}</Link>
                  ) : <div key={k} className="w-full flex" style={{ height: `${(s.value / t.value) * 100}%` }} title={label}>{bar}</div>;
                })}
              </div>
              <span className="text-[10px] text-muted tabular-nums">{q.as_of.slice(2, 7)}</span>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-ink-2">
        {Object.entries(SEG).filter(([k]) => shown(k.split(":")[1]) && qs.some((q) => q.by_source?.some((s) => `${s.source}:${s.kind}` === k))).map(([k, v]) => (
          <span key={k}><span className="inline-block w-2.5 h-2.5 align-middle mr-1 rounded-sm" style={v.style} />{v.name}</span>
        ))}
      </div>
      <ChartSources cs={doc.chart_sources} />
      {note ? <p className="text-xs text-muted">Primary-round dollars per calendar quarter: Form D amount sold where the entity files, Epoch&apos;s press-compiled rounds for an entity-quarter with no filing. Amendments replace their originals; SPVs and secondaries are excluded; debt appears only under &ldquo;Incl. debt&rdquo;.</p> : null}
    </div>
  );
}
