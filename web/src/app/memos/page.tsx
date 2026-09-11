import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { memos } from "@/lib/data";

export const metadata = { title: "Memos" };

export default function MemosPage() {
  const rows = memos();
  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Weekly memos" lede="What changed each week: status moves, new evidence, watchlist posts, the thesis monitor and any crosswalk pair that moved in opposite directions. A model drafts the prose when a key is configured and every number is checked against the record it cites; otherwise the memo is the deterministic digest. Each memo is a pull request a human merged." action={<a href="/memos/feed.xml" className="text-sm text-ink-2 hover:text-ink">RSS feed</a>} />
      {rows.length ? (
        <ol className="flex flex-col border-t border-grid">
          {rows.map((m) => (
            <li key={m.date} className="grid gap-2 md:grid-cols-[10rem_minmax(0,1fr)] py-6 border-b border-grid">
              <div className="eyebrow">{m.date}</div>
              <div className="flex flex-col gap-2 max-w-[68ch]">
                <h2 className="display text-2xl md:text-[1.75rem] leading-tight"><Link href={`/memos/${m.date}`} className="hover:underline underline-offset-4 decoration-grid">{m.title}</Link></h2>
                <p className="text-ink-2">{m.summary}</p>
                <p className="eyebrow">{m.since} → {m.date} · {m.mode === "prose" ? `drafted by ${m.model}` : "deterministic digest"} · {m.events} status events · {m.new_observations.toLocaleString("en-US")} new observations</p>
              </div>
            </li>
          ))}
        </ol>
      ) : <p className="text-muted">No memo yet; the first runs on Monday 09:17 UTC.</p>}
    </div>
  );
}
