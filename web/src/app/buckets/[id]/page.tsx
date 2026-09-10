import Link from "next/link";
import { IndicatorCard } from "@/components/IndicatorCard";
import { LadderView } from "@/components/LadderView";
import { bucket, index, ladder, obsIndex } from "@/lib/data";

export const dynamicParams = false;
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return { title: bucket(id).name };
}
export function generateStaticParams() { return index().buckets.map((b) => ({ id: b.id })); }

export default async function BucketPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const b = bucket(id);
  const idx = obsIndex();
  const { layers } = index();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs text-muted"><Link href="/" className="hover:text-ink">Diffusion</Link> / bucket {b.order}</p>
        <h1 className="text-2xl font-semibold tracking-tight">{b.name}</h1>
        <dl className="mt-3 grid gap-2 text-sm md:grid-cols-3">
          <div><dt className="text-muted">Stock</dt><dd>{b.stock}</dd></div>
          <div><dt className="text-muted">Speed limit</dt><dd>{b.speed_limit}</dd></div>
          <div><dt className="text-muted">Valve measured</dt><dd>{b.valve.replace(/_/g, " ")}</dd></div>
        </dl>
      </div>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Indicators</h2>
        {b.indicators.length ? <div className="grid gap-3 md:grid-cols-2">{b.indicators.map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}</div> : <p className="text-sm text-muted">None published yet.</p>}
      </section>
      {id === "return_arrow" ? (
        <section>
          <h2 className="text-sm font-medium text-ink-2 mb-2">Continual-learning ladder</h2>
          <LadderView doc={ladder()} obsIndex={idx} />
        </section>
      ) : null}
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Crosswalk to the capture lens</h2>
        <ul className="text-sm flex flex-col gap-1.5">
          {b.crosswalk.map((c, i) => (
            <li key={i}><Link href={`/layers/${c.layer_id}`} className="font-medium hover:underline">{layers.find((l) => l.id === c.layer_id)?.name ?? c.layer_id}</Link> <span className="text-muted">({c.relation.replace(/_/g, " ")})</span> — <span className="text-ink-2">{c.note}</span></li>
          ))}
        </ul>
      </section>
    </div>
  );
}
