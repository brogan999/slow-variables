import Link from "next/link";
import { IndicatorCard } from "@/components/IndicatorCard";
import { LadderView } from "@/components/LadderView";
import { VentureFlowStrip } from "@/components/VentureFlowStrip";
import { index, ladder, layer, obsIndex, venture } from "@/lib/data";

// P1 §6.3: the labs' enter bell (buying from the layer below) and exit bell (buying it outright), read together
const BELLS = ["lab_procurement_signal", "lab_vertical_integration_exit_bell"];

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
  const { buckets, indicators } = index();
  const bells = id === "model" ? BELLS.flatMap((b) => indicators.filter((c) => c.id === b)) : [];
  const shown = bells.length ? l.indicators.filter((c) => !BELLS.includes(c.id)) : l.indicators;
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs text-muted"><Link href="/capture" className="hover:text-ink">Capture</Link> / layer {l.order}</p>
        <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">{l.name}</h1>
        <p className="mt-1 text-sm text-ink-2">{l.description}{l.dependency_tier ? ` Dependency tier ${l.dependency_tier}.` : ""}</p>
        {id === "deployment_application" ? <p className="mt-2 text-xs text-ink-2 rounded border border-grid px-3 py-2">Disclosure: the maintainer is involved with a private value-chain map, a firm in this layer&apos;s deployment-services sub-layer. Its indicators follow the same rules as every other. <Link href="/methodology#disclaimers" className="underline decoration-grid underline-offset-2">Disclaimers</Link></p> : null}
      </div>
      {bells.length ? (
        <section>
          <h2 className="display text-2xl leading-tight mb-2 mt-2">Entry and exit bells</h2>
          <p className="text-sm text-ink-2 mb-3 max-w-[60ch]">The entry bell rings when the labs start buying from the layers around them (data and training environments); the exit bell rings when they buy those companies outright.</p>
          <div className="grid gap-3 md:grid-cols-2">{bells.map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}</div>
        </section>
      ) : null}
      <section>
        <h2 className="display text-2xl leading-tight mb-3 mt-2">Indicators</h2>
        {shown.length ? <div className="grid gap-3 md:grid-cols-2">{shown.map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}</div> : <p className="text-sm text-muted">None published yet.</p>}
      </section>
      {id === "training_input" ? (
        <section>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">Continual-learning ladder</h2>
          <LadderView doc={ladder()} obsIndex={idx} />
        </section>
      ) : null}
      {l.sublayers.length ? (
        <section>
          <h2 className="display text-2xl leading-tight mb-3 mt-2">Sub-layers and venture flow</h2>
          <ol className="flex flex-col gap-5">
            {l.sublayers.map((s) => {
              const v = venture(s.id);
              return (
                <li key={s.id}>
                  <h3 className="text-sm font-medium mb-2"><span className="text-muted tabular-nums">{s.order}.</span> <Link href={`/stack/${s.id}`} className="hover:underline">{s.name}</Link></h3>
                  {v ? <VentureFlowStrip doc={v} obsIndex={idx} note={false} /> : <p className="text-xs text-muted">No primary rounds on file.</p>}
                </li>
              );
            })}
          </ol>
          <p className="text-xs text-muted mt-3">Primary-round dollars per calendar quarter for each sub-layer, each strip on its own scale: Form D amounts sold where the entity files, Epoch&apos;s press-compiled rounds otherwise.</p>
        </section>
      ) : null}
      <section>
        <h2 className="display text-2xl leading-tight mb-3 mt-2">Crosswalk to the diffusion lens</h2>
        <ul className="text-sm flex flex-col gap-1.5">
          {l.crosswalk.map((c, i) => (
            <li key={i}><Link href={c.bucket_id === "leak" ? "/" : `/buckets/${c.bucket_id}`} className="font-medium hover:underline">{buckets.find((b) => b.id === c.bucket_id)?.name ?? "Leak"}</Link> <span className="text-muted">({c.relation.replace(/_/g, " ")})</span> — <span className="text-ink-2">{c.note}</span></li>
          ))}
        </ul>
      </section>
    </div>
  );
}
