import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { ChartSources } from "@/components/ChartSources";
import { MarginStackChart } from "@/components/MarginStackChart";
import { StackVertical } from "@/components/StackVertical";
import { StatusChip } from "@/components/StatusChip";
import { capture, obsIndex } from "@/lib/data";

export const metadata = { title: "Capture lens" };

export default function CaptureLens() {
  const c = capture();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Capture lens</h1>
          <Link href="/diffusion" className="text-sm text-ink-2 hover:text-ink">← Switch to diffusion lens</Link>
        </div>
        {c.verdict ? <p className="mt-2 max-w-3xl text-lg leading-snug">{c.verdict}</p> : null}
        <p className="mt-2 text-lg leading-snug text-ink-2 max-w-[60ch]">Who keeps the surplus, layer by layer. Bars are each layer&apos;s share of the stack&apos;s gross profit: chips and cloud from filings, labs estimated and hatched. A layer without a series shows a hairline, and its indicators carry the reading.</p>
      </section>
      <StackVertical layers={c.layers} bars={c.stack_bars} />
      <section>
        <h2 className="display text-2xl leading-tight mb-3 mt-2">Gross profit by layer <span className="text-muted">· share per calendar quarter</span></h2>
        <MarginStackChart rows={c.gross_profit_stack_series} obsIndex={idx} parts={[{ id: "compute_semis", name: "Chips", fill: "var(--s1)", prefix: "sec.nvda.gross_profit." }, { id: "compute_cloud", name: "Cloud", fill: "var(--s2)", prefix: "sec_seg.msft.intelligent_cloud.revenue." }, { id: "model", name: "Labs", fill: "var(--s1)", prefix: "epoch." }]} unmeasured="Apps: no gross-profit series, so unmeasured rather than drawn." />
        <ChartSources cs={c.gross_profit_stack_sources} />
      </section>
      <section>
        <h2 className="display text-2xl leading-tight mb-3 mt-2">Filed operating income, five segments <span className="text-muted">· the filed check</span></h2>
        <MarginStackChart rows={c.margin_stack_series} obsIndex={idx} parts={[{ id: "compute_semis", name: "Semis segments", fill: "var(--s1)", prefix: "sec_seg.nvda." }, { id: "compute_cloud", name: "Cloud segments", fill: "var(--s2)", prefix: "sec_seg.amzn." }]} unmeasured="NVIDIA Compute & Networking and AMD Data Center against AWS, Google Cloud and Microsoft Intelligent Cloud; labs and apps file no segments." />
        <ChartSources cs={c.margin_stack_sources} />
      </section>
      <ol className="flex flex-col gap-3">
        {c.layers.map((l) => {
          const published = l.indicators.filter((i) => i.published);
          return (
            <li key={l.id} className="panel p-4">
              <div className="flex flex-wrap items-center gap-3">
                <h2 className="display text-xl leading-tight"><Link href={`/layers/${l.id}`} className="hover:underline underline-offset-4 decoration-grid">{l.order}. {l.name}</Link></h2>
                <StatusChip status={l.status} />
                {l.tally?.scored ? <span className="text-xs text-muted" title={`${l.tally.scored} of ${l.tally.published} published indicators cast a vote; one instrument votes once`}>{l.tally.scored} of {l.tally.published} scored</span> : published.length ? <span className="text-xs text-muted">{published.length} indicator{published.length === 1 ? "" : "s"}</span> : null}
                {l.id === "training_input" ? <Link href="/buckets/return_arrow" className="text-xs text-ink-2 hover:text-ink ml-auto">⇄ return arrow</Link> : null}
              </div>
              <p className="text-sm text-ink-2 mt-1">{l.description}</p>
              {published.length ? (
                <>
                  {/* the lens is a summary: the most confident readings, then the layer page for the rest */}
                  <div className="mt-3 grid gap-3 md:grid-cols-2">{[...published].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)).slice(0, 4).map((i) => <IndicatorCard key={i.id} c={i} obsIndex={idx} />)}</div>
                  {published.length > 4 ? <p className="mt-2 text-sm"><Link href={`/layers/${l.id}`} className="underline decoration-grid underline-offset-4">All {published.length} indicators on this layer →</Link></p> : null}
                </>
              ) : <p className="mt-3 text-sm text-muted rounded-lg border border-dashed border-grid p-3">No published indicator for this layer yet.</p>}
            </li>
          );
        })}
      </ol>
      <section className="grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">Last three status changes</h2>
          <ChangelogList events={c.recent_status_events} obsIndex={idx} />
        </div>
        <div>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">What would change our mind</h2>
          <ul className="text-sm text-ink-2 flex flex-col gap-1.5 list-disc pl-4">{c.what_would_change.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      </section>
    </div>
  );
}
