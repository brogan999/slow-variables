import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { StatusChip } from "@/components/StatusChip";
import { index, obsIndex, predictions } from "@/lib/data";

export const metadata = { title: "Predictions" };

const LEDGERS: Record<string, string> = { nk: "Narayanan & Kapoor", lab: "Lab timelines", ai2027: "AI 2027", capture: "Capture theses" };

export default function PredictionsPage() {
  const rows = predictions();
  const idx = obsIndex();
  const { indicators } = index();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Predictions</h1>
        <p className="text-sm text-ink-2 max-w-3xl">One ledger, four claimant families, scored against the same evidence. Claim text is verbatim from the linked source; the status vocabulary is the AI 2027 tracker&apos;s (confirmed, ahead, on track, behind, emerging, not yet testable). A claimant&apos;s self-assessment never resolves a claim.</p>
      </div>
      {Object.entries(LEDGERS).map(([ledger, name]) => {
        const items = rows.filter((p) => p.ledger === ledger && p.published);
        return (
          <section key={ledger}>
            <h2 className="text-sm font-medium text-ink-2 mb-2">{name} <span className="text-muted">· {items.length}</span></h2>
            {items.length ? (
              <ol className="flex flex-col gap-3">
                {items.map((p) => (
                  <li key={p.id} id={p.id} className="rounded-lg bg-surface ring-hair p-4 scroll-mt-4 target:ring-2 target:ring-fast/40">
                    <div className="flex flex-wrap items-center gap-2 text-xs text-ink-2">
                      <h3 className="font-medium text-ink">{p.claimant}</h3>
                      <span className="tabular-nums">{p.claim_date}</span>
                      {p.window_end ? <span>window to {p.window_end}</span> : null}
                      <StatusChip status={p.status} />
                      {p.confidence_now !== null ? <span>conf {p.confidence_now}</span> : null}
                    </div>
                    <blockquote className="mt-2 border-l-2 border-grid pl-3 text-[15px] leading-relaxed">&ldquo;{p.claim_text}&rdquo; {p.claim_url ? <a href={p.claim_url} className="text-xs text-ink-2 underline decoration-grid underline-offset-4">source</a> : null}</blockquote>
                    <p className="mt-2 text-sm"><span className="text-muted">How we track it.</span> {p.operationalisation}</p>
                    {p.related_indicators.length ? <p className="mt-1 text-xs text-ink-2">Indicators: {p.related_indicators.map((r) => <Link key={r} href={`/indicators/${r}`} className="hover:underline mr-2">{indicators.find((i) => i.id === r)?.name ?? r}</Link>)}</p> : null}
                    <details className="mt-2 text-sm"><summary className="cursor-pointer text-ink-2">Counterevidence and history</summary>
                      <p className="mt-1">{p.counterevidence}</p>
                      <div className="mt-2"><ChangelogList events={p.status_events} obsIndex={idx} showTarget={false} /></div>
                    </details>
                  </li>
                ))}
              </ol>
            ) : <p className="text-sm text-muted">No sourced claims yet in this family.</p>}
          </section>
        );
      })}
    </div>
  );
}
