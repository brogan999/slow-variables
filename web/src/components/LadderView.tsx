import Link from "next/link";
import { ChartSources } from "./ChartSources";
import type { LadderDoc } from "@/lib/data";

// Appendix E rungs, filled up to the current production level; production rows and research rows listed on each rung.
export function LadderView({ doc, obsIndex }: { doc: LadderDoc; obsIndex: Record<string, string> }) {
  const level = doc.current?.value ?? null;
  return (
    <div className="flex flex-col gap-2">
      {[...doc.rungs].reverse().map((r) => {
        const reached = level !== null && r.level <= level;
        return (
          <div key={r.level} className={`rounded-lg p-3 ring-hair ${reached ? "bg-surface" : "bg-transparent"}`}>
            <div className="flex flex-wrap items-baseline gap-2 text-sm">
              <span className={`font-mono text-xs ${reached ? "text-ink" : "text-muted"}`}>L{r.level}</span>
              <span className={`font-medium ${reached ? "" : "text-ink-2"}`}>{r.name}</span>
              {level === r.level ? <span className="text-xs rounded-full border border-ink-2 px-2">current production level</span> : null}
            </div>
            <p className="text-xs text-ink-2 mt-0.5">{r.description} <span className="text-muted">Observables: {r.observables}.</span></p>
            {r.production.length ? <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">{r.production.map((p) => <li key={p.obs_id}><Link href={obsIndex[p.obs_id] ? `/series/${obsIndex[p.obs_id]}#${p.obs_id}` : "#"} className="underline decoration-grid underline-offset-4">{p.entity_id ?? p.subject}</Link> <span className="text-muted">{p.as_of} · t{p.tier}</span></li>)}</ul> : null}
            {r.research.length ? <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted">{r.research.map((p) => <li key={p.obs_id}>research: <Link href={obsIndex[p.obs_id] ? `/series/${obsIndex[p.obs_id]}#${p.obs_id}` : "#"} className="underline decoration-grid underline-offset-4">{p.subject}</Link> {p.as_of}</li>)}</ul> : null}
          </div>
        );
      })}
      <p className="text-xs text-muted">Production rows are vendors describing their own systems (tier 7 unless independently evaluated); research rows never move the level. The rule: L0-L3 normal, L4 emerging, L5-L6 fast.</p>
      <ChartSources cs={doc.chart_sources} />
    </div>
  );
}
