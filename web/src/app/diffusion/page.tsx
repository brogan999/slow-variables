import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { StatusChip } from "@/components/StatusChip";
import { PageHeader } from "@/components/PageHeader";
import { StockFlowDiagram } from "@/components/StockFlowDiagram";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { BandStrips, Freshness, HeadlineSeries, LagModel, StageGauges, Sureness } from "@/components/DiffusionFigures";
import { argument, diffusion, indicator, obsIndex, thesis } from "@/lib/data";

export const metadata = { title: "How fast AI is spreading" };


export default function DiffusionPage() {
  const d = diffusion();
  const idx = obsIndex();
  const verdicts = thesis();
  const f = d.figures;
  return (
    <div className="flex flex-col gap-16">
      <PageHeader eyebrow="How fast · the diffusion lens" title={argument().headlines.diffusion.claim}
        lede={<>Arvind Narayanan and Sayash Kapoor, two Princeton computer scientists, argue that AI will spread the way electricity did: over decades, through stages. This page times each stage separately, from new methods to reorganised work. A stage carries a status only when a published indicator measures it; otherwise it reads unmeasured.</>} />

      <StageGauges f={f.gauges} />

      <StockFlowDiagram buckets={d.buckets} valves={d.valves} sources={d.n_sources} />

      <LagModel f={f.model} />

      <section aria-labelledby="stages" className="flex flex-col gap-4">
        <h2 id="stages" className="eyebrow">The stages, one card each</h2>
        <p className="max-w-[62ch] font-serif text-lg text-ink-2">Why it matters: a technology changes the economy only as fast as its slowest stage, so a fast first stage says little on its own.</p>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {d.buckets.map((b) => (
            <article key={b.id} id={b.id} className="flex scroll-mt-8 flex-col gap-3 rounded-[4px] border border-grid bg-surface p-5">
              <div className="eyebrow">Stage {b.order}</div>
              <h3 className="display text-[1.375rem] leading-tight"><Link href={`/buckets/${b.id}`} className="decoration-axis underline-offset-4 hover:underline">{b.name}</Link></h3>
              <div className="flex flex-wrap items-center gap-2 text-sm"><StatusChip status={b.status} /><span className="text-muted">{b.tally.scored} of {b.tally.published} published readings count</span></div>
              <p className="text-[15px] text-ink-2"><span className="text-muted">What limits its speed: </span>{b.speed_limit}</p>
              {b.indicators.length ? (
                <ul className="flex flex-col gap-1.5 border-t border-dashed border-grid pt-3 text-sm">
                  {[...b.indicators].sort((x, y) => (y.confidence ?? 0) - (x.confidence ?? 0)).slice(0, 3).map((c) => (
                    <li key={c.id} className="flex flex-wrap items-center justify-between gap-2"><Link href={`/indicators/${c.id}`} className="hover:underline">{c.name}</Link><StatusChip status={c.status} /></li>
                  ))}
                </ul>
              ) : <p className="text-sm text-muted">No published indicator for this stage yet.</p>}
              <Link href={`/buckets/${b.id}`} className="mt-auto text-sm font-medium underline decoration-axis underline-offset-4 hover:decoration-ink">{b.n_indicators > 3 ? `All ${b.n_indicators} gauges for this stage →` : "The stage in full →"}</Link>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="readings" className="flex flex-col gap-6">
        <h2 id="readings" className="eyebrow">How close each stage is to fast</h2>
        <p className="max-w-[62ch] font-serif text-lg text-ink-2">A status is a word. Behind it is a number and a line it has or has not crossed, so these figures show the distance as well as the verdict.</p>
        <BandStrips f={f.bands} />
        <HeadlineSeries f={f.headline} docs={f.headline.map((h) => indicator(h.id))} />
      </section>

      <section aria-labelledby="trust" className="flex flex-col gap-6">
        <h2 id="trust" className="eyebrow">How far to trust each stage&apos;s reading</h2>
        <p className="max-w-[62ch] font-serif text-lg text-ink-2">A stage can read normal on fresh, well-evidenced gauges or on old and thin ones. These figures show which.</p>
        <Freshness f={f.fresh} />
        <Sureness f={f.sure} />
      </section>

      <section className="border-t border-grid pt-8 flex flex-col gap-4">
        <details>
          <summary className="cursor-pointer display text-xl">The tests behind the headline</summary>
          <div className="mt-4"><ThesisMonitor verdicts={verdicts} obsIndex={idx} /></div>
        </details>
        <details>
          <summary className="cursor-pointer display text-xl">Recent changes</summary>
          <div className="mt-4"><ChangelogList events={d.recent_status_events} obsIndex={idx} /></div>
        </details>
        <details>
          <summary className="cursor-pointer display text-xl">What would change each reading</summary>
          <ul className="mt-4 text-sm text-ink-2 flex flex-col gap-2 list-disc pl-5 max-w-[75ch]">{d.what_would_change.map((w) => <li key={w}>{w}</li>)}</ul>
        </details>
      </section>
    </div>
  );
}
