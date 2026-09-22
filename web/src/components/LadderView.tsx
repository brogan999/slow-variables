import Link from "next/link";
import { ChartSources } from "./ChartSources";
import { Figure } from "./Figure";
import { Chip } from "./StatusChip";
import type { LadderDoc } from "@/lib/data";

// Appendix E's rungs of continual learning, highest first, filled up to the current production level. Each rung
// lists the companies whose own descriptions put a product there, and research that has reached it (research never
// moves the level). The current level is a chip, linked to the reading that set it.
export function LadderView({ doc }: { doc: LadderDoc }) {
  const level = doc.current?.value ?? null;
  return (
    <Figure
      title="How far products have climbed the ladder of learning on the job"
      note="filled up to the current production level"
      foot={<>
        <p>Production rows are vendors describing their own systems (tier 7 unless independently evaluated); research rows never move the level. The rule: rungs 0 to 3 normal, 4 emerging, 5 and 6 fast.</p>
        <ChartSources cs={doc.chart_sources} />
      </>}
    >
      <ol className="flex flex-col gap-2">
        {[...doc.rungs].reverse().map((r) => {
          const reached = level !== null && r.level <= level;
          return (
            <li key={r.level} className={`rounded-[3px] px-3 py-2.5 ring-1 ${reached ? "bg-surface-2 ring-grid" : "ring-grid"}`}>
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <span className={`num text-[11px] ${reached ? "text-ink" : "text-muted"}`}>L{r.level}</span>
                <span className={`font-sans font-semibold ${reached ? "text-ink" : "text-ink-2"}`}>{r.name}</span>
                {level === r.level && doc.current ? <Chip name="current production level" meta={`as of ${doc.current.as_of}`} href={`/indicators/continual_learning_level`} /> : null}
              </div>
              <p className="mt-1 text-[12px] text-ink-2">{r.description} <span className="text-muted">What would show it: {r.observables}.</span></p>
              {r.production.length ? (
                <ul className="mt-2 flex flex-wrap gap-1.5">
                  {r.production.map((p) => <li key={p.obs_id}><Chip name={p.name} meta={`${p.as_of} · tier ${p.tier}`} href={p.href ?? undefined} /></li>)}
                </ul>
              ) : null}
              {r.research.length ? (
                <ul className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-[12px] text-muted">
                  {r.research.map((p) => <li key={p.obs_id}>research: {p.href ? <Link href={p.href} className="underline decoration-grid underline-offset-2 hover:text-ink">{p.name}</Link> : p.name} {p.as_of}</li>)}
                </ul>
              ) : null}
            </li>
          );
        })}
      </ol>
    </Figure>
  );
}
