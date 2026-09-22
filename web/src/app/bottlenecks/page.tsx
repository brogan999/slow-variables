import Link from "next/link";
import { BottleneckMap, Bets, MapReasons } from "@/components/BottleneckMap";
import { StatusChip } from "@/components/StatusChip";
import { bottleneckMap, bottlenecks, index, words } from "@/lib/data";
import { indicatorHref } from "@/lib/format";
import { SITE } from "@/lib/site";

const title = "Bottlenecks";
const description = "Where AI is being held up today, and at which stage of its spread: the chain of inputs it is made from and the frictions that slow it, with today's reading of each and who expects what to bind next.";
// a page's openGraph replaces the site's wholesale, so the share image is named again here
export const metadata = {
  title,
  description,
  openGraph: { title: `${title} · ${SITE.name}`, description, url: "/bottlenecks", siteName: SITE.name, type: "article", images: [{ url: "/opengraph-image", width: 1200, height: 630, alt: SITE.name }] },
};

export default function BottlenecksPage() {
  const doc = bottleneckMap();
  const { sections, essays, items } = bottlenecks();
  const { buckets } = index();
  const bucketName = (id: string) => buckets.find((b) => b.id === id)?.name ?? words(id);
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="display text-[2.5rem] md:text-[3.5rem] leading-[1.02] max-w-[24ch]">Bottlenecks</h1>
        <p className="text-lg leading-snug text-ink-2 max-w-[62ch]">Where AI is being held up today, and at which stage: in the chain of inputs it is made from, and in the frictions that slow it on the way from a working model to firms reorganising around it. A bottleneck here is whatever sets the pace, a scarce input upstream or a slow institution downstream; to bind is to be that scarce thing. Each row carries today&apos;s reading once; each cell says whether the row acts on that stage, and whether a named writer expects it to bind there.</p>
      </div>
      <BottleneckMap doc={doc} />
      <section className="flex flex-col gap-3">
        <h2 className="display text-2xl leading-tight mt-2">Why each row sits where it does</h2>
        <p className="text-sm text-ink-2 max-w-[62ch]">For each row: what it is, why it acts on each stage, what reads it, and who expects it to bind. A row&apos;s name in the map opens its entry here.</p>
        <MapReasons doc={doc} />
      </section>
      <section className="flex flex-col gap-3">
        <h2 className="display text-2xl leading-tight mt-2">Where startup money is going</h2>
        <p className="text-sm text-ink-2 max-w-[62ch]">Money startups raised by selling new shares, in each sub-layer the chain&apos;s inputs sit in (a sub-layer is a group of companies doing the same job within a layer of the chain). Startup money only: the physical build-out is paid for with big companies&apos; capital spending and debt, which this table misses; the capital row reads the builders&apos; spending.</p>
        <Bets doc={doc} />
      </section>
      <details className="group">
        <summary className="cursor-pointer list-none"><h2 className="display text-2xl leading-tight inline"><span aria-hidden className="text-muted mr-2 inline-block transition-transform group-open:rotate-90">▸</span>Narayanan and Kapoor&apos;s barriers, all of them</h2></summary>
        <p className="text-sm text-ink-2 mt-2 mb-4 max-w-[62ch]">The computer scientists Arvind Narayanan and Sayash Kapoor argue that AI will spread like other general-purpose technologies, slowly, because of barriers outside the models. These are the barriers they name across their essays, by family; the map above places each family at its stage.</p>
        <div className="flex flex-col gap-6">
          {sections.map((s, si) => (
            <section key={s.name} id={`s-${si}`} className="scroll-mt-24">
              <h3 className="font-sans font-semibold text-[15px] text-ink mb-1">{s.name} <span className="text-muted font-normal">· acts on <Link href={`/buckets/${s.bucket_id}`} className="underline decoration-grid underline-offset-2">{bucketName(s.bucket_id)}</Link></span></h3>
              <ol className="flex flex-col gap-2">
                {items.filter((i) => i.section === s.name).map((b) => (
                  <li key={b.id} id={`b${b.id}`} className="panel p-3 text-sm scroll-mt-24 target:bg-surface-2">
                    <div><span className="text-muted tabular-nums mr-2">#{b.id}</span><span className="font-medium">{b.title}.</span> {b.text} {b.domain ? <span className="text-xs text-muted" title={b.domain_basis ?? undefined}>[{b.domain}] </span> : null}<span className="text-xs text-muted">{b.source_codes.map((c, i) => { const e = essays.find((x) => x.code === c); return <span key={c}>{i ? ", " : ""}{e ? <a href={e.url} className="underline decoration-grid underline-offset-4" title={`${e.title} (${e.date})`}>{c}</a> : c}</span>; })}</span></div>
                    {b.related.length ? <div className="mt-1.5 flex flex-wrap gap-x-3 gap-y-1 text-xs">{b.related.map((r) => <span key={r.id}><Link href={indicatorHref(r.id, r.published)} className="hover:underline">{r.name}</Link> <StatusChip status={r.published ? r.status : null} /></span>)}</div> : null}
                  </li>
                ))}
              </ol>
            </section>
          ))}
          <section>
            <h3 className="font-sans font-semibold text-[15px] text-ink mb-2">Their essays</h3>
            <ul className="text-sm columns-1 md:columns-2 gap-6">{essays.map((e) => <li key={e.code} className="break-inside-avoid"><span className="text-muted tabular-nums mr-2">{e.code}</span><a href={e.url} className="hover:underline">{e.title}</a> <span className="text-muted">{e.date}</span></li>)}</ul>
          </section>
        </div>
      </details>
    </div>
  );
}
