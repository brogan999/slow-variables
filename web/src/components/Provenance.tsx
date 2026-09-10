import Link from "next/link";
import { fmt, type Point } from "@/lib/data";

// Every number renders as a link to its L3 row. `obsIndex` maps observation id -> series key.
export function Num({ p, unit, obsIndex }: { p: Point | null | undefined; unit?: string; obsIndex: Record<string, string> }) {
  if (!p || p.value === null) return <span className="text-muted">unmeasured</span>;
  const id = p.obs_ids[0];
  const key = p.series_key ?? obsIndex[id];
  const label = fmt(p.value, unit ?? p.unit);
  return (
    <span className="inline-flex items-baseline gap-1">
      {key ? <Link href={`/series/${key}#${id}`} className="underline decoration-grid underline-offset-4 hover:decoration-ink">{label}</Link> : <span>{label}</span>}
      {p.low != null && p.high != null ? <span className="text-[11px] text-ink-2" title="95% interval">({fmt(p.low, unit ?? p.unit)}–{fmt(p.high, unit ?? p.unit)})</span> : null}
      {p.disputed ? <span className="text-[11px] text-slow" title="disputed">⚑<span className="sr-only">disputed</span></span> : null}
      <span className="text-[11px] text-muted">as of {p.as_of}</span>
      {p.obs_ids.length > 1 ? <span className="text-[11px] text-muted">({p.obs_ids.length} obs)</span> : null}
    </span>
  );
}

export function ObsLinks({ ids, obsIndex, max = 6 }: { ids: string[]; obsIndex: Record<string, string>; max?: number }) {
  return (
    <span className="inline-flex flex-wrap gap-x-2 gap-y-0.5 font-mono text-[11px]">
      {ids.slice(0, max).map((id) => (
        obsIndex[id] ? <Link key={id} href={`/series/${obsIndex[id]}#${id}`} className="text-ink-2 hover:text-ink">obs:{id.slice(0, 8)}</Link> : <span key={id} className="text-muted">obs:{id.slice(0, 8)}</span>
      ))}
      {ids.length > max ? <span className="text-muted">+{ids.length - max} more</span> : null}
    </span>
  );
}
