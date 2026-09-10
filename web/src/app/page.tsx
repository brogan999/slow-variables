import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { StockFlowDiagram } from "@/components/StockFlowDiagram";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { diffusion, obsIndex, thesis } from "@/lib/data";

export default function DiffusionLens() {
  const d = diffusion();
  const idx = obsIndex();
  const verdicts = thesis();
  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">Diffusion lens</h1>
          <Link href="/capture" className="text-sm text-ink-2 hover:text-ink">Switch to capture lens →</Link>
        </div>
        <p className="mt-2 max-w-3xl text-lg leading-snug">{d.verdict}</p>
        <p className="mt-1 text-sm text-ink-2 max-w-3xl">
          Five stocks from <em>AI as Normal Technology</em>. A valve carries a status only when a published indicator measures it; everything else reads <em>unmeasured</em>, not a guess.
        </p>
      </section>
      <StockFlowDiagram buckets={d.buckets} valves={d.valves} />
      <section className="grid gap-4 md:grid-cols-2">
        {d.buckets.map((b) => (
          <div key={b.id} className="flex flex-col gap-2">
            <h2 className="text-sm font-medium text-ink-2"><Link href={`/buckets/${b.id}`} className="hover:text-ink">{b.order}. {b.name}</Link> <span className="text-muted">· {b.speed_limit.split(" — ")[0].split(". ")[0]}</span></h2>
            {b.indicators.length ? b.indicators.map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />) : <p className="text-sm text-muted rounded-lg border border-dashed border-grid p-3">No published indicator yet. Connectors for this stock land in the next milestone.</p>}
          </div>
        ))}
      </section>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Thesis monitor <span className="text-muted">· the falsification rules, evaluated nightly</span></h2>
        <ThesisMonitor verdicts={verdicts} obsIndex={idx} />
      </section>
      <section className="grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="text-sm font-medium text-ink-2 mb-2">Last three status changes</h2>
          <ChangelogList events={d.recent_status_events} obsIndex={idx} />
        </div>
        <div>
          <h2 className="text-sm font-medium text-ink-2 mb-2">What would change our mind</h2>
          <ul className="text-sm text-ink-2 flex flex-col gap-1.5 list-disc pl-4">{d.what_would_change.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      </section>
    </div>
  );
}
