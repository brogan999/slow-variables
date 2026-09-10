import Link from "next/link";
import { IndicatorCard } from "@/components/IndicatorCard";
import { fmt, obsIndex, stack } from "@/lib/data";

export const dynamicParams = false;
export function generateStaticParams() { return stack().layers.flatMap((l) => l.sublayers.map((s) => ({ id: s.id }))); }
export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const s = stack().layers.flatMap((l) => l.sublayers).find((x) => x.id === id);
  return { title: s?.name ?? id };
}

export default async function SublayerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const layer = stack().layers.find((l) => l.sublayers.some((s) => s.id === id))!;
  const s = layer.sublayers.find((x) => x.id === id)!;
  const idx = obsIndex();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-xs text-muted"><Link href="/stack" className="hover:text-ink">Stack</Link> / <Link href={`/layers/${layer.id}`} className="hover:text-ink">{layer.name}</Link> / sub-layer {s.order}</p>
        <h1 className="text-2xl font-semibold tracking-tight">{s.name}</h1>
      </div>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Indicators</h2>
        {s.indicators.length ? <div className="grid gap-3 md:grid-cols-2">{s.indicators.filter((c) => c.published).map((c) => <IndicatorCard key={c.id} c={c} obsIndex={idx} />)}</div> : <p className="text-sm text-muted">No indicator addresses this sub-layer yet; its entities carry whatever filings and dataset rows attach to them.</p>}
      </section>
      <section>
        <h2 className="text-sm font-medium text-ink-2 mb-2">Entities <span className="text-muted">· {s.entities.length}</span></h2>
        <div className="overflow-x-auto">
          <table className="data w-full text-sm">
            <thead><tr><th scope="col">Entity</th><th scope="col">Role</th><th scope="col">Since</th><th scope="col">Verified</th><th scope="col">Latest observation</th></tr></thead>
            <tbody>
              {s.entities.map((e) => (
                <tr key={e.id}>
                  <td><span className="font-medium">{e.name}</span>{e.cik ? <span className="ml-2 text-xs text-muted font-mono">CIK {e.cik}</span> : null}{e.notes ? <div className="text-xs text-ink-2">{e.notes}</div> : null}</td>
                  <td className="text-ink-2">{e.is_primary ? "primary" : "secondary"}</td>
                  <td className="tabular-nums text-ink-2">{e.from_date ?? "—"}{e.to_date ? ` → ${e.to_date}` : ""}</td>
                  <td>{e.verified ? <span>● yes</span> : <span className="text-muted">○ not yet</span>}</td>
                  <td className="text-xs">{e.latest ? <Link href={`/series/${e.latest.series_key}#${e.latest.obs_ids[0]}`} className="underline decoration-grid underline-offset-4">{e.latest.value !== null ? fmt(e.latest.value, e.latest.unit) : e.latest.value_text}</Link> : <span className="text-muted">none</span>}{e.latest ? <span className="text-muted"> · {e.latest.series_key.split(".").slice(2).join(".")} · {e.latest.as_of}</span> : null}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-muted mt-2">Seed lists come from the capture brief and are verified against filings one by one. A name here is not a claim about size or funding until an observation attaches.</p>
      </section>
    </div>
  );
}
