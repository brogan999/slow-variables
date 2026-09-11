import Link from "next/link";
import { indicatorHref } from "@/lib/format";
import { index, words } from "@/lib/data";

export const metadata = { title: "Crosswalk" };

export default function CrosswalkPage() {
  const { crosswalk, buckets, layers, sublayers, indicators } = index();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="display text-[2.25rem] md:text-[3rem] leading-[1.05] tracking-[-0.015em]">Crosswalk</h1>
      <p className="text-lg leading-snug text-ink-2 max-w-[60ch]">The same observations carry a diffusion address (bucket, valve) and a capture address (layer, sub-layer). Diffusion asks how fast value moves; capture asks who keeps it. The leak on the diffusion diagram is the capture lens.</p>
      <div className="overflow-x-auto">
        <table className="data w-full text-sm">
          <thead><tr><th scope="col">Diffusion bucket</th><th scope="col">Relation</th><th scope="col">Capture layer</th><th scope="col">Note</th><th scope="col">Shared indicators</th></tr></thead>
          <tbody>
            {crosswalk.map((c, i) => (
              <tr key={i}>
                <td>{c.bucket_id === "leak" ? <span>Leak</span> : <Link href={`/buckets/${c.bucket_id}`} className="font-medium hover:underline">{buckets.find((b) => b.id === c.bucket_id)?.name}</Link>}</td>
                <td className="text-ink-2 whitespace-nowrap">{words(c.relation)}</td>
                <td><Link href={`/layers/${c.layer_id}`} className="font-medium hover:underline">{layers.find((l) => l.id === c.layer_id)?.name}</Link>{c.sublayer_id ? <span className="text-muted"> / {sublayers.find((s) => s.id === c.sublayer_id)?.name}</span> : null}</td>
                <td className="text-ink-2">{c.note}</td>
                <td><span className="flex flex-wrap gap-x-2">{c.shared_indicators.map((s) => <Link key={s} href={indicatorHref(s, indicators.find((i) => i.id === s)?.published)} className="hover:underline">{indicators.find((i) => i.id === s)?.name ?? s}</Link>)}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
