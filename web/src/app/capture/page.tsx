import Link from "next/link";
import { StackPlate } from "@/components/ArgumentParts";
import { FourPlaces } from "@/components/FourPlaces";
import { ChangelogList } from "@/components/Changelog";
import { StackChart } from "@/components/StackChart";
import { PageHeader } from "@/components/PageHeader";
import { StatusChip } from "@/components/StatusChip";
import { argument, capture, obsIndex, outlook } from "@/lib/data";

export const metadata = { title: "Who profits from AI" };


export default function CaptureLens() {
  const c = capture();
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-16">
      <PageHeader eyebrow="Who profits · the capture lens" title={argument().headlines.capture.claim}
        lede="The AI industry is a stack of layers, from chips and data centres at the bottom to the apps people use at the top. This page follows where the profit settles, layer by layer. Gross profit is what is left of revenue after paying to deliver the product; where a layer publishes none, it is left out rather than guessed." />

      <FourPlaces shifts={outlook().shifts} />
      <StackPlate />

      <section aria-labelledby="layers" className="flex flex-col gap-4">
        <h2 id="layers" className="eyebrow">The layers, from the chips up</h2>
        <p className="max-w-[62ch] font-serif text-lg text-ink-2">Why it matters: whichever layer holds the scarce part keeps the profit, and the four places above say where that is moving.</p>
        <ol className="flex flex-col border-t border-grid">
          {[...c.layers].sort((a, b) => a.order - b.order).map((l) => {
            const published = [...l.indicators.filter((i) => i.published)].sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0));
            return (
              <li key={l.id} id={l.id} className="grid scroll-mt-8 gap-3 border-b border-grid py-5 md:grid-cols-[18rem_1fr] md:gap-6">
                <div className="flex flex-col items-start gap-2">
                  <div className="eyebrow flex items-center gap-3">Layer {l.order}{l.id === "training_input" ? <Link href="/buckets/return_arrow" className="normal-case tracking-normal font-sans text-ink-2 hover:text-ink">⇄ feeds back into methods</Link> : null}</div>
                  <h3 className="display text-[1.375rem] leading-tight"><Link href={`/layers/${l.id}`} className="decoration-axis underline-offset-4 hover:underline">{l.name}</Link></h3>
                  <StatusChip status={l.status} />
                </div>
                <div className="flex flex-col gap-2 text-[15px]">
                  <p className="text-ink-2">{l.description}</p>
                  {published.length ? (
                    <ul className="flex flex-col gap-1.5 text-sm">
                      {published.slice(0, 3).map((i) => <li key={i.id} className="flex flex-wrap items-center justify-between gap-2"><Link href={`/indicators/${i.id}`} className="hover:underline">{i.name}</Link><StatusChip status={i.status} /></li>)}
                    </ul>
                  ) : l.held?.length ? (
                    <p className="text-sm text-ink-2">Held, not yet published: {l.held.map((h, k) => <span key={h.id}>{k ? "; " : ""}<span className="text-ink">{h.name}</span> ({h.reason})</span>)}</p>
                  ) : <p className="text-sm text-muted">No data for this layer yet.</p>}
                  <Link href={`/layers/${l.id}`} className="self-start text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">{l.n_published > 3 ? `All ${l.n_published} gauges on this layer →` : "The layer in full →"}</Link>
                </div>
              </li>
            );
          })}
        </ol>
      </section>

      <section className="border-t border-grid pt-8 flex flex-col gap-4">
        <StackChart stack={c.margin_stack} title="The all-filed check: operating income, five segments" what="operating income"
          unmeasured="NVIDIA Compute & Networking and AMD Data Center against AWS, Google Cloud and Microsoft Intelligent Cloud; labs and apps file no segments." />
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
