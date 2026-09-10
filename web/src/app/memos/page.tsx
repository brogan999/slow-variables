import Link from "next/link";
import { memos } from "@/lib/data";

export const metadata = { title: "Memos" };

export default function MemosPage() {
  const rows = memos();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-semibold tracking-tight">Weekly memos</h1>
      <p className="text-sm text-ink-2 max-w-3xl">What changed each week: status moves, new evidence, watchlist posts, the thesis monitor and any crosswalk pair that moved in opposite directions. A model drafts the prose when a key is configured and every number is checked against the record it cites; otherwise the memo is the deterministic digest. Each memo is a pull request a human merged.</p>
      {rows.length ? (
        <ul className="flex flex-col gap-3">
          {rows.map((m) => (
            <li key={m.date} className="rounded-lg bg-surface ring-hair p-3 text-sm">
              <div className="flex flex-wrap items-baseline gap-x-3"><Link href={`/memos/${m.date}`} className="font-medium hover:underline">{m.title}</Link><span className="text-xs text-muted">{m.since} to {m.date} · {m.mode === "prose" ? `drafted by ${m.model}` : "deterministic digest"} · {m.events} status events · {m.new_observations} new observations</span></div>
              <p className="mt-1 text-ink-2">{m.summary}</p>
            </li>
          ))}
        </ul>
      ) : <p className="text-sm text-muted">No memo yet; the first runs on Monday 09:17 UTC.</p>}
    </div>
  );
}
