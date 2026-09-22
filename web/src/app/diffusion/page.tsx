import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { PageHeader } from "@/components/PageHeader";
import { StockFlowDiagram } from "@/components/StockFlowDiagram";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { argument, diffusion, obsIndex, thesis } from "@/lib/data";

export const metadata = { title: "How fast AI is spreading" };


export default function DiffusionPage() {
  const d = diffusion();
  const idx = obsIndex();
  const verdicts = thesis();
  return (
    <div className="flex flex-col gap-16">
      <PageHeader eyebrow="How fast · the diffusion lens" title={argument().headlines.diffusion.claim}
        lede={<>Arvind Narayanan and Sayash Kapoor, two Princeton computer scientists, argue that AI will spread the way electricity did: over decades, through stages. This page times each stage separately, from new methods to reorganised work. A stage carries a status only when a published indicator measures it; otherwise it reads unmeasured.</>} />

      <StockFlowDiagram buckets={d.buckets} valves={d.valves} sources={d.n_sources} />

      {d.buckets.map((b) => (
        <section key={b.id} id={b.id} className="border-t border-grid pt-8 scroll-mt-8">
          <div className="eyebrow">Stage {b.order}</div>
          <h2 className="display text-[1.75rem] md:text-[2.125rem] leading-tight mt-2"><Link href={`/buckets/${b.id}`} className="hover:underline underline-offset-4 decoration-axis">{b.name}</Link></h2>
          <p className="mt-2 mb-6 text-ink-2 max-w-[62ch]"><span className="text-muted">What limits its speed: </span>{b.speed_limit}</p>
          {b.indicators.length ? (
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              {/* the lens is a summary: the most confident readings, then the stage page for the rest */}
              {[...b.indicators].sort((x, y) => (y.confidence ?? 0) - (x.confidence ?? 0)).slice(0, 4).map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}
            </div>
          ) : <p className="text-sm text-muted">No published indicator for this stage yet.</p>}
          {b.n_indicators > 4 ? <p className="mt-4 text-sm"><Link href={`/buckets/${b.id}`} className="underline decoration-axis underline-offset-4">All {b.n_indicators} indicators for this stage →</Link></p> : null}
        </section>
      ))}

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
