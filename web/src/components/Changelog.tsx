import Link from "next/link";
import { publishedIds, type StatusEvent } from "@/lib/data";
import { indicatorHref } from "@/lib/format";
import { ObsLinks } from "./Provenance";
import { StatusChip } from "./StatusChip";

export function ChangelogList({ events, obsIndex, showTarget = true }: { events: StatusEvent[]; obsIndex: Record<string, string>; showTarget?: boolean }) {
  if (!events.length) return <p className="text-sm text-muted">No status changes yet.</p>;
  return (
    <ol className="flex flex-col gap-3">
      {events.map((e) => (
        <li key={e.id} className="text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-muted tabular-nums">{e.created_at.slice(0, 10)}</span>
            {showTarget ? <Link href={e.target_type === "prediction" ? `/predictions#${e.target_id}` : indicatorHref(e.target_id, publishedIds().has(e.target_id))} className="font-medium hover:underline">{e.target_id}</Link> : null}
            <StatusChip status={e.old_status} /> <span className="text-muted" aria-hidden>→</span><span className="sr-only">to</span> <StatusChip status={e.new_status} />
            <span className="text-xs text-muted">conf {e.old_conf ?? "—"} → {e.new_conf} · {e.author}</span>
          </div>
          <p className="text-ink-2 mt-1">{e.reason}</p>
          {e.counterevidence_considered ? <p className="text-xs text-muted mt-1">Weighed against it: {e.counterevidence_considered}</p> : null}
          {e.evidence_ids.length ? <div className="mt-1"><ObsLinks ids={e.evidence_ids} obsIndex={obsIndex} /></div> : null}
        </li>
      ))}
    </ol>
  );
}

// The full changelog grouped by month, newest month open; each month is a <details> so 300 events stay navigable.
export function ChangelogByMonth({ events, obsIndex }: { events: StatusEvent[]; obsIndex: Record<string, string> }) {
  const months = [...new Set(events.map((e) => e.created_at.slice(0, 7)))].sort().reverse();
  return (
    <div className="flex flex-col gap-3">
      {months.map((m, i) => {
        const items = events.filter((e) => e.created_at.startsWith(m));
        return (
          <details key={m} open={i === 0} className="group panel p-3">
            <summary className="cursor-pointer list-none text-sm font-medium"><span className="text-muted mr-2 inline-block transition-transform group-open:rotate-90">▸</span>{m} <span className="text-muted font-normal">· {items.length} change{items.length === 1 ? "" : "s"}</span></summary>
            <div className="mt-3"><ChangelogList events={items} obsIndex={obsIndex} /></div>
          </details>
        );
      })}
    </div>
  );
}
