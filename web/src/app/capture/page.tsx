import Link from "next/link";
import { StackPlate } from "@/components/ArgumentParts";
import { ChangelogList } from "@/components/Changelog";
import { ChartSources } from "@/components/ChartSources";
import { IndicatorCard } from "@/components/IndicatorCard";
import { MarginStackChart } from "@/components/MarginStackChart";
import { PageHeader } from "@/components/PageHeader";
import { StatusChip } from "@/components/StatusChip";
import { capture, obsIndex, thesis } from "@/lib/data";

export const metadata = { title: "Who profits from AI" };

// The headline is the rents-migrate-up test's state in words; the page never writes its own verdict.
const CLAIM: Record<string, string> = {
  contradicted: "So far, the profit is staying with the chip makers",
  supported: "The profit is moving up to the labs and apps",
  unsupported: "The profit is not yet moving up the stack",
  untestable: "Too early to say who keeps the profit",
};

export default function CaptureLens() {
  const c = capture();
  const idx = obsIndex();
  const test = thesis().find((v) => v.id === "rents_migrate_up");
  return (
    <div className="flex flex-col gap-16">
      <PageHeader eyebrow="Who profits · the capture lens" title={CLAIM[test?.state ?? "untestable"] ?? CLAIM.untestable}
        lede="The AI industry is a stack of layers, from chips and data centres at the bottom to the apps people use at the top. This page follows where the profit settles, layer by layer. Gross profit is what is left of revenue after paying to deliver the product; where a layer publishes none, it is left out rather than guessed." />

      <StackPlate />

      {c.layers.map((l) => {
        const published = l.indicators.filter((i) => i.published);
        return (
          <section key={l.id} id={l.id} className="border-t border-grid pt-8 scroll-mt-8">
            <div className="eyebrow flex items-center gap-3">Layer {l.order}{l.id === "training_input" ? <Link href="/buckets/return_arrow" className="normal-case tracking-normal font-sans text-ink-2 hover:text-ink">⇄ feeds back into methods</Link> : null}</div>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <h2 className="display text-[1.75rem] md:text-[2.125rem] leading-tight"><Link href={`/layers/${l.id}`} className="hover:underline underline-offset-4 decoration-axis">{l.name}</Link></h2>
              <StatusChip status={l.status} />
            </div>
            <p className="mt-2 mb-6 text-ink-2 max-w-[62ch]">{l.description}</p>
            {published.length ? (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                {/* the lens is a summary: the most confident readings, then the layer page for the rest */}
                {[...published].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0)).slice(0, 4).map((i) => <IndicatorCard key={i.id} c={i} obsIndex={idx} />)}
              </div>
            ) : <p className="text-sm text-muted">No published indicator for this layer yet.</p>}
            {published.length > 4 ? <p className="mt-4 text-sm"><Link href={`/layers/${l.id}`} className="underline decoration-axis underline-offset-4">All {published.length} indicators on this layer →</Link></p> : null}
          </section>
        );
      })}

      <section className="border-t border-grid pt-8 flex flex-col gap-4">
        <details>
          <summary className="cursor-pointer display text-xl">The all-filed check: operating income, five segments</summary>
          <div className="mt-4">
            <MarginStackChart rows={c.margin_stack_series} obsIndex={idx} parts={[{ id: "compute_semis", name: "Chip segments", fill: "var(--s1)", prefix: "sec_seg.nvda." }, { id: "compute_cloud", name: "Cloud segments", fill: "var(--s2)", prefix: "sec_seg.amzn." }]} unmeasured="NVIDIA Compute & Networking and AMD Data Center against AWS, Google Cloud and Microsoft Intelligent Cloud; labs and apps file no segments." />
            <ChartSources cs={c.margin_stack_sources} />
          </div>
        </details>
        {c.verdict ? <details><summary className="cursor-pointer display text-xl">Every layer&apos;s reading</summary><p className="mt-4 text-ink-2 max-w-[75ch]">{c.verdict}</p></details> : null}
        <details>
          <summary className="cursor-pointer display text-xl">Recent changes</summary>
          <div className="mt-4"><ChangelogList events={c.recent_status_events} obsIndex={idx} /></div>
        </details>
        <details>
          <summary className="cursor-pointer display text-xl">What would change each reading</summary>
          <ul className="mt-4 text-sm text-ink-2 flex flex-col gap-2 list-disc pl-5 max-w-[75ch]">{c.what_would_change.map((w) => <li key={w}>{w}</li>)}</ul>
        </details>
      </section>
    </div>
  );
}
