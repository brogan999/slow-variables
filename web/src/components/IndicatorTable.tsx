"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { Num } from "@/components/Provenance";
import { Grade, PendingNote, StatusChip } from "@/components/StatusChip";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { Card } from "@/lib/data";

type Lens = "all" | "diffusion" | "capture" | "unpublished";
const LENSES: [Lens, string][] = [["all", "All"], ["diffusion", "Diffusion"], ["capture", "Capture"], ["unpublished", "Unpublished"]];

export function IndicatorTable({ indicators, names, obsIndex }: { indicators: Card[]; names: Record<string, string>; obsIndex: Record<string, string> }) {
  const [q, setQ] = useState("");
  const [lens, setLens] = useState<Lens>("all");
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return indicators.filter((c) => {
      if (lens === "diffusion" && !c.bucket_id) return false;
      if (lens === "capture" && !c.layer_id) return false;
      if (lens === "unpublished" && c.published) return false;
      return !needle || c.name.toLowerCase().includes(needle) || c.id.includes(needle);
    });
  }, [indicators, q, lens]);
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-3">
        <Input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search indicators" aria-label="Search indicators" className="max-w-xs bg-surface" />
        <ToggleGroup value={[lens]} onValueChange={(v: string[]) => { if (v[0]) setLens(v[0] as Lens); }} aria-label="Filter by lens">
          {LENSES.map(([id, label]) => <ToggleGroupItem key={id} value={id} className="text-xs">{label}</ToggleGroupItem>)}
        </ToggleGroup>
        <span className="eyebrow" aria-live="polite">{rows.length} of {indicators.length}</span>
      </div>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th scope="col">Indicator</th><th scope="col">Bucket</th><th scope="col">Layer</th><th scope="col">Status</th><th scope="col">Conf</th><th scope="col">Grade</th><th scope="col">Latest</th><th scope="col">Obs</th></tr></thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id}>
                <td className="min-w-56">{c.published ? <Link href={`/indicators/${c.id}`} className="font-medium hover:underline underline-offset-4 decoration-grid">{c.name}</Link> : <span className="font-medium text-ink-2">{c.name}</span>}{c.published ? null : <span className="ml-2 eyebrow">unpublished</span>}{!c.published && c.unpublished_reason ? <div className="text-xs text-ink-2 mt-0.5 max-w-md">{c.unpublished_reason}</div> : null}</td>
                <td className="text-ink-2">{names[c.bucket_id ?? ""] ?? "—"}</td>
                <td className="text-ink-2">{names[c.layer_id ?? ""] ?? "—"}</td>
                <td>{c.published ? <StatusChip status={c.status} /> : <span className="text-xs text-muted">no status until published</span>}{c.stale_as_of ? <div className="text-xs text-slow mt-1">stale as of {c.stale_as_of}</div> : null}{c.pending ? <div className="mt-1"><PendingNote p={c.pending} /></div> : null}</td>
                <td className="num">{c.confidence ?? "—"}</td>
                <td><Grade grade={c.grade} /></td>
                <td className="min-w-44"><Num p={c.latest} unit={c.unit} obsIndex={obsIndex} /></td>
                <td className="num text-ink-2">{c.n_observations}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
