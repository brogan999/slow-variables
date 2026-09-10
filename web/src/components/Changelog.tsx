import Link from "next/link";
import type { StatusEvent } from "@/lib/data";
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
            {showTarget ? <Link href={`/indicators/${e.target_id}`} className="font-medium hover:underline">{e.target_id}</Link> : null}
            <StatusChip status={e.old_status} /> <span className="text-muted">→</span> <StatusChip status={e.new_status} />
            <span className="text-xs text-muted">conf {e.old_conf ?? "—"} → {e.new_conf} · {e.author}</span>
          </div>
          <p className="text-ink-2 mt-1">{e.reason}</p>
          {e.evidence_ids.length ? <div className="mt-1"><ObsLinks ids={e.evidence_ids} obsIndex={obsIndex} /></div> : null}
        </li>
      ))}
    </ol>
  );
}
