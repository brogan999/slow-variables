import Link from "next/link";
import { fmt } from "@/lib/format";

type Row = { as_of: string; layer_id: string | null; value: number; obs_ids: string[] };
const LAYERS: [string, string][] = [["compute_semis", "Semis"], ["compute_cloud", "Cloud"], ["model", "Labs"], ["deployment_application", "Apps"]];

// Stacked share of filed segment operating income per calendar quarter; layers with no series are hatched as unmeasured.
export function MarginStackChart({ rows, obsIndex }: { rows: Row[]; obsIndex: Record<string, string> }) {
  const quarters = [...new Set(rows.map((r) => r.as_of))].sort();
  if (!quarters.length) return <p className="text-sm text-muted">No filed margin series yet.</p>;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-1 overflow-x-auto">
        {quarters.map((q) => {
          const parts = LAYERS.map(([id, name]) => ({ id, name, row: rows.find((r) => r.as_of === q && r.layer_id === id) }));
          return (
            <div key={q} className="flex flex-col items-center gap-1 min-w-[56px]">
              <div className="w-full h-40 flex flex-col-reverse rounded-sm overflow-hidden ring-hair">
                {parts.map((p) => {
                  if (!p.row) return null;
                  const id = p.row.obs_ids[0];
                  const bar = <div className="w-full h-full" style={{ background: p.id === "compute_semis" ? "var(--s1)" : "var(--s2)" }} title={`${p.name} ${fmt(p.row.value, "share")} ${q}`} />;
                  return obsIndex[id] ? <Link key={p.id} href={`/series/${obsIndex[id]}#${id}`} className="w-full flex flex-col-reverse" style={{ height: `${p.row.value * 100}%` }} aria-label={`${p.name} ${fmt(p.row.value, "share")} in ${q}`}>{bar}</Link> : <div key={p.id} className="w-full" style={{ height: `${p.row.value * 100}%` }}>{bar}</div>;
                })}
              </div>
              <span className="num text-[10px] text-muted">{q.slice(2, 7)}</span>
            </div>
          );
        })}
      </div>
      <div className="flex flex-wrap gap-x-4 text-xs text-ink-2">
        <span><span className="inline-block w-3 h-3 align-middle mr-1" style={{ background: "var(--s1)" }} />Semis</span>
        <span><span className="inline-block w-3 h-3 align-middle mr-1" style={{ background: "var(--s2)" }} />Cloud</span>
        <span className="text-muted">Labs and apps: no filed or estimated margin series yet, so their share is unmeasured rather than drawn.</span>
      </div>
    </div>
  );
}
