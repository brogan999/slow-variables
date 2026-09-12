import Link from "next/link";
import { ChangelogList } from "@/components/Changelog";
import { IndicatorCard } from "@/components/IndicatorCard";
import { StockFlowDiagram } from "@/components/StockFlowDiagram";
import { ThesisMonitor } from "@/components/ThesisMonitor";
import { diffusion, memos, obsIndex, thesis } from "@/lib/data";

export const metadata = { title: "Diffusion lens" };

export default function DiffusionPage() {
  const d = diffusion();
  const idx = obsIndex();
  const verdicts = thesis();
  const latest = memos()[0];
  return (
    <div className="flex flex-col gap-8">
      <section>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Diffusion lens</h1>
          <Link href="/capture" className="text-sm text-ink-2 hover:text-ink">Switch to capture lens →</Link>
        </div>
        <p className="mt-2 max-w-3xl text-lg leading-snug">{d.verdict}</p>
        <p className="mt-2 text-lg leading-snug text-ink-2 max-w-[60ch]">
          Five stocks from <em>AI as Normal Technology</em>. A valve carries a status only when a published indicator measures it; everything else reads <em>unmeasured</em>, not a guess.
        </p>
      </section>
      {latest ? (
        <p className="text-sm panel px-3 py-2 max-w-3xl"><span className="text-muted">This week · </span><Link href={`/memos/${latest.date}`} className="font-medium hover:underline">{latest.title}</Link><span className="text-ink-2"> — {latest.events} status events and {latest.new_observations.toLocaleString("en-US")} new observations, {latest.mode === "prose" ? `drafted by ${latest.model}` : "as a deterministic digest"}.</span></p>
      ) : null}
      <StockFlowDiagram buckets={d.buckets} valves={d.valves} />
      <section className="grid gap-4 md:grid-cols-2">
        {d.buckets.map((b) => (
          <div key={b.id} className="flex flex-col gap-2">
            <h2 className="display text-2xl leading-tight"><Link href={`/buckets/${b.id}`} className="hover:text-ink">{b.order}. {b.name}</Link> <span className="text-muted">· {b.speed_limit.split(" — ")[0].split(". ")[0]}</span></h2>
            {/* the lens is a summary: the most confident readings, then the bucket page for the rest */}
            {b.indicators.length ? [...b.indicators].sort((x, y) => (y.confidence ?? 0) - (x.confidence ?? 0)).slice(0, 4).map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />) : <p className="text-sm text-muted rounded-lg border border-dashed border-grid p-3">No published indicator for this stock yet.</p>}
            {b.indicators.length > 4 ? <p className="text-sm"><Link href={`/buckets/${b.id}`} className="underline decoration-grid underline-offset-4">All {b.indicators.length} indicators in this stock →</Link></p> : null}
          </div>
        ))}
      </section>
      <section>
        <h2 className="display text-2xl leading-tight mb-3 mt-2">Thesis monitor <span className="text-muted">· the falsification rules, evaluated nightly</span></h2>
        <ThesisMonitor verdicts={verdicts} obsIndex={idx} />
      </section>
      <section className="grid gap-6 md:grid-cols-2">
        <div>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">Last three status changes</h2>
          <ChangelogList events={d.recent_status_events} obsIndex={idx} />
        </div>
        <div>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">What would change our mind</h2>
          <ul className="text-sm text-ink-2 flex flex-col gap-1.5 list-disc pl-4">{d.what_would_change.map((w) => <li key={w}>{w}</li>)}</ul>
        </div>
      </section>
    </div>
  );
}
