import Link from "next/link";
import { Chip, StatusChip } from "@/components/StatusChip";
import { stack } from "@/lib/data";

export const metadata = { title: "Stack" };

export default function StackPage() {
  const { layers } = stack();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02] max-w-[24ch]">The stack</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">Seven layers, twenty-one sub-layers, and the companies the tracker follows in each. Membership is many-to-many and dated; an entity is <em>verified</em> once a filing or a dataset row attaches to it. Only the compute layer has segment filings today, so most sub-layers are lists of names waiting for a series.</p>
      </div>
      {layers.map((l) => (
        <section key={l.id}>
          <h2 className="display text-2xl leading-tight mb-3"><Link href={`/layers/${l.id}`} className="hover:underline">{l.order}. {l.name}</Link> <span className="text-muted font-normal">· {l.description}</span></h2>
          {l.sublayers.length ? (
            <ul className="grid gap-2 md:grid-cols-2">
              {l.sublayers.map((s) => {
                return (
                  <li key={s.id} className="min-w-0 panel p-3 text-sm">
                    <Link href={`/stack/${s.id}`} className="font-medium hover:underline">{s.order}. {s.name}</Link>
                    <div className="mt-1 text-xs text-ink-2">{s.n_entities} entit{s.n_entities === 1 ? "y" : "ies"} · {s.n_verified} verified{s.n_indicators ? ` · ${s.n_indicators} indicator${s.n_indicators === 1 ? "" : "s"}` : ""}</div>
                    {s.indicators.length ? <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">{s.indicators.map((c) => <span key={c.id}><Link href={c.published ? `/indicators/${c.id}` : "#"} className="hover:underline">{c.name}</Link> <StatusChip status={c.published ? c.status : null} /></span>)}</div> : null}
                    {s.entities.length ? <div className="mt-2 flex flex-wrap gap-1.5">{s.entities.slice(0, 8).map((e) => <Chip key={e.id} name={e.name} />)}{s.entities.length > 8 ? <Link href={`/stack/${s.id}`} className="self-center text-xs text-ink-2 underline decoration-axis underline-offset-2">all companies</Link> : null}</div> : null}
                  </li>
                );
              })}
            </ul>
          ) : <p className="text-sm text-muted">Indicator-only layer: no companies, only measures of adopters, workers and consumers.</p>}
        </section>
      ))}
    </div>
  );
}
