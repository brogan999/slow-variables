import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { MarginStackChart } from "@/components/MarginStackChart";
import { StackVertical } from "@/components/StackVertical";
import { StatusChip } from "@/components/StatusChip";
import { capture, obsIndex } from "@/lib/data";
import { summarise } from "@/lib/format";

export const metadata = { title: "Capture lens" };

export default function CaptureLens() {
  const c = capture();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Capture lens</h1>
          <Link href="/" className="text-sm text-ink-2 hover:text-ink">← Switch to diffusion lens</Link>
        </div>
        {c.verdict ? <p className="mt-2 max-w-3xl text-lg leading-snug">{c.verdict}</p> : null}
        <p className="mt-1 text-sm text-ink-2 max-w-3xl">Who keeps the surplus, layer by layer. The compute layer's bar is sized by its filed segment operating income; a layer without a filed margin series shows a hairline, and its indicators carry the reading.</p>
      </section>
      <StackVertical layers={c.layers} shares={c.margin_shares} obsIndex={idx} />
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Margin stack by quarter <span className="text-muted">· share of filed segment operating income</span></h2>
        <MarginStackChart rows={c.margin_stack_series} obsIndex={idx} />
      </section>
      <ol className="flex flex-col gap-3">
        {c.layers.map((l) => {
          const published = l.indicators.filter((i) => i.published);
          const statuses = published.map((i) => i.status).filter(Boolean) as string[];
          const summary = summarise(statuses);
          return (
            <li key={l.id} className="rounded-lg bg-surface ring-hair p-4">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="font-medium"><Link href={`/layers/${l.id}`} className="hover:underline">{l.order}. {l.name}</Link></h2>
                <StatusChip status={summary} />
                {published.length ? <span className="text-xs text-muted">{published.length} indicator{published.length === 1 ? "" : "s"}</span> : null}
                {l.id === "training_input" ? <Link href="/buckets/return_arrow" className="text-xs text-ink-2 hover:text-ink ml-auto">⇄ return arrow</Link> : null}
              </div>
              <p className="text-sm text-ink-2 mt-1">{l.description}</p>
              {published.length ? <div className="mt-3 grid gap-3 md:grid-cols-2">{published.map((i) => <IndicatorCard key={i.id} c={i} obsIndex={idx} />)}</div> : <p className="mt-3 text-sm text-muted rounded-lg border border-dashed border-grid p-3">No published indicator for this layer yet.</p>}
            </li>
          );
        })}
      </ol>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Last three status changes</h2>
        <ChangelogList events={c.recent_status_events} obsIndex={idx} />
      </section>
    </div>
  );
}
