"use client";

import { ArrowDownIcon, ArrowUpDownIcon, ArrowUpIcon } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Num } from "@/components/Provenance";
import { Grade, PendingNote, StatusChip } from "@/components/StatusChip";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import type { Card } from "@/lib/data";

type Lens = "all" | "diffusion" | "capture" | "unpublished";
type Key = "name" | "status" | "conf" | "grade" | "latest";
// status order follows the chip glyphs: faster/concentrating, consistent/stable, slower/dispersing, mixed/unclear/emerging, unmeasured
const ORDER = ["faster_than_normal", "concentrating", "consistent_with_normal", "stable", "slower_than_normal", "dispersing", "mixed", "unclear", "emerging", "not_yet_measurable"];
const GET: Record<Key, (c: Card) => string | number | null> = {
  name: (c) => c.name.toLowerCase(),
  status: (c) => (c.published && c.status ? ORDER.indexOf(c.status) : null),
  conf: (c) => c.confidence,
  grade: (c) => c.grade,
  latest: (c) => c.latest?.as_of ?? null,
};
const FIRST: Record<Key, 1 | -1> = { name: 1, status: 1, conf: -1, grade: 1, latest: -1 };
const LENSES: [Lens, string][] = [["all", "All"], ["diffusion", "Diffusion"], ["capture", "Capture"], ["unpublished", "Unpublished"]];

export function IndicatorTable({ indicators, names, obsIndex }: { indicators: Card[]; names: Record<string, string>; obsIndex: Record<string, string> }) {
  const [q, setQ] = useState("");
  const [lens, setLens] = useState<Lens>("all");
  const [sort, setSort] = useState<{ k: Key; dir: 1 | -1 } | null>(null);
  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const out = indicators.filter((c) => {
      if (lens === "diffusion" && !c.bucket_id) return false;
      if (lens === "capture" && !c.layer_id) return false;
      if (lens === "unpublished" && c.published) return false;
      return !needle || c.name.toLowerCase().includes(needle) || c.id.includes(needle);
    });
    if (!sort) return out;
    return [...out].sort((a, b) => {  // missing values always sort last, in either direction
      const x = GET[sort.k](a), y = GET[sort.k](b);
      return x === y ? 0 : x === null ? 1 : y === null ? -1 : (x < y ? -1 : 1) * sort.dir;
    });
  }, [indicators, q, lens, sort]);
  // a function, not a component: an inner component would remount the button and drop keyboard focus on each press
  const head = (k: Key, label: string) => {
    const dir = sort?.k === k ? sort.dir : 0;
    return (
      <th scope="col" aria-sort={dir === 1 ? "ascending" : dir === -1 ? "descending" : undefined}>
        <button type="button" onClick={() => setSort({ k, dir: dir ? (-dir as 1 | -1) : FIRST[k] })} className="inline-flex items-center gap-1 uppercase tracking-[inherit] hover:text-ink">
          {label}
          {dir === 1 ? <ArrowUpIcon aria-hidden className="size-3" /> : dir === -1 ? <ArrowDownIcon aria-hidden className="size-3" /> : <ArrowUpDownIcon aria-hidden className="size-3 opacity-50" />}
        </button>
      </th>
    );
  };
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
          <thead><tr>{head("name", "Indicator")}<th scope="col">Bucket</th><th scope="col">Layer</th>{head("status", "Status")}{head("conf", "Conf")}{head("grade", "Grade")}{head("latest", "Latest")}<th scope="col">Obs</th></tr></thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.id} id={c.id} className="scroll-mt-24">
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
