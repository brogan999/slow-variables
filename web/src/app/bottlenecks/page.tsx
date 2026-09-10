import Link from "next/link";
import { StatusChip } from "@/components/StatusChip";
import { bottlenecks, index, words } from "@/lib/data";

export const metadata = { title: "Bottlenecks" };

const FAST = new Set(["faster_than_normal"]);
const NORMAL = new Set(["consistent_with_normal", "slower_than_normal"]);

export default function BottlenecksPage() {
  const { sections, essays, items } = bottlenecks();
  const { buckets } = index();
  const bucketName = (id: string) => buckets.find((b) => b.id === id)?.name ?? words(id);
  const rows = sections.map((s) => {
    const its = items.filter((i) => i.section === s.name);
    const linked = its.flatMap((i) => i.related.filter((r) => r.published));
    const uniq = [...new Map(linked.map((r) => [r.id, r])).values()];
    const count = (pred: (st: string | null) => boolean) => uniq.filter((r) => pred(r.status)).length;
    return { ...s, n: its.length, watched: its.filter((i) => i.related.length).length, fast: count((st) => FAST.has(st ?? "")), normal: count((st) => NORMAL.has(st ?? "")), other: count((st) => !!st && !FAST.has(st) && !NORMAL.has(st)), unmeasured: count((st) => !st) };
  });
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Bottlenecks</h1>
        <p className="text-sm text-ink-2 max-w-3xl">Every barrier to AI diffusion that Narayanan and Kapoor name across eighteen essays: 89 items in nine families, each mapped to the diffusion stock it acts on. Where the tracker has an instrument for a bottleneck, its indicators are linked and carry their current status. Families with no linked indicator are the tracker&apos;s blind spots, listed on purpose.</p>
      </div>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th scope="col">Family</th><th scope="col">Acts on</th><th scope="col" className="text-right">Items</th><th scope="col" className="text-right">With an instrument</th><th scope="col" className="text-right">Faster than normal</th><th scope="col" className="text-right">Consistent or slower</th><th scope="col" className="text-right">Emerging or unclear</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name}>
                <td><a href={`#s-${sections.indexOf(r)}`} className="font-medium hover:underline">{r.name}</a></td>
                <td><Link href={`/buckets/${r.bucket_id}`} className="text-ink-2 hover:underline">{bucketName(r.bucket_id)}</Link></td>
                <td className="text-right tabular-nums">{r.n}</td>
                <td className="text-right tabular-nums">{r.watched}</td>
                <td className="text-right tabular-nums">{r.fast || "–"}</td>
                <td className="text-right tabular-nums">{r.normal || "–"}</td>
                <td className="text-right tabular-nums">{r.other || "–"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-muted">Counts are distinct published indicators linked within the family. &ldquo;Faster than normal&rdquo; on a bottleneck&apos;s instrument means the barrier is being crossed faster than the normal-technology bands allow; &ldquo;consistent or slower&rdquo; means it is holding.</p>
      {sections.map((s, si) => (
        <details key={s.name} id={`s-${si}`} open={si === 0} className="group">
          <summary className="cursor-pointer list-none"><h2 className="text-base font-medium mb-2 inline"><span className="text-muted mr-2 inline-block transition-transform group-open:rotate-90">▸</span>{s.name} <span className="text-muted font-normal">· acts on {bucketName(s.bucket_id)}</span></h2></summary>
          <p className="text-xs text-muted mb-2"><Link href={`/buckets/${s.bucket_id}`} className="underline decoration-grid underline-offset-4">Open the {bucketName(s.bucket_id)} stock</Link></p>
          <ol className="flex flex-col gap-2">
            {items.filter((i) => i.section === s.name).map((b) => (
              <li key={b.id} id={`b${b.id}`} className="rounded-lg bg-surface ring-hair p-3 text-sm">
                <div><span className="text-muted tabular-nums mr-2">#{b.id}</span><span className="font-medium">{b.title}.</span> {b.text} <span className="text-xs text-muted">{b.source_codes.map((c, i) => { const e = essays.find((x) => x.code === c); return <span key={c}>{i ? ", " : ""}{e ? <a href={e.url} className="underline decoration-grid underline-offset-4" title={`${e.title} (${e.date})`}>{c}</a> : c}</span>; })}</span></div>
                {b.related.length ? <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">{b.related.map((r) => <span key={r.id}><Link href={`/indicators/${r.id}`} className="hover:underline">{r.name}</Link> <StatusChip status={r.published ? r.status : null} /></span>)}</div> : null}
              </li>
            ))}
          </ol>
        </details>
      ))}
      <section>
        <h2 className="text-base font-medium mb-2">Essays</h2>
        <ul className="text-sm columns-1 md:columns-2 gap-6">{essays.map((e) => <li key={e.code} className="break-inside-avoid"><span className="text-muted tabular-nums mr-2">{e.code}</span><a href={e.url} className="hover:underline">{e.title}</a> <span className="text-muted">{e.date}</span></li>)}</ul>
      </section>
    </div>
  );
}
