import Link from "next/link";
import { StatusChip } from "@/components/StatusChip";
import { stack } from "@/lib/data";

export const metadata = { title: "Stack" };

export default function StackPage() {
  const { layers } = stack();
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">The stack</h1>
        <p className="text-sm text-ink-2 max-w-3xl">Seven layers, twenty-one sub-layers, and the companies the tracker follows in each. Membership is many-to-many and dated; an entity is <em>verified</em> once a filing or a dataset row attaches to it. Only the compute layer has segment filings today, so most sub-layers are lists of names waiting for a series.</p>
      </div>
      {layers.map((l) => (
        <section key={l.id}>
          <h2 className="text-base font-medium mb-2"><Link href={`/layers/${l.id}`} className="hover:underline">{l.order}. {l.name}</Link> <span className="text-muted font-normal">· {l.description}</span></h2>
          {l.sublayers.length ? (
            <ul className="grid gap-2 md:grid-cols-2">
              {l.sublayers.map((s) => {
                const verified = s.entities.filter((e) => e.verified).length;
                return (
                  <li key={s.id} className="min-w-0 rounded-lg bg-surface ring-hair p-3 text-sm">
                    <Link href={`/stack/${s.id}`} className="font-medium hover:underline">{s.order}. {s.name}</Link>
                    <div className="mt-1 text-xs text-ink-2">{s.entities.length} entit{s.entities.length === 1 ? "y" : "ies"} · {verified} verified{s.indicators.length ? ` · ${s.indicators.length} indicator${s.indicators.length === 1 ? "" : "s"}` : ""}</div>
                    {s.indicators.length ? <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">{s.indicators.map((c) => <span key={c.id}><Link href={c.published ? `/indicators/${c.id}` : "#"} className="hover:underline">{c.name}</Link> <StatusChip status={c.published ? c.status : null} /></span>)}</div> : null}
                    <p className="mt-1.5 text-xs text-muted truncate">{s.entities.slice(0, 8).map((e) => e.name).join(", ")}{s.entities.length > 8 ? ", …" : ""}</p>
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
