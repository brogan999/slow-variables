import Link from "next/link";
import type { StackRow } from "@/lib/data";
import { fmt } from "@/lib/format";

export type StackPart = { id: string; name: string; fill: string; prefix: string };
// One directional texture marks an estimate; colour never carries it alone ("est." is in every label).
export const HATCH = "repeating-linear-gradient(45deg, var(--s1) 0 1.5px, transparent 1.5px 5px)";

// Stacked shares per calendar quarter. Estimated rows are hatched; layers with no series are named, never drawn.
export function MarginStackChart({ rows, parts, unmeasured, obsIndex }: { rows: StackRow[]; parts: StackPart[]; unmeasured: string; obsIndex: Record<string, string> }) {
  const quarters = [...new Set(rows.map((r) => r.as_of))].sort();
  if (!quarters.length) return <p className="text-sm text-muted">No margin series yet.</p>;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-end gap-1 overflow-x-auto">
        {quarters.map((q) => (
          <div key={q} className="flex flex-col items-center gap-1 min-w-[56px]">
            <div className="w-full h-40 flex flex-col-reverse gap-[2px] rounded-sm overflow-hidden ring-hair">
              {parts.map((p) => {
                const row = rows.find((r) => r.as_of === q && r.layer_id === p.id);
                if (!row) return null;
                const est = row.basis === "estimated";
                const label = `${p.name}${est ? " (est., grade C)" : ""} ${fmt(row.value, "share")} in ${q}`;
                const id = row.obs_ids.find((i) => (obsIndex[i] ?? "").startsWith(p.prefix));
                const bar = <div className="w-full h-full" style={{ background: est ? HATCH : p.fill }} title={label} />;
                return id ? (
                  <Link key={p.id} href={`/series/${obsIndex[id]}#${id}`} className="w-full flex flex-col-reverse" style={{ height: `${row.value * 100}%` }} aria-label={label}>{bar}</Link>
                ) : <div key={p.id} className="w-full" style={{ height: `${row.value * 100}%` }} aria-label={label}>{bar}</div>;
              })}
            </div>
            <span className="num text-[10px] text-muted">{q.slice(2, 7)}</span>
          </div>
        ))}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-2">
        {parts.map((p) => {
          const est = rows.some((r) => r.layer_id === p.id && r.basis === "estimated");
          return <span key={p.id}><span className="inline-block w-3 h-3 align-middle mr-1 ring-hair" style={{ background: est ? HATCH : p.fill }} />{p.name}{est ? " (est., grade C)" : ""}</span>;
        })}
        <span className="text-muted">{unmeasured}</span>
      </div>
    </div>
  );
}
