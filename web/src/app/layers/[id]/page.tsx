import Link from "next/link";
import { IndicatorCard } from "@/components/IndicatorCard";
import { index, layer, obsIndex } from "@/lib/data";

export const dynamicParams = false;
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return { title: layer(id).name };
}
export function generateStaticParams() { return index().layers.map((l) => ({ id: l.id })); }

export default async function LayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const l = layer(id);
  const idx = obsIndex();
  const { buckets } = index();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs text-muted"><Link href="/capture" className="hover:text-ink">Capture</Link> / layer {l.order}</p>
        <h1 className="text-2xl font-semibold tracking-tight">{l.name}</h1>
        <p className="mt-1 text-sm text-ink-2">{l.description}{l.dependency_tier ? ` Dependency tier ${l.dependency_tier}.` : ""}</p>
        {id === "deployment_application" ? <p className="mt-2 text-xs text-ink-2 rounded border border-grid px-3 py-2">Disclosure: the maintainer is involved with a private value-chain map, a firm in this layer&apos;s deployment-services sub-layer. Its indicators follow the same rules as every other.</p> : null}
      </div>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Indicators</h2>
        {l.indicators.length ? <div className="grid gap-3 md:grid-cols-2">{l.indicators.map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}</div> : <p className="text-sm text-muted">None published yet.</p>}
      </section>
      {l.sublayers.length ? (
        <section>
          <h2 className="text-sm font-medium text-ink-2 mb-2">Sub-layers</h2>
          <ol className="text-sm grid gap-1 md:grid-cols-2">{l.sublayers.map((s) => <li key={s.id}><span className="text-muted tabular-nums">{s.order}.</span> <Link href={`/stack/${s.id}`} className="hover:underline">{s.name}</Link></li>)}</ol>
          
        </section>
      ) : null}
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Crosswalk to the diffusion lens</h2>
        <ul className="text-sm flex flex-col gap-1.5">
          {l.crosswalk.map((c, i) => (
            <li key={i}><Link href={c.bucket_id === "leak" ? "/" : `/buckets/${c.bucket_id}`} className="font-medium hover:underline">{buckets.find((b) => b.id === c.bucket_id)?.name ?? "Leak"}</Link> <span className="text-muted">({c.relation.replace(/_/g, " ")})</span> — <span className="text-ink-2">{c.note}</span></li>
          ))}
        </ul>
      </section>
    </div>
  );
}
